// Starts the "Deploy site" workflow on main every day at 06:00 UTC (queue block 50, 20 Nov 2026).
// A Cloudflare Worker with a Cron Trigger "0 6 * * *"; its one secret, GITHUB_TOKEN, is a fine-grained token limited to
// knezkk/peptidechooser-site with "Actions: Read and write". Set up by hand in the Cloudflare dashboard (README.md here).
// It sends daily=true, so the workflow's gate job lets only one daily run a day build; GitHub's own schedule is the backup.
// No fetch handler: the Worker answers nothing on the web.

const DISPATCH_URL = "https://api.github.com/repos/knezkk/peptidechooser-site/actions/workflows/pages.yml/dispatches";
const TRIES = 3;

async function dispatch(token) {
  let last = "";
  for (let i = 1; i <= TRIES; i++) {
    const res = await fetch(DISPATCH_URL, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
        Accept: "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "peptidechooser-daily-trigger",
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ ref: "main", inputs: { daily: "true" } }),
    });
    if (res.status === 204) return `started on try ${i}`;
    last = `${res.status} ${(await res.text()).slice(0, 200)}`;
    if (res.status === 401 || res.status === 403 || res.status === 404 || res.status === 422) break; // a wrong token or name: trying again will not help
    await new Promise((r) => setTimeout(r, 20000 * i));
  }
  throw new Error(`could not start Deploy site: ${last}`);
}

export default {
  async scheduled(event, env, ctx) {
    if (!env.GITHUB_TOKEN) throw new Error("GITHUB_TOKEN secret is missing");
    console.log(await dispatch(env.GITHUB_TOKEN));
  },
};
