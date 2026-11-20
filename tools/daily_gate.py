"""Once a day: whether this run of "Deploy site" builds and deploys (queue block 50, 20 Nov 2026).

Two triggers start the daily run: the 06:00 UTC trigger (a workflow_dispatch with daily=true, from the Cloudflare Worker in
tools/daily-trigger/) and GitHub's own schedule as a backup. Whichever comes second skips. A push to main and a manual run
(daily=false) always build.

A daily run skips when, since 05:30 UTC today, a run on main
- succeeded (any trigger: the prices are as fresh as that run), or
- was a daily or manual run that stopped (it already said why; the next try is tomorrow or a manual run), or
- is a daily or manual run still running.
Before 05:30 UTC a daily run skips too: it is yesterday's late schedule, and today's 06:00 run follows.
If GitHub cannot be asked, the run builds: two deploys are better than none.

Writes run=true|false to $GITHUB_OUTPUT and one line to $GITHUB_STEP_SUMMARY.
Run the tests: python3 tools/test_daily_gate.py"""
import json
import os
import sys
import urllib.request
from datetime import datetime, timezone

WINDOW = (5, 30)  # the daily window opens at 05:30 UTC
DAILY_EVENTS = {"schedule", "workflow_dispatch"}


def window_start(now):
    return now.replace(hour=WINDOW[0], minute=WINDOW[1], second=0, microsecond=0)


def when(run):
    return datetime.fromisoformat((run.get("run_started_at") or run["created_at"]).replace("Z", "+00:00"))


def decide(event, daily, now, runs, this_run_id):
    """(build, line). runs: GitHub's workflow runs on main, newest first."""
    if event == "push":
        return True, None
    if event == "workflow_dispatch" and not daily:
        return True, None
    start = window_start(now)
    if now < start:
        return False, "Skipped: daily run before 05:30 UTC (a late one from yesterday); today's 06:00 UTC run follows."
    for r in runs:
        if r["id"] == this_run_id or when(r) < start:
            continue
        at = f'{when(r):%H:%M} UTC (run #{r["run_number"]}, {r["event"]})'
        if r.get("conclusion") == "success":
            return False, f"Skipped: a deploy on main already succeeded today at {at}."
        if r["event"] in DAILY_EVENTS and r.get("conclusion") == "failure":
            return False, f"Skipped: today's daily run already ran at {at} and stopped; its summary says why."
        if r["event"] in DAILY_EVENTS and r.get("status") in ("queued", "in_progress", "waiting", "pending"):
            return False, f"Skipped: today's daily run is already running, started {at}."
    return True, None


def runs_since(start):
    repo, token = os.environ["GITHUB_REPOSITORY"], os.environ["GH_TOKEN"]
    url = (f"https://api.github.com/repos/{repo}/actions/workflows/pages.yml/runs"
           f"?branch=main&per_page=100&created=%3E%3D{start:%Y-%m-%dT%H:%M:%SZ}")
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json",
                                               "X-GitHub-Api-Version": "2022-11-28", "User-Agent": "deploy-site-daily-gate"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)["workflow_runs"]


def main():
    event = os.environ.get("EVENT", "")
    daily = os.environ.get("DAILY", "").lower() == "true"
    now = datetime.now(timezone.utc)
    runs = []
    if event == "schedule" or (event == "workflow_dispatch" and daily):
        try:
            runs = runs_since(window_start(now))
        except Exception as e:  # noqa: BLE001 - any failure to ask GitHub means build
            build, line = True, f"Daily gate could not ask GitHub ({type(e).__name__}), so this run builds."
        else:
            build, line = decide(event, daily, now, runs, int(os.environ.get("GITHUB_RUN_ID", "0")))
    else:
        build, line = decide(event, daily, now, runs, 0)
    if build and line is None and (event == "schedule" or event == "workflow_dispatch" and daily):
        line = f"Daily run ({'06:00 UTC trigger' if event == 'workflow_dispatch' else 'GitHub schedule'}) builds and deploys."
    if line:
        print(line)
    for name, text in (("GITHUB_OUTPUT", f"run={'true' if build else 'false'}\n"),
                       ("GITHUB_STEP_SUMMARY", f"**{line}**\n" if line else "")):
        if os.environ.get(name) and text:
            with open(os.environ[name], "a", encoding="utf-8") as f:
                f.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
