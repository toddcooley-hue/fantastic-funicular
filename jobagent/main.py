# job_agent/main.py
import argparse
from apscheduler.schedulers.blocking import BlockingScheduler
from job_agent.ingest import run_once

def run():
    stats = run_once()
    print(f"Fetched/updated: {stats['new']} | Notified: {stats['notified']}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--watch", action="store_true", help="Run daily at 8:00 AM")
    args = parser.parse_args()

    if args.watch:
        sched = BlockingScheduler(timezone="America/New_York")
        sched.add_job(run, "cron", hour=8, minute=0)
        run()  # run now, too
        sched.start()
    else:
        run()
