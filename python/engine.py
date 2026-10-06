from __future__ import annotations
import importlib.util, importlib.metadata, math, os, shutil, subprocess, sys, wave
from pathlib import Path
import numpy as np
import librosa
import torch

FPS=50.0
AUTO={"2/4":2,"3/4":3,"4/4":4,"6/8":6}
ENGINE_VERSION="r6-app-v6b-silence"

def z(x):
    x=np.asarray(x,float); return (x-x.mean())/(x.std()+1e-9) if x.size else x

def sample_frames(x,idx):
    x=np.asarray(x,float); idx=np.asarray(idx,int)
    if not len(x): return np.zeros(len(idx))
    return x[np.clip(idx,0,len(x)-1)]

def sample_times(x,t):
    x=np.asarray(x,float); t=np.asarray(t,float)
    if not len(x): return np.zeros(len(t))
    idx=np.rint(t*FPS).astype(int); return x[np.clip(idx,0,len(x)-1)]

def sigmoid(x):
    x=np.asarray(x,float); return 1/(1+np.exp(-np.clip(x,-60,60)))

def coherence(v,p,ph):
    v=z(v); idx=np.arange(len(v)); a=v[((idx-ph)%p)==0]; b=v[((idx-ph)%p)!=0]
    return float(a.mean()-b.mean()) if len(a) and len(b) else -1e9

def bass_feature(y,sr,hop,bf):
    c=np.abs(librosa.cqt(y=y,sr=sr,hop_length=hop,fmin=librosa.note_to_hz('C1'),n_bins=36,bins_per_octave=12))
    low=c[:24].mean(axis=0); d=np.r_[0.,np.maximum(0.,np.diff(low))]
    return sample_frames(low+.75*d,bf)

def harmonic_novelty(y,sr,hop,bf):
    h,_=librosa.effects.hpss(y); c=librosa.feature.chroma_cqt(y=h,sr=sr,hop_length=hop)
    if c.shape[1]<2: return np.zeros(len(bf))
    a,b=c[:,:-1],c[:,1:]; nov=np.r_[0.,1.-np.sum(a*b,axis=0)/(np.linalg.norm(a,axis=0)*np.linalg.norm(b,axis=0)+1e-9)]
    return sample_frames(nov,bf)

def auto_signature(dr,bass,harm):
    fused=.62*dr+.25*bass+.13*harm; best={}
    for sig,p in AUTO.items():
        cand=[]
        for ph in range(p):
            sc=.50*coherence(fused,p,ph)+.30*coherence(dr,p,ph)+.13*coherence(bass,p,ph)+.07*coherence(harm,p,ph)
            if sig=='4/4': sc+=.02
            if sig=='6/8':
                pos=(np.arange(len(dr))-ph)%6; a=dr[(pos==0)|(pos==3)]; b=dr[(pos!=0)&(pos!=3)]
                if len(a) and len(b): sc+=.16*float(np.clip(a.mean()-b.mean(),-1,1))
            cand.append((sc,ph))
        best[sig]=max(cand)
    order=sorted(best.items(),key=lambda x:x[1][0],reverse=True); sig,(top,ph)=order[0]; second=order[1][1][0]
    return {"signature":sig,"phase":int(ph),"confidence":float(np.clip(.5+top-second,0,1)),"scores":{k:round(v[0],5) for k,v in best.items()}}

def phase_scores(v,p):
    arr=np.asarray(v,float)
    rows=[]
    for ph in range(p):
        a=arr[ph::p]
        others=[arr[q::p] for q in range(p) if q!=ph]
        b=np.concatenate(others) if others else np.asarray([],float)
        sc=float(a.mean()-b.mean()) if len(a) and len(b) else -1e9
        rows.append({"phase":int(ph),"score":sc,"downbeat_mean":float(a.mean()) if len(a) else -1e9})
    return rows

def choose_phase(v,p):
    rows=phase_scores(v,p)
    ranked=sorted(rows,key=lambda x:(x["score"],x["downbeat_mean"]),reverse=True)
    best=ranked[0]
    second=ranked[1] if len(ranked)>1 else {"score":best["score"]}
    return {
        "phase":int(best["phase"]),
        "score":float(best["score"]),
        "margin":float(best["score"]-second["score"]),
        "phase_scores":rows,
    }

def refine_duple_signature_with_beat_this(initial_signature, bt, threshold=0.04):
    if initial_signature not in ("2/4","4/4"):
        return initial_signature, {
            "applied":False,
            "reason":"not_duple_simple",
            "initial_signature":initial_signature,
        }

    p2=choose_phase(bt,2)
    p4=choose_phase(bt,4)
    delta=float(p4["score"]-p2["score"])

    refined=initial_signature
    reason="keep_initial"
    if delta > threshold:
        refined="4/4"
        reason="beat_this_prefers_4_4"
    elif delta < -threshold:
        refined="2/4"
        reason="beat_this_prefers_2_4"

    return refined, {
        "applied":True,
        "initial_signature":initial_signature,
        "refined_signature":refined,
        "threshold":float(threshold),
        "delta_4_minus_2":delta,
        "phase2_best":p2,
        "phase4_best":p4,
        "reason":reason,
    }

def chord_label(raw):
    s=str(raw or 'N').strip()
    if not s or s=='N': return '.'
    if ':' not in s: return s
    root,q=s.split(':',1); mp={'maj':'','min':'m','7':'7','min7':'m7','maj7':'maj7','dim':'dim','sus2':'sus2','sus4':'sus4'}
    return root+mp.get(q,q)

def chord_for_interval(segs,a,b):
    best=None; ov=0.0
    for s in segs:
        x=max(0.0,min(b,s['end'])-max(a,s['start']))
        if x>ov:
            ov=x
            best=s
    # A zero-overlap segment must never fill a silent beat.
    return best['chord'] if best is not None and ov>0.0 else '.'

def harmonic_silence_mask(y,sr,beats,hop=512):
    """
    Detect beat-level harmonic rests ("no chord"), not digital silence.
    The metric grid is untouched. A beat is silent only when BOTH:
      - harmonic RMS is in the quiet tail of the song;
      - chroma energy is also in the quiet tail.
    This avoids treating voice/percussion-only activity as a sustained chord.
    """
    beats=np.asarray(beats,float)
    if not len(beats):
        return np.zeros(0,dtype=bool), {
            "silent_beats":0,
            "total_beats":0,
            "silent_ratio":0.0,
            "rms_threshold_db":None,
            "chroma_threshold":None,
        }

    harm,_=librosa.effects.hpss(y)
    step=float(np.median(np.diff(beats))) if len(beats)>1 else .5

    rms=[]
    chroma_energy=[]

    chroma=np.abs(librosa.feature.chroma_cqt(y=harm,sr=sr,hop_length=hop))
    chroma_times=librosa.frames_to_time(np.arange(chroma.shape[1]),sr=sr,hop_length=hop)

    for i,a in enumerate(beats):
        b=beats[i+1] if i+1<len(beats) else a+step
        ia=max(0,int(round(a*sr)))
        ib=min(len(harm),max(ia+1,int(round(b*sr))))
        chunk=np.asarray(harm[ia:ib],float)
        r=float(np.sqrt(np.mean(chunk*chunk)+1e-12)) if len(chunk) else 0.0
        rms.append(r)

        mask=(chroma_times>=a)&(chroma_times<b)
        if np.any(mask):
            ce=float(np.mean(np.sum(chroma[:,mask],axis=0)))
        else:
            idx=int(np.argmin(np.abs(chroma_times-a))) if len(chroma_times) else 0
            ce=float(np.sum(chroma[:,idx])) if chroma.shape[1] else 0.0
        chroma_energy.append(ce)

    rms=np.asarray(rms,float)
    chroma_energy=np.asarray(chroma_energy,float)
    rms_db=20.0*np.log10(np.maximum(rms,1e-9))

    # Robust adaptive thresholds. We deliberately require both conditions.
    # Quiet-tail anchor prevents "everything is a chord" on arrangements
    # where lv-chordia labels through a harmonic rest.
    rms_p15=float(np.percentile(rms_db,15))
    rms_median=float(np.median(rms_db))
    rms_threshold=float(min(rms_p15+3.0, rms_median-12.0))

    chroma_p15=float(np.percentile(chroma_energy,15))
    chroma_median=float(np.median(chroma_energy))
    chroma_threshold=float(min(chroma_p15*1.15, chroma_median*0.40))

    mask=(rms_db<=rms_threshold)&(chroma_energy<=chroma_threshold)

    # Single isolated silent beats are allowed musically, but suppress tiny
    # numerical holes: require a meaningful energy drop relative to median.
    strong_drop=rms_db <= (rms_median-9.0)
    mask=mask & strong_drop

    diag={
        "silent_beats":int(mask.sum()),
        "total_beats":int(len(mask)),
        "silent_ratio":float(mask.mean()) if len(mask) else 0.0,
        "rms_threshold_db":rms_threshold,
        "rms_median_db":rms_median,
        "chroma_threshold":chroma_threshold,
        "chroma_median":chroma_median,
        "silent_indices":[int(i) for i in np.flatnonzero(mask)],
    }
    return mask,diag

def grid(segs,beats,phase,period,count=32,silent_beats=None):
    beats=np.asarray(beats,float); step=float(np.median(np.diff(beats))) if len(beats)>1 else .5; cells={}
    for i,a in enumerate(beats):
        b=beats[i+1] if i+1<len(beats) else a+step; rel=i-phase; m=rel//period; bt=rel%period
        if 0<=m<count:
            if silent_beats is not None and i < len(silent_beats) and bool(silent_beats[i]):
                cells[(m,bt)]='.'
            else:
                cells[(m,bt)]=chord_for_interval(segs,float(a),float(b))
    out=[]
    for m in range(count):
        raw=[cells.get((m,b),'.') for b in range(period)]; r=[]; prev=None
        for bt,c in enumerate(raw):
            if c=='.': r.append('.'); prev='.'
            elif bt==0: r.append(c); prev=c
            elif c==prev: r.append('-')
            else: r.append(c); prev=c
        idx=phase+m*period; out.append({"measure":m,"start_s":float(beats[idx]) if idx<len(beats) else None,"text":" ".join(r)})
    return out

def ensure_deps(deps:Path, log):
    deps.mkdir(parents=True,exist_ok=True); sys.path.insert(0,str(deps)); importlib.invalidate_caches()
    req=[]
    if importlib.util.find_spec('beat_this') is None: req += ['beat-this==1.1.0','torchaudio==2.11.0','einops==0.8.2','rotary-embedding-torch==0.9.1','soxr==1.1.0','tqdm==4.70.1']
    if importlib.util.find_spec('lv_chordia') is None: req += ['lv-chordia==1.1.0']
    for package in req:
        log('INFO',f'installation dépendance {package}')
        subprocess.run([sys.executable,'-m','pip','install','--upgrade','--target',str(deps),'--no-deps',package],check=True)
        importlib.invalidate_caches()

def analyze(audio:Path,signature_request:str,deps:Path,work:Path,progress,log):
    if not torch.cuda.is_available(): raise RuntimeError('CUDA obligatoire : aucun fallback CPU')
    ff=shutil.which('ffmpeg')
    if not ff: raise RuntimeError('ffmpeg introuvable dans PATH')
    ensure_deps(deps,log)
    from beat_this.inference import Audio2Frames
    from lv_chordia.chord_recognition import chord_recognition
    progress(8); log('INFO',f'GPU {torch.cuda.get_device_name(0)}')
    work.mkdir(parents=True,exist_ok=True); wav=work/'input.wav'
    subprocess.run([ff,'-hide_banner','-loglevel','error','-y','-i',str(audio),'-ac','1','-ar','22050','-c:a','pcm_s16le',str(wav)],check=True)
    with wave.open(str(wav),'rb') as w: sr=w.getframerate(); raw=w.readframes(w.getnframes())
    y=np.frombuffer(raw,dtype='<i2').astype(np.float32)/32768.; hop=512
    progress(18); _,perc=librosa.effects.hpss(y)
    tempo_arr,beats=librosa.beat.beat_track(y=perc,sr=sr,hop_length=hop,units='time',trim=False); tempo=float(np.asarray(tempo_arr).squeeze()); beats=np.asarray(beats,float)
    bf=librosa.time_to_frames(beats,sr=sr,hop_length=hop); onset=sample_frames(librosa.onset.onset_strength(y=perc,sr=sr,hop_length=hop),bf)
    bass=bass_feature(y,sr,hop,bf); harm=harmonic_novelty(y,sr,hop,bf)
    silent_beats,silence_diag=harmonic_silence_mask(y,sr,beats,hop)
    log('INFO',f'no-chord {silence_diag["silent_beats"]}/{silence_diag["total_beats"]} beats')
    progress(30)
    if signature_request=='Auto':
        meter=auto_signature(z(onset),z(bass),z(harm))
        initial_signature=meter['signature']
    else:
        meter={"signature":signature_request,"confidence":1.0,"scores":{}}
        initial_signature=signature_request

    model=Audio2Frames(checkpoint_path='final0',device='cuda',float16=False)
    _,db=model(y,sr)
    bt=sample_times(sigmoid(db.detach().float().cpu().numpy()),beats)

    if signature_request=='Auto':
        signature,duple_refinement=refine_duple_signature_with_beat_this(initial_signature,bt)
    else:
        signature=initial_signature
        duple_refinement={
            "applied":False,
            "reason":"manual_signature",
            "initial_signature":initial_signature,
            "refined_signature":signature,
        }

    meter["initial_signature"]=initial_signature
    meter["signature"]=signature
    meter["duple_refinement"]=duple_refinement

    period=int(signature.split('/')[0])
    log('INFO',f'signature utilisée {signature}; initiale {initial_signature}; tempo {tempo:.3f}')
    progress(48); rz,bz,hz=z(onset),z(bass),z(harm)
    specs=[('Beat This downbeat',bt),('Percussive onset',rz),('Bass CQT',bz),('Rhythm + Bass',.72*rz+.28*bz),('Harmonic novelty',hz),('R41-like fusion',.62*rz+.25*bz+.13*hz)]
    alg=[]
    for name,v in specs:
        p=choose_phase(v,period)
        p['algorithm']=name
        alg.append(p)

    phase_hist={}
    for a in alg:
        key=str(a["phase"])
        phase_hist[key]=phase_hist.get(key,0)+1
    convergence={
        "distinct_phases":len(phase_hist),
        "phase_histogram":phase_hist,
        "unanimous":len(phase_hist)==1,
    }

    progress(60); log('INFO',f'phases {phase_hist}; unanimité={convergence["unanimous"]}')
    log('INFO','analyse accords lv-chordia')
    rawsegs=chord_recognition(audio_path=str(audio),chord_dict_name='submission'); segs=[]
    for x in rawsegs or []:
        a=float(x.get('start_time',0)); b=float(x.get('end_time',a))
        if b>a: segs.append({"start":a,"end":b,"chord":chord_label(x.get('chord')),"raw_chord":str(x.get('chord','N'))})
    if not segs: raise RuntimeError('lv-chordia n’a retourné aucun segment')
    progress(82)
    for a in alg: a['grid']=grid(segs,beats,int(a['phase']),period,32,silent_beats=silent_beats)
    progress(95)
    versions = {
        "python": sys.version.split()[0],
        "torch": str(torch.__version__),
        "librosa": str(librosa.__version__),
    }
    for package in ("beat-this", "lv-chordia", "torchaudio"):
        try:
            versions[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            versions[package] = None

    return {
        "engine_version": ENGINE_VERSION,
        "analysis_source": "master_audio",
        "tempo": tempo,
        "signature": signature,
        "meter": meter,
        "duration_s": float(len(y) / sr),
        "sample_rate": int(sr),
        "beat_grid_s": [float(x) for x in beats],
        "versions": versions,
        "parameters": {
            "hop_length": hop,
            "beat_this_checkpoint": "final0",
            "beat_this_fps": FPS,
            "chord_engine": "lv-chordia",
            "chord_dictionary": "submission",
            "stems_required": False,
        },
        "algorithms": alg,
        "convergence": convergence,
        "silence": silence_diag,
        "segments": segs,
    }

def self_test():
    x=np.zeros(24); x[2::4]=1
    cp=choose_phase(x,4)
    assert cp['phase']==2
    assert len(cp['phase_scores'])==4
    sig,diag=refine_duple_signature_with_beat_this('2/4',x,threshold=.01)
    assert sig=='4/4'
    beats=np.arange(0,8,.5); segs=[{"start":0,"end":8,"chord":"Cm"}]
    assert grid(segs,beats,0,4,1)[0]['text']=='Cm - - -'
    sm=np.zeros(len(beats),dtype=bool); sm[1]=True
    assert grid(segs,beats,0,4,1,silent_beats=sm)[0]['text']=='Cm . Cm -'
    assert chord_for_interval([{"start":1.0,"end":2.0,"chord":"C"}],0.0,0.5)=='.'
    print('ENGINE_SELF_TEST_OK')

if __name__=='__main__':
    if '--self-test' in sys.argv: self_test()
