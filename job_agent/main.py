# job_agent/main.py
import argparse
from apscheduler.schedulers.blocking import BlockingScheduler
from job_agent.ingest import run_once

def run():
    try:
        stats = run_once()
    except Exception as e:
        print(f"[run] error: {e}")
        return  # don't crash the workflow; logs will show the error

    if not isinstance(stats, dict):
        print("[run] completed without stats dict (no counts to show)")
        return

    print(f"Fetched/updated: {stats.get('new', 0)} | Notified: {stats.get('notified', 0)}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--watch", action="store_true",
                        help="Run daily at 8:00 AM America/New_York")
    args = parser.parse_args()

    if args.watch:
        sched = BlockingScheduler(timezone="America/New_York")
        sched.add_job(run, "cron", hour=8, minute=0)
        run()  # run now, too
        sched.start()
    else:
        run()


