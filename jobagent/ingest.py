# job_agent/ingest.py
import hashlib, yaml, os
from datetime import datetime
from dotenv import load_dotenv
from sqlalchemy import select, update
from job_agent.models import get_session, Job
from job_agent.sources.rss import RSSSource
from job_agent.sources.remotive import RemotiveSource
from job_agent.matcher import passes_filters, score
from job_agent.notifier import notify_slack, notify_email

def make_hash(*parts): return hashlib.sha1("||".join(parts).encode()).hexdigest()

def make_source(s):
    if s["type"] == "rss":
        return RSSSource(s["name"], s["url"])
    if s["type"] == "api" and s["name"] == "remotive":
        return RemotiveSource(s.get("category",""))
    raise ValueError(f"Unknown source: {s}")

def run_once(config_path="config.yaml", db="sqlite:///jobs.db"):
    load_dotenv()
    cfg = yaml.safe_load(open(config_path, "r", encoding="utf-8"))
    session = get_session(db)

    # 1) pull from all sources
    raw_jobs = []
    for s in cfg["sources"]:
        src = make_source(s)
        for j in src.fetch():
            ext_id = j["external_id"] or make_hash(j.get("url",""), j.get("title",""))
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
            # keep earliest seen; update fresh fields
            exists.title = j["title"]; exists.company = j["company"]
            exists.location = j["location"]; exists.url = j["url"]
            exists.description = j["description"]; exists.published_at = j["published_at"]
            exists.salary = j["salary"]; exists.raw = j["raw"]
            new_or_updated.append(j)
    session.commit()

    # 3) filter + score
    candidates = [j for j in new_or_updated if passes_filters(j, cfg)]
    for c in candidates:
        c["_score"] = score(c, cfg)
    candidates.sort(key=lambda x: x["_score"], reverse=True)

    # 4) select only those not notified yet
    to_notify = []
    for c in candidates:
        row = session.execute(
            select(Job).where(Job.source==c["source"], Job.external_id==c["external_id"])
        ).scalar_one()
        if not row.notified:
            to_notify.append(c)
            row.notified = True
    session.commit()

    # 5) notify
    if to_notify:
        notify_slack(os.getenv("SLACK_WEBHOOK_URL") or cfg["notify"].get("slack_webhook"), to_notify)
        notify_email(cfg, to_notify)

    return {"new": len(new_or_updated), "notified": len(to_notify)}
