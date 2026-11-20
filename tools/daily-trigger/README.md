# Daily 06:00 UTC deploy trigger

GitHub's `schedule` in `.github/workflows/pages.yml` runs late or not at all on a quiet repo (19 Nov 2026: 9 hours late;
20 Nov: no run). This Cloudflare Worker starts "Deploy site" on `main` every day at 06:00 UTC with `daily=true`. The
schedule stays as a backup; the workflow's `gate` job (`tools/daily_gate.py`) lets one daily run a day build.

- `worker.js`: the whole Worker. It has no web address that answers and keeps one secret, `GITHUB_TOKEN`.
- Setup is by hand in two dashboards (owner steps in the PR of queue block 50). The token goes straight from GitHub into
  Cloudflare and is never typed into a chat or a file.
- The token expires; renew it in GitHub and paste the new one into the same Cloudflare secret.
- To see whether it ran: Cloudflare, the Worker, Logs; GitHub, Actions, "Deploy site", a run named for
  `workflow_dispatch` at about 06:00 UTC.
