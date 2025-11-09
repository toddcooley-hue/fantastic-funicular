# 🎓 Job Agent Prototype

A configurable Python agent that aggregates **HigherEdJobs** and other RSS job feeds, filters and scores postings, and exports daily CSV results.  
Built and scheduled entirely through **GitHub Actions** — no local environment needed.

---

## 🧭 Overview

The agent:
1. Pulls postings from multiple job sources (RSS and APIs).  
2. Normalizes each job’s data (title, company, location, URL, etc.).  
3. Filters by keywords, location, and recency.  
4. Writes a clean CSV (`outputs/new_jobs.csv`) with new matches.  
5. Uploads the CSV as an **artifact** to GitHub Actions after each run.

---

## 🗂 Folder Structure

job_agent/
│
├── init.py
├── ingest.py # Main pipeline: fetch → filter → save
├── main.py # Entry point for manual or scheduled runs
├── matcher.py # Rule-based filtering/scoring
├── models.py # SQLite schema
├── notifier.py # Placeholder (no notifications enabled)
└── sources/
├── init.py
├── base.py
├── rss.py # Generic RSS fetcher
└── remotive.py # Example API source (optional)

yaml
Copy code

---

## ⚙️ Configuration

All behavior lives in [`config.yaml`](./config.yaml).

```yaml
filters:
  include_keywords: ["Director", "Enrollment", "CRM", "Admissions", "Marketing"]
  exclude_keywords: ["Faculty", "Professor", "Adjunct"]
  locations: ["Remote", "Massachusetts", "Vermont", "Maine"]
  staleness_days: 14

sources:
  - type: rss
    name: HEJ Enrollment
    url: "https://www.higheredjobs.com/rss/enrollment.xml"
  - type: rss
    name: HEJ Marketing
    url: "https://www.higheredjobs.com/rss/marketing.xml"
  - type: rss
    name: HEJ Remote
    url: "https://www.higheredjobs.com/rss/remote.xml"

notify:
  enabled: false
To change what the agent pulls, just edit your sources and filters here — no code changes needed.

🕰 GitHub Actions Automation
The workflow run-agent.yml runs daily at 8 AM ET, installs dependencies, runs the agent, and uploads outputs/new_jobs.csv as an artifact.

You can also trigger it manually:

Actions → Run Job Agent → “Run workflow”

Artifacts live at the bottom of each run’s summary page.

🧪 Local Testing (optional)
If you later clone this repo:

bash
Copy code
python -m venv .venv
source .venv/bin/activate     # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
python -m job_agent.main
Results will appear in outputs/new_jobs.csv.

🪴 Next Steps
✅ Confirm HigherEdJobs feeds pull correctly

🔲 Add optional semantic matching (SentenceTransformers)

🔲 Re-enable Slack/email notifications if desired

🔲 Expand to other niche boards (InsideHigherEd, Chronicle, etc.)

Prototype built by Todd Cooley
Designed for Higher Ed professionals exploring data-driven career search tools.

