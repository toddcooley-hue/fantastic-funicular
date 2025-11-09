# job_agent/ingest.py

import hashlib, yaml, os
from datetime import datetime
from dotenv import load_dotenv
from sqlalchemy import select
from job_agent.models import get_session, Job
from job_agent.sources.rss import RSSSource
from job_agent.sources.remotive import RemotiveSource
from job_agent.matcher import passes_filters, score

def make_hash(*parts): 
    return hashlib.sha1("||".join(parts).encode()).hexdigest()

def make_source(s):
    if s["type"] == "rss":
        return RSSSource(s["name"], s["url"])
    if s["type"] == "api" and s["name"] == "remotive":
        return RemotiveSource(s.get("category",""))
    raise ValueError(f"Unknown source: {s}")

def run_once(config_path="config.yaml", db="sqlite:///jobs.db"):
    load_dotenv()
    with open(config_path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    session = get_session(db)

    # 1) pull from all sources
    raw_jobs = []
    for s in cfg["sources"]:
        src = make_source(s)
        try:
            jobs = src.fetch()
        except Exception as e:
            print(f"[source:{s.get('name','unknown')}] error: {e} (skipping)")
            jobs = []
        for j in jobs:
            ext_id = j.get("external_id") or make_hash(j.get("url",""), j.get("title",""))
            raw_jobs.append({**j, "source": s.get("name","unknown"), "external_id": ext_id})

    # 2) upsert + dedupe
    new_or_updated = []
    for j in raw_jobs:
        exists = session.execute(
            select(Job).where(Job.source == j["source"], Job.external_id == j["external_id"])
        ).scalar_one_or_none()
        if not exists:
            session.add(Job(**j))
            new_or_updated.append(j)
        else:
            exists.title = j.get("title", "")
            exists.company = j.get("company", "")
            exists.location = j.get("location", "")
            exists.url = j.get("url", "")
            exists.description = j.get("description", "")
            exists.published_at = j.get("published_at")
            exists.salary = j.get("salary")
            exists.raw = j.get("raw", "")
            new_or_updated.append(j)
    session.commit()

    # 3) filter + score
    candidates = [j for j in new_or_updated if passes_filters(j, cfg)]
    for c in candidates:
        c["_score"] = score(c, cfg)
    candidates.sort(key=lambda x: x["_score"], reverse=True)

    # 4) select only those not notified yet (mark so we don't repeat)
    to_notify = []
    for c in candidates:
        row = session.execute(
            select(Job).where(Job.source == c["source"], Job.external_id == c["external_id"])
        ).scalar_one()
        if not row.notified:
            to_notify.append(c)
            row.notified = True
    session.commit()

    # 5) console output
    if to_notify:
        print(f"\n✅ {len(to_notify)} new matches found:\n")
        for j in to_notify:
            print(f"- {j['title']} — {j.get('company','')} ({j.get('location','')})")
            print(f"  {j['url']}\n")
    else:
        print("No new matches found.")

    # 6) always write CSV to outputs/
    out_dir = os.path.join(os.getcwd(), "outputs")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.abspath(os.path.join(out_dir, "new_jobs.csv"))

    # write with pandas if available; fallback to csv module
    try:
        import pandas as pd
        pd.DataFrame(to_notify).to_csv(out_path, index=False)
        print(f"[write] Saved CSV via pandas → {out_path} ({len(to_notify)} rows)")
    except Exception as e:
        print(f"[write] pandas failed ({e}); falling back to csv module")
        import csv
        fieldnames = sorted({k for j in to_notify for k in j.keys()}) if to_notify else []
        with open(out_path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=fieldnames)
            if fieldnames: w.writeheader()
            for row in to_notify: w.writerow(row)
        print(f"[write] Saved CSV via csv module → {out_path} ({len(to_notify)} rows)")



