// check-lighthouse (design book, layout.md, Checks before every release): Lighthouse 12 mobile preset on three page types,
// each category at 90 or more; a page under 90 fails the deploy. Serves ./dist gzipped, as GitHub Pages does.
// Usage: node tools/check_lighthouse.js   (needs lighthouse, chrome-launcher and Playwright's Chromium)
// One run per page; a page under 90 gets two more and its median counts, so one slow run does not stop a deploy.
const http = require('http');
const fs = require('fs');
const path = require('path');
const zlib = require('zlib');
const { chromium } = require('playwright');

const DIST = path.resolve(__dirname, '..', 'dist');
const MIN = 90;
const MIME = { '.html': 'text/html', '.css': 'text/css', '.js': 'text/javascript', '.json': 'application/json', '.svg': 'image/svg+xml',
  '.png': 'image/png', '.woff2': 'font/woff2', '.xml': 'application/xml', '.txt': 'text/plain', '.webmanifest': 'application/manifest+json' };

// a seller page: the first one built, else a page every build has
function pages() {
  const dir = path.join(DIST, 'sellers');
  const seller = fs.existsSync(dir) ? fs.readdirSync(dir, { withFileTypes: true }).find((e) => e.isDirectory()) : null;
  return ['/', '/weight-loss/', seller ? `/sellers/${seller.name}/` : '/about/'];
}

function serve() {
  return new Promise((resolve) => {
    const s = http.createServer((req, res) => {
      let f = path.join(DIST, decodeURIComponent(req.url.split('?')[0]));
      if (fs.existsSync(f) && fs.statSync(f).isDirectory()) f = path.join(f, 'index.html');
      if (!fs.existsSync(f)) { res.statusCode = 404; return res.end('404'); }
      const ext = path.extname(f), body = fs.readFileSync(f);
      res.setHeader('content-type', MIME[ext] || 'application/octet-stream');
      if (['.html', '.css', '.js', '.json', '.svg', '.xml', '.txt'].includes(ext)) { res.setHeader('content-encoding', 'gzip'); return res.end(zlib.gzipSync(body)); }
      res.end(body);
    });
    s.listen(0, () => resolve(s));
  });
}

(async () => {
  const lighthouse = (await import('lighthouse')).default;
  const { launch } = await import('chrome-launcher');
  const server = await serve();
  const base = `http://127.0.0.1:${server.address().port}`;
  const started = Date.now();
  const once = async (p) => {
    const chrome = await launch({ chromeFlags: ['--headless=new', '--no-sandbox'], chromePath: chromium.executablePath() });
    try {
      const { lhr } = await lighthouse(base + p, { port: chrome.port, output: 'json', logLevel: 'error',
        onlyCategories: ['performance', 'accessibility', 'best-practices', 'seo'] });
      return Object.fromEntries(Object.entries(lhr.categories).map(([k, v]) => [k, Math.round(v.score * 100)]));
    } finally { await chrome.kill(); }
  };
  const low = (r) => Object.entries(r).filter(([, v]) => v < MIN);
  const problems = [];
  for (const p of pages()) {
    let r = await once(p);
    if (low(r).length) {
      const runs = [r, await once(p), await once(p)];
      r = Object.fromEntries(Object.keys(r).map((k) => [k, runs.map((x) => x[k]).sort((a, b) => a - b)[1]]));
    }
    console.log(`  ${p}: ${Object.entries(r).map(([k, v]) => `${k} ${v}`).join(', ')}`);
    if (low(r).length) problems.push(`${p}: ${low(r).map(([k, v]) => `${k} ${v}`).join(', ')} (under ${MIN})`);
  }
  server.close();
  console.log(`check-lighthouse: ${problems.length ? problems.length + ' problem(s)' : 'ok'} (${Math.round((Date.now() - started) / 1000)}s)`);
  problems.forEach((x) => console.log('  -', x));
  process.exit(problems.length ? 1 : 0);
})();
