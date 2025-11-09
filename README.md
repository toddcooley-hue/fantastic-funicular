# fantastic-funicular
Custom Job Agent running in python

# Job Agent

A modular Python agent that aggregates job postings from multiple public sources, filters and scores them based on configurable criteria, and sends daily notifications for matching roles.

### Core Features
- Config-driven architecture (`config.yaml`)
- Pluggable sources (RSS, APIs)
- Rule-based and semantic matching
- Slack/email notifications
- SQLite persistence for deduplication

### Roadmap
✅ Define architecture  
✅ Add config + models + matcher stubs  
🔲 Implement first source (RSS)  
🔲 Add notification module  
🔲 Deploy scheduled runs via GitHub Actions

*Designed for flexibility and data transparency.*

```mermaid
flowchart LR
  A[Sources: RSS/APIs] --> B[Ingest]
  B --> C[SQLite Store]
  C --> D[Matcher & Scoring]
  D --> E[Notifier: Slack/Email]
```

