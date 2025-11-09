# job_agent/sources/rss.py
import feedparser
from datetime import datetime
from bs4 import BeautifulSoup

def _clean_html(html: str) -> str:
    return BeautifulSoup(html or "", "html.parser").get_text(" ", strip=True)

class RSSSource:
    def __init__(self, name: str, url: str):
        self.name = name
        self.url = url

    def fetch(self):
        feed = feedparser.parse(self.url)
        out = []
        for e in feed.entries:
            desc = _clean_html(getattr(e, "summary", "") or getattr(e, "description", ""))
            pub = getattr(e, "published_parsed", None)
            out.append({
                "external_id": getattr(e, "id", getattr(e, "link", "")),
                "title": e.title,
                "company": "",         # many RSS feeds don’t include; fine to leave blank
                "location": "",
                "url": e.link,
                "description": desc,
                "published_at": datetime(*pub[:6]) if pub else None,
                "salary": None,
                "raw": str(e),
            })
        return out
