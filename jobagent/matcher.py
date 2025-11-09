# job_agent/matcher.py
import re
from datetime import datetime, timedelta

def passes_filters(job, cfg):
    text = " ".join([
        job.get("title",""), job.get("company",""),
        job.get("location",""), job.get("description","")
    ]).lower()

    inc = cfg["filters"]["include_keywords"]
    exc = cfg["filters"]["exclude_keywords"]
    locs = [l.lower() for l in cfg["filters"]["locations"]]
    staleness = cfg.get("staleness_days", 10)

    if job.get("published_at") and job["published_at"] < datetime.utcnow() - timedelta(days=staleness):
        return False

    if inc and not any(k.lower() in text for k in inc):
        return False
    if any(k.lower() in text for k in exc):
        return False

    if locs and not any(l in text for l in locs):
        # allow if job explicitly says remote
        if "remote" not in text:
            return False

    if cfg.get("salary_min") and job.get("salary") and job["salary"] < cfg["salary_min"]:
        return False

    return True

def score(job, cfg):
    # simple additive scoring
    base = 0
    title = job.get("title","").lower()
    for k in cfg["filters"]["include_keywords"]:
        if k.lower() in title:
            base += 2
    if "remote" in (job.get("location","") + job.get("description","")).lower():
        base += 1
    return base
