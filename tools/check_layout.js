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
    // a redirect page (data/redirects.json) moves on at once and has no layout of its own
    else if (e.name.endsWith('.html') && !fs.readFileSync(path.join(dir, e.name), 'utf8').includes('http-equiv="refresh"'))
      out.push(base + '/' + (e.name === 'index.html' ? '' : e.name));
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
        let outside = 0, which = [];
        for (const el of document.body.querySelectorAll('*')) {
          if (el.closest('.tbl-wrap, .nav')) continue;
          const b = el.getBoundingClientRect();
          if (b.width && b.right > iw + 1) {
            outside++;
            // name the element, so a failure in the deploy (real data only) can be fixed without guessing
            if (which.length < 3) which.push(`${el.tagName.toLowerCase()}.${(el.className || '').toString().split(' ').join('.')} "${(el.textContent || '').trim().slice(0, 40)}"`);
          }
        }
        return { sw, iw, outside, which };
      });
      n++;
      if (r.sw > r.iw) problems.push(`${w}px ${p}: page scrolls sideways (${r.sw} > ${r.iw})`);
      if (r.outside) problems.push(`${w}px ${p}: ${r.outside} element(s) past the right edge: ${r.which.join(', ')}`);
    }
    await page.close();
  }
  // Header cards (pages.md, Every page, Header; owner task 3 Nov 2026): each category open at 1180, 1440, 1920 and 2560px
  // leaves no sideways scroll, stays inside the container (24px clear of its right edge) and keeps one pixel width
  // from 1440px up.
  const cardW = {};
  for (const w of [1180, 1440, 1920, 2560]) {
    const page = await browser.newPage({ viewport: { width: w, height: 900 } });
    await page.goto(`http://127.0.0.1:${port}/`, { waitUntil: 'load' });
    const count = await page.evaluate(() => document.querySelectorAll('.nav-cat').length);
    for (let i = 0; i < count; i++) {
      await page.click(`.nav-cat:nth-child(${i + 1}) .nav-cat-btn`);
      const r = await page.evaluate((i) => {
        const c = document.querySelectorAll('.nav-cat')[i], pn = c.querySelector('.nav-panel'), w = document.querySelector('.site-head .wrap');
        const b = pn.getBoundingClientRect(), wb = w.getBoundingClientRect(), cs = getComputedStyle(w);
        return { open: c.classList.contains('open'), sw: document.documentElement.scrollWidth, iw: window.innerWidth, left: b.left, right: b.right, width: Math.round(b.width),
                 L: wb.left + parseFloat(cs.paddingLeft), R: wb.right - parseFloat(cs.paddingRight) };
      }, i);
      n++;
      const tag = `${w}px header card ${i + 1}`;
      if (!r.open) problems.push(`${tag}: does not open`);
      if (r.sw > r.iw) problems.push(`${tag}: page scrolls sideways`);
      if (r.left < r.L - 1 || r.right > r.R - 24 + 1) problems.push(`${tag}: outside the container (${Math.round(r.left)} to ${Math.round(r.right)})`);
      if (w >= 1440) { (cardW[i] = cardW[i] || new Set()).add(r.width); }
      await page.keyboard.press('Escape');
    }
    await page.close();
  }
  for (const [i, s] of Object.entries(cardW)) if (s.size > 1) problems.push(`header card ${+i + 1}: width changes from 1440px up (${[...s].join(', ')})`);
  // /sellers/ shops tab (pages.md, Sellers; owner task w2, 3 Nov 2026): the clinics tab is the default the loop above
  // measured; the shops tab opens from the hash
  if (list.includes('/sellers/')) for (const w of WIDTHS) {
    const page = await browser.newPage({ viewport: { width: w, height: 900 } });
    await page.goto(`http://127.0.0.1:${port}/sellers/#type=shops`, { waitUntil: 'load' });
    const r = await page.evaluate(() => ({ sw: document.documentElement.scrollWidth, iw: window.innerWidth,
      shown: !document.getElementById('shops') || !document.getElementById('shops').hidden }));
    n++;
    if (!r.shown) problems.push(`${w}px /sellers/#type=shops: the shops tab does not open`);
    if (r.sw > r.iw) problems.push(`${w}px /sellers/#type=shops: page scrolls sideways (${r.sw} > ${r.iw})`);
    await page.close();
  }
  await browser.close();
  server.close();
  console.log(`check-layout: ${problems.length ? problems.length + ' problem(s)' : 'ok'} (${n} checks)`);
  problems.forEach((x) => console.log('  -', x));
  process.exit(problems.length ? 1 : 0);
})();
