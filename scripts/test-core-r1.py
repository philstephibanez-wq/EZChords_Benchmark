from __future__ import annotations
import json, shutil, sys, tempfile
from pathlib import Path
PROJECT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(PROJECT/"python"))
from ezstudio.core import EventRecord, LabPaths, ObservationRecord, RunRecord, sha256_file
from ezstudio.core.registry import JsonlRunRegistry
from ezstudio.core.storage import ArtifactStore, RunWorkspace

def main()->int:
    temp=Path(tempfile.mkdtemp(prefix="ezstudio-core-r1-"))
    try:
        paths=LabPaths(temp/"runtime"); paths.ensure(); source=temp/"source.wav"; source.write_bytes(b"EZStudio_lab CORE R1 fixture\n")
        store=ArtifactStore(paths); a1=store.import_file(source,kind="audio_source"); a2=store.import_file(source,kind="audio_source")
        assert a1.artifact_id==a2.artifact_id and a1.sha256==sha256_file(source) and store.resolve(a1.artifact_id).read_bytes()==source.read_bytes()
        run=RunRecord(run_id="stems-000001",item="stems",engine_name="contract-test",engine_version="1.0",config={"precision":"fp16","chunk":30},input_artifact_ids=[a1.artifact_id]); run.mark_running(); run.mark_done()
        registry=JsonlRunRegistry(paths); manifest=registry.persist_run(run); registry.append_artifact(run,a1); registry.append_observation(run,ObservationRecord(namespace="runtime",name="duration_s",value=1.25,unit="s")); registry.append_event(run,EventRecord(event_type="contract_test",time_s=0.0,payload={"ok":True}))
        parsed=json.loads(manifest.read_text(encoding="utf-8")); assert parsed["schema_version"]==1 and parsed["item"]=="stems" and parsed["status"]=="done" and len(parsed["config_hash"])==64
        workspace=RunWorkspace(paths,"stems","stems-000001"); assert (workspace.path("raw")/"observations.jsonl").is_file() and (workspace.path("raw")/"events.jsonl").is_file()
        try: RunRecord(run_id="bad-1",item="unknown",engine_name="x",engine_version="1",config={}); raise AssertionError("Unknown item accepted")
        except ValueError: pass
        project_text="\n".join(p.read_text(encoding="utf-8",errors="ignore") for p in (PROJECT/"python"/"ezstudio").rglob("*.py")); forbidden="H:"+chr(92)+"EZScore"; assert forbidden not in project_text
        print("EZSTUDIO_CORE_R1_SCHEMA_OK"); print("EZSTUDIO_CORE_R1_CONTENT_ADDRESSING_OK"); print("EZSTUDIO_CORE_R1_RUN_WORKSPACE_OK"); print("EZSTUDIO_CORE_R1_EZSCORE_INDEPENDENCE_OK"); print("EZSTUDIO_CORE_R1_OK"); return 0
    finally: shutil.rmtree(temp,ignore_errors=True)
if __name__=="__main__": raise SystemExit(main())
