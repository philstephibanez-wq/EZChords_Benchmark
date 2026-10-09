from __future__ import annotations
import argparse, json, sqlite3, zipfile
from datetime import datetime, timezone
from pathlib import Path

REGIONS = ("profile","stems","chords","lyrics")
TEXT_SUFFIXES = {".json",".txt",".log",".csv",".tsv"}

def rows(c, sql, params=()):
    cur=c.execute(sql,params)
    cols=[d[0] for d in cur.description]
    return [dict(zip(cols,r)) for r in cur.fetchall()]

def decode(r):
    o=dict(r)
    for k,v in list(o.items()):
        if k.endswith("_json") and isinstance(v,str):
            try:o[k[:-5]]=json.loads(v)
            except Exception:pass
    return o

def safe(v):
    import re
    return re.sub(r"[^A-Za-z0-9._-]+","-",v.strip()).strip("-._") or "item"

def tables(c):
    return {r[0] for r in c.execute("select name from sqlite_master where type='table'")}

def genome_payload(c, t, run_ids):
    req={
        "genome_gene_revisions",
        "genome_region_revisions",
        "genome_region_revision_genes",
        "genome_region_revision_parents",
        "scientific_run_genome",
        "genome_region_baselines",
    }
    if not req.issubset(t):
        return {
            "schema":"ezstudio.genome.export.v1",
            "available":False,
            "run_links":[],
            "region_revisions":[],
            "region_parents":[],
            "region_genes":[],
            "gene_revisions":[],
            "baselines":[],
        }

    if run_ids:
        marks=",".join("?" for _ in run_ids)
        run_links=[decode(r) for r in rows(
            c,
            f"""select sg.*,rr.region,rr.revision_ref,rr.fingerprint
                from scientific_run_genome sg
                join genome_region_revisions rr on rr.id=sg.region_revision_id
                where sg.run_id in ({marks})
                order by sg.run_id""",
            tuple(run_ids)
        )]
    else:
        run_links=[]

    regions=sorted({str(x["region"]) for x in run_links if x.get("region")})
    if not regions:
        return {
            "schema":"ezstudio.genome.export.v1",
            "available":True,
            "run_links":run_links,
            "region_revisions":[],
            "region_parents":[],
            "region_genes":[],
            "gene_revisions":[],
            "baselines":[],
        }

    rmarks=",".join("?" for _ in regions)
    region_revisions=[decode(r) for r in rows(
        c,
        f"""select * from genome_region_revisions
            where region in ({rmarks})
            order by region,revision_number""",
        tuple(regions)
    )]
    ids=[int(x["id"]) for x in region_revisions]

    if ids:
        imarks=",".join("?" for _ in ids)
        region_parents=[decode(r) for r in rows(
            c,
            f"""select * from genome_region_revision_parents
                where child_region_revision_id in ({imarks})
                   or parent_region_revision_id in ({imarks})
                order by child_region_revision_id,parent_region_revision_id""",
            tuple(ids+ids)
        )]
        region_genes=[decode(r) for r in rows(
            c,
            f"""select * from genome_region_revision_genes
                where region_revision_id in ({imarks})
                order by region_revision_id,position""",
            tuple(ids)
        )]
    else:
        region_parents=[]
        region_genes=[]

    gids=sorted({int(x["gene_revision_id"]) for x in region_genes})
    if gids:
        gmarks=",".join("?" for _ in gids)
        gene_revisions=[decode(r) for r in rows(
            c,
            f"""select * from genome_gene_revisions
                where id in ({gmarks})
                order by gene_key,revision_number""",
            tuple(gids)
        )]
    else:
        gene_revisions=[]

    baselines=[decode(r) for r in rows(
        c,
        f"""select b.*,rr.revision_ref,rr.fingerprint
            from genome_region_baselines b
            join genome_region_revisions rr on rr.id=b.region_revision_id
            where b.region in ({rmarks})
            order by b.region""",
        tuple(regions)
    )]

    return {
        "schema":"ezstudio.genome.export.v1",
        "available":True,
        "regions":regions,
        "run_links":run_links,
        "region_revisions":region_revisions,
        "region_parents":region_parents,
        "region_genes":region_genes,
        "gene_revisions":gene_revisions,
        "baselines":baselines,
    }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--db",required=True)
    ap.add_argument("--song-id",required=True,type=int)
    ap.add_argument("--output",required=True)
    a=ap.parse_args()

    c=sqlite3.connect(a.db)
    t=tables(c)
    selected=rows(c,"select * from songs where id=?",(a.song_id,))
    if not selected: raise RuntimeError("catalog_song_not_found")
    song=selected[0]
    h=str(song.get("audio_sha256") or "")
    ids=[a.song_id] if not h else [
        int(r["id"]) for r in rows(
            c,"select id from songs where audio_sha256=? order by id",(h,)
        )
    ]
    marks=",".join("?" for _ in ids)

    runs=[] if "scientific_runs" not in t else [
        decode(r) for r in rows(
            c,
            f"select * from scientific_runs where song_id in ({marks}) order by id",
            tuple(ids)
        )
    ]
    active={
        x:[r for r in runs if r.get("item")==x and r.get("state")!="abandoned"]
        for x in REGIONS
    }
    jobs=[] if "analysis_jobs" not in t else [
        decode(r) for r in rows(
            c,
            f"select * from analysis_jobs where song_id in ({marks}) order by id",
            tuple(ids)
        )
    ]

    arts={}
    if runs and "scientific_artifacts" in t:
        rids=[int(r["id"]) for r in runs]
        rm=",".join("?" for _ in rids)
        for r in rows(
            c,
            f"select * from scientific_artifacts where run_id in ({rm}) order by run_id,id",
            tuple(rids)
        ):
            arts.setdefault(int(r["run_id"]),[]).append(decode(r))

    legacy=[] if "benchmark_runs" not in t else [
        decode(r) for r in rows(
            c,
            f"select * from benchmark_runs where song_id in ({marks}) order by id",
            tuple(ids)
        )
    ]

    human_validations=[] if "profile_human_validations" not in t else [
        decode(r) for r in rows(
            c,
            f"""select v.*
                from profile_human_validations v
                join scientific_runs sr on sr.id=v.run_id
                where sr.song_id in ({marks})
                order by v.run_id,v.subject_key""",
            tuple(ids)
        )
    ]

    present=[bool(active[x]) for x in REGIONS]
    gap=False
    valid=True
    for x in present:
        if not x: gap=True
        elif gap: valid=False

    latest={}
    for x in REGIONS:
        r=active[x][-1] if active[x] else None
        latest[x]=None if r is None else {
            "run_id":int(r["id"]),
            "public_id":r.get("public_id"),
            "state":r.get("state"),
            "engine_name":r.get("engine_name"),
            "engine_version":r.get("engine_version"),
            "model_name":r.get("model_name"),
        }

    genome=genome_payload(c,t,[int(r["id"]) for r in runs])

    manifest={
        "schema":"ezstudio.chromosome.adn.v2",
        "generated_at":datetime.now(timezone.utc).isoformat(),
        "song":song,
        "catalog_song_ids":ids,
        "chromosome":{
            "regions":latest,
            "integrity":{
                "order":list(REGIONS),
                "present":dict(zip(REGIONS,present)),
                "valid_prefix":valid,
            },
        },
        "genomic_evolution":{
            "schema":genome["schema"],
            "available":genome["available"],
            "regions":genome.get("regions",[]),
            "baselines":genome.get("baselines",[]),
        },
        "counts":{
            "scientific_runs":len(runs),
            "analysis_jobs":len(jobs),
            "legacy_chords_runs":len(legacy),
            "profile_human_validations":len(human_validations),
            "genome_region_revisions":len(genome.get("region_revisions",[])),
            "genome_gene_revisions":len(genome.get("gene_revisions",[])),
        },
        "binary_audio_included":False,
    }

    out=Path(a.output)
    out.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(out,"w",zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        z.writestr("manifest.json",json.dumps(manifest,ensure_ascii=False,indent=2)+"\n")
        z.writestr("sqlite/analysis_jobs.json",json.dumps(jobs,ensure_ascii=False,indent=2,default=str)+"\n")
        z.writestr("sqlite/legacy_chords_runs.json",json.dumps(legacy,ensure_ascii=False,indent=2,default=str)+"\n")
        z.writestr("sqlite/profile_human_validations.json",json.dumps(human_validations,ensure_ascii=False,indent=2,default=str)+"\n")
        links=genome.get("run_links",[])
        for run in runs:
            rid=int(run["id"])
            region=str(run.get("item") or "unknown")
            pid=str(run.get("public_id") or f"{region}-{rid}")
            payload=dict(run)
            payload["artifacts"]=arts.get(rid,[])
            payload["genome"]=next((x for x in links if int(x["run_id"])==rid),None)
            z.writestr(
                f"sqlite/regions/{safe(region)}/{safe(pid)}.json",
                json.dumps(payload,ensure_ascii=False,indent=2,default=str)+"\n"
            )
            for art in arts.get(rid,[]):
                p=Path(str(art.get("path") or ""))
                if p.is_file() and p.suffix.lower() in TEXT_SUFFIXES and p.stat().st_size<=25*1024*1024:
                    z.write(p,f"artifacts/{safe(region)}/{safe(pid)}/{safe(p.name)}")

        for name in (
            "run_links","region_revisions","region_parents",
            "region_genes","gene_revisions","baselines"
        ):
            z.writestr(
                f"genome/{name}.json",
                json.dumps(genome.get(name,[]),ensure_ascii=False,indent=2,default=str)+"\n"
            )

        z.writestr(
            "README.txt",
            "EZStudio_lab chromosome ADN bundle v2\n"
            "Two orthogonal histories are preserved:\n"
            "1) scientific runs per song;\n"
            "2) genomic evolution of region/gene revisions.\n"
            "No heavy audio binaries included.\n"
        )

    print(f"EZSTUDIO_CHROMOSOME_ADN_EXPORT_V2_OK {out}")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
