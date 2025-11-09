# job_agent/sources/remotive.py
import requests
from datetime import datetime

class RemotiveSource:
    def __init__(self, category: str = ""):
        self.category = category

    def fetch(self):
        params = {}
        if self.category:
            params["category"] = self.category
        r = requests.get("https://remotive.com/api/remote-jobs", params=params, timeout=20)
        r.raise_for_status()
        data = r.json().get("jobs", [])
        out = []
        for j in data:
            out.append({
                "external_id": str(j["id"]),
                "title": j["title"],
                "company": j.get("company_name", ""),
                "location": j.get("candidate_required_location", ""),
                "url": j["url"],
                "description": j.get("description", ""),
                "published_at": datetime.fromisoformat(j["publication_date"].replace("Z","+00:00")),
                "salary": None,   # parse from j.get("salary") if present
                "raw": r.text,
            })
        return out
