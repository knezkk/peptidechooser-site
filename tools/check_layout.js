// check-layout (rulebook 11.12, design book layout.md): no sideways scroll on any page at any width.
// Usage: node tools/check_layout.js  (serves ./dist itself)
const { chromium } = require('playwright');
const http = require('http');
const fs = require('fs');
const path = require('path');

const DIST = path.resolve(__dirname, '..', 'dist');
const WIDTHS = [320, 390, 768, 1024, 1440, 1920, 2560];
const MIME = { '.html': 'text/html', '.css': 'text/css', '.svg': 'image/svg+xml', '.png': 'image/png', '.js': 'text/javascript' };

function serve() {
  return new Promise((resolve) => {
    const s = http.createServer((req, res) => {
      let p = decodeURIComponent(req.url.split('?')[0]);
      let f = path.join(DIST, p);
      if (fs.existsSync(f) && fs.statSync(f).isDirectory()) f = path.join(f, 'index.html');
      if (!fs.existsSync(f)) { res.statusCode = 404; return res.end('404'); }
      res.setHeader('content-type', MIME[path.extname(f)] || 'application/octet-stream');
      fs.createReadStream(f).pipe(res);
    });
    s.listen(0, () => resolve(s));
  });
}

function pages(dir, base = '') {
  const out = [];
  for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
    if (e.isDirectory()) out.push(...pages(path.join(dir, e.name), base + '/' + e.name));
    else if (e.name.endsWith('.html')) out.push(base + '/' + (e.name === 'index.html' ? '' : e.name));
  }
  return out;
}

(async () => {
  const server = await serve();
  const port = server.address().port;
  const list = pages(DIST);
  const browser = await chromium.launch();
  const problems = [];
  let n = 0;
  for (const w of WIDTHS) {
    const page = await browser.newPage({ viewport: { width: w, height: 900 } });
    for (const p of list) {
      await page.goto(`http://127.0.0.1:${port}${p}`, { waitUntil: 'load' });
      const r = await page.evaluate(() => {
        const sw = document.documentElement.scrollWidth, iw = window.innerWidth;
        const wraps = [...document.querySelectorAll('.wrap')];
        let outside = 0;
        for (const el of document.body.querySelectorAll('*')) {
          if (el.closest('.tbl-wrap, .nav')) continue;
          const b = el.getBoundingClientRect();
          if (b.width && b.right > iw + 1) outside++;
        }
        return { sw, iw, outside };
      });
      n++;
      if (r.sw > r.iw) problems.push(`${w}px ${p}: page scrolls sideways (${r.sw} > ${r.iw})`);
      if (r.outside) problems.push(`${w}px ${p}: ${r.outside} element(s) past the right edge`);
    }
    await page.close();
  }
  await browser.close();
  server.close();
  console.log(`check-layout: ${problems.length ? problems.length + ' problem(s)' : 'ok'} (${n} checks)`);
  problems.forEach((x) => console.log('  -', x));
  process.exit(problems.length ? 1 : 0);
})();
