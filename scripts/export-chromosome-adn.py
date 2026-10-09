from __future__ import annotations
import argparse, json, sqlite3, zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REGIONS = ('profile','stems','chords','lyrics')
TEXT_SUFFIXES = {'.json','.txt','.log','.csv','.tsv'}

def rows(c, sql, params=()):
    cur=c.execute(sql,params); cols=[d[0] for d in cur.description]; return [dict(zip(cols,r)) for r in cur.fetchall()]

def decode(r):
    o=dict(r)
    for k,v in list(o.items()):
        if k.endswith('_json') and isinstance(v,str):
            try:o[k[:-5]]=json.loads(v)
            except Exception:pass
    return o

def safe(v):
    import re
    return re.sub(r'[^A-Za-z0-9._-]+','-',v.strip()).strip('-._') or 'item'

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--db',required=True); ap.add_argument('--song-id',required=True,type=int); ap.add_argument('--output',required=True); a=ap.parse_args()
    c=sqlite3.connect(a.db)
    tables={r[0] for r in c.execute("select name from sqlite_master where type='table'")}
    s=rows(c,'select * from songs where id=?',(a.song_id,))
    if not s: raise RuntimeError('catalog_song_not_found')
    song=s[0]; h=str(song.get('audio_sha256') or '')
    ids=[a.song_id] if not h else [int(r['id']) for r in rows(c,'select id from songs where audio_sha256=? order by id',(h,))]
    marks=','.join('?' for _ in ids)
    runs=[] if 'scientific_runs' not in tables else [decode(r) for r in rows(c,f'select * from scientific_runs where song_id in ({marks}) order by id desc',tuple(ids))]
    by={x:[r for r in runs if r.get('item')==x] for x in REGIONS}
    jobs=[] if 'analysis_jobs' not in tables else [decode(r) for r in rows(c,f'select * from analysis_jobs where song_id in ({marks}) order by id desc',tuple(ids))]
    arts={}
    if runs and 'scientific_artifacts' in tables:
        rids=[int(r['id']) for r in runs]; rm=','.join('?' for _ in rids)
        for r in rows(c,f'select * from scientific_artifacts where run_id in ({rm}) order by run_id,id',tuple(rids)): arts.setdefault(int(r['run_id']),[]).append(decode(r))
    legacy=[] if 'benchmark_runs' not in tables else [decode(r) for r in rows(c,f'select * from benchmark_runs where song_id in ({marks}) order by id desc',tuple(ids))]
    present=[bool(by[x]) for x in REGIONS]; gap=False; valid=True
    for x in present:
        if not x: gap=True
        elif gap: valid=False
    latest={x:({'run_id':int(by[x][0]['id']),'public_id':by[x][0].get('public_id'),'state':by[x][0].get('state'),'engine_name':by[x][0].get('engine_name'),'engine_version':by[x][0].get('engine_version'),'model_name':by[x][0].get('model_name')} if by[x] else None) for x in REGIONS}
    manifest={'schema':'ezstudio.chromosome.adn.v1','generated_at':datetime.now(timezone.utc).isoformat(),'song':song,'catalog_song_ids':ids,'chromosome':{'regions':latest,'integrity':{'order':list(REGIONS),'present':dict(zip(REGIONS,present)),'valid_prefix':valid}},'counts':{'scientific_runs':len(runs),'analysis_jobs':len(jobs),'legacy_chords_runs':len(legacy)},'binary_audio_included':False}
    out=Path(a.output); out.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        z.writestr('manifest.json',json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
        z.writestr('sqlite/analysis_jobs.json',json.dumps(jobs,ensure_ascii=False,indent=2,default=str)+'\n')
        z.writestr('sqlite/legacy_chords_runs.json',json.dumps(legacy,ensure_ascii=False,indent=2,default=str)+'\n')
        for run in runs:
            rid=int(run['id']); region=str(run.get('item') or 'unknown'); pid=str(run.get('public_id') or f'{region}-{rid}'); payload=dict(run); payload['artifacts']=arts.get(rid,[])
            z.writestr(f'sqlite/regions/{safe(region)}/{safe(pid)}.json',json.dumps(payload,ensure_ascii=False,indent=2,default=str)+'\n')
            for art in arts.get(rid,[]):
                p=Path(str(art.get('path') or ''))
                if p.is_file() and p.suffix.lower() in TEXT_SUFFIXES and p.stat().st_size<=25*1024*1024: z.write(p,f'artifacts/{safe(region)}/{safe(pid)}/{safe(p.name)}')
        z.writestr('README.txt','EZStudio_lab chromosome ADN bundle v1\nPROFILE -> STEMS -> CHORDS/N -> LYRICS\nNo heavy audio binaries included; metadata and hashes remain in manifests.\n')
    print(f'EZSTUDIO_CHROMOSOME_ADN_EXPORT_OK {out}')
    return 0
if __name__=='__main__': raise SystemExit(main())
