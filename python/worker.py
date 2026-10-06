from __future__ import annotations
import argparse, json, os, sqlite3, sys, traceback
from pathlib import Path
from engine import analyze, ENGINE_VERSION

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--db',required=True); ap.add_argument('--run-id',type=int,required=True); ap.add_argument('--audio',required=True); ap.add_argument('--signature',required=True); ap.add_argument('--deps',required=True); ap.add_argument('--keep-upload',choices=['0','1'],default='0'); a=ap.parse_args()
    db=sqlite3.connect(a.db,timeout=60); db.execute('PRAGMA journal_mode=WAL'); db.execute('PRAGMA foreign_keys=ON')
    def log(level,msg):
        print(level,msg,flush=True); db.execute('INSERT INTO run_logs(run_id,created_at,level,message) VALUES(?,datetime(\'now\'),?,?)',(a.run_id,level,str(msg))); db.commit()
    def progress(p):
        db.execute('UPDATE benchmark_runs SET progress=?,updated_at=datetime(\'now\') WHERE id=?',(int(p),a.run_id)); db.commit()
    dep_root=Path(a.deps)
    os.environ['TORCH_HOME']=str(dep_root.parent/'torch_cache')
    audio=Path(a.audio); work=dep_root.parent/'work'/f'run-{a.run_id}'
    try:
        db.execute("UPDATE benchmark_runs SET status='running',progress=1,updated_at=datetime('now'),engine_version=? WHERE id=?",(ENGINE_VERSION,a.run_id)); db.commit(); log('INFO','worker démarré')
        result=analyze(audio,a.signature,Path(a.deps),work,progress,log)
        db.execute('DELETE FROM algorithm_results WHERE run_id=?',(a.run_id,))
        for item in result['algorithms']:
            db.execute('INSERT INTO algorithm_results(run_id,algorithm,phase,score,margin,grid_json) VALUES(?,?,?,?,?,?)',(a.run_id,item['algorithm'],int(item['phase']),float(item['score']),float(item['margin']),json.dumps(item['grid'],ensure_ascii=False)))
        db.execute("UPDATE benchmark_runs SET status='done',progress=100,detected_signature=?,tempo=?,result_json=?,updated_at=datetime('now'),error=NULL WHERE id=?",(result['signature'],float(result['tempo']),json.dumps(result,ensure_ascii=False),a.run_id)); db.commit(); log('INFO','analyse terminée')
        if a.keep_upload=='0':
            try: audio.unlink(missing_ok=True); log('INFO','upload source supprimé après analyse')
            except Exception as e: log('WARN',f'impossible de supprimer upload: {e}')
        return 0
    except Exception as e:
        tb=traceback.format_exc(); print(tb,file=sys.stderr); log('ERROR',f'{type(e).__name__}: {e}'); db.execute("UPDATE benchmark_runs SET status='error',updated_at=datetime('now'),error=? WHERE id=?",(f'{type(e).__name__}: {e}',a.run_id)); db.commit(); return 1
    finally: db.close()
if __name__=='__main__': raise SystemExit(main())
