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
        for j in src.fetch():
            ext_id = j.get("external_id") or make_hash(j.get("url",""), j.get("title",""))
            raw_jobs.append({**j, "source": s.get("name","unknown"), "external_id": ext_id})

    # 2) upsert + dedupe
    new_or_updated = []
    for j in raw_jobs:
        exists = session.execute(
            select(Job).where(Job.source==j["source"], Job.external_id==j["external_id"])
        ).scalar_one_or_none()
        if not exists:
            row = Job(**j)
            session.add(row)
            new_or_updated.append(j)
        else:
            exists.title = j["title"]
            exists.company = j.get("company","")
            exists.location = j.get("location","")
            exists.url = j.get("url","")
            exists.description = j.get("description","")
            exists.published_at = j.get("published_at")
            exists.salary = j.get("salary")
            exists.raw = j.get("raw","")
            new_or_updated.append(j)
    session.commit()

    # 3) filter + score
    candidates = [j for j in new_or_updated if passes_filters(j, cfg)]
    for c in candidates:
        c["_score"] = score(c, cfg)
    candidates.sort(key=lambda x: x["_score"], reverse=True)

    # 4) select only those not notified yet (we still mark them so we don't repeat)
    to_notify = []
    for c in candidates:
        row = session.execute(
            select(Job).where(Job.source==c["source"], Job.external_id==c["external_id"])
        ).scalar_one()
        if not row.notified:
            to_notify.append(c)
            row.notified = True
    session.commit()

    # 5) output results instead of notifying
    if to_notify:
        print(f"\n✅ {len(to_notify)} new matches found:\n")
        for j in to_notify:
            print(f"- {j['title']} — {j.get('company','')} ({j.get('location','')})")
            print(f"  {j['url']}\n")

        import os
from datetime import datetime

# ... after you build `to_notify` and before return:

# ensure output dir
out_dir = os.path.join(os.getcwd(), "outputs")
os.makedirs(out_dir, exist_ok=True)

# always write a CSV (even if empty) so Actions can upload it
try:
    import pandas as pd
    df = pd.DataFrame(to_notify)
    out_path = os.path.join(out_dir, "new_jobs.csv")   # fixed name for Actions
    df.to_csv(out_path, index=False)
    print(f"Saved {out_path} ({len(df)} rows)")
except Exception as e:
    print(f"CSV write skipped ({e})")


        # optional CSV output
        try:
            import pandas as pd
            pd.DataFrame(to_notify).to_csv("new_jobs.csv", index=False)
            print("Saved new_jobs.csv")
        except Exception as e:
            print(f"CSV write skipped ({e})")
    else:
        print("No new matches found.")

    return {"new": len(new_or_updated), "notified": len(to_notify)}

