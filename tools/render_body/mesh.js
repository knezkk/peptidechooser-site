// Offline only. Builds one posed, smoothed, baked body from the MakeHuman CC0 data and writes it to BODY_WORK.
// Usage: BODY_WORK=/some/dir node tools/render_body/mesh.js female|male
// Needs three and three-mesh-bvh (see README.md); nothing here ships to the page.
const fs = require('fs');
const path = require('path');
const https = require('https');
const THREE = require('three');
const { MeshBVH } = require('three-mesh-bvh');

const LID = +(process.env.BODY_LID || .5);
const WORK = process.env.BODY_WORK || '/tmp/pc-body';
const SEX = process.argv[2] || 'female';
// Pinned so a re-render uses the same model. LICENSE.ASSETS.md in that commit is CC0 1.0.
const COMMIT = process.env.MH_COMMIT || 'a8bc2d54ff0ac92e78ff71431b1023eda42bf482';
const RAW = `https://raw.githubusercontent.com/makehumancommunity/makehuman/${COMMIT}/makehuman/data/`;

function get(rel) {
  const file = path.join(WORK, 'mh', rel);
  if (fs.existsSync(file)) return Promise.resolve(fs.readFileSync(file, 'utf8'));
  fs.mkdirSync(path.dirname(file), { recursive: true });
  return new Promise((ok, no) => {
    https.get(RAW + rel, { family: 4 }, r => {
      if (r.statusCode !== 200) return no(new Error(rel + ': HTTP ' + r.statusCode));
      let s = ''; r.setEncoding('utf8'); r.on('data', d => s += d);
      r.on('end', () => { fs.writeFileSync(file, s); ok(s); });
    }).on('error', no);
  });
}

function parseObj(text) {
  const V = [], F = []; let group = '';
  const eye = {};
  for (const line of text.split('\n')) {
    if (line.startsWith('v ')) { const p = line.split(/\s+/); V.push([+p[1], +p[2], +p[3]]); }
    else if (line.startsWith('g ')) group = line.slice(2).trim();
    else if (line.startsWith('f ')) {
      const idx = line.trim().split(/\s+/).slice(1).map(s => parseInt(s, 10) - 1);
      if (group === 'body') F.push(idx);
      else if (group === 'joint-l-eye' || group === 'joint-r-eye') (eye[group] = eye[group] || new Set()), idx.forEach(i => eye[group].add(i));
    }
  }
  return { V, F, eye };
}

const applyTarget = (V, text, w) => {
  for (const line of text.split('\n')) {
    if (!line || line[0] === '#') continue;
    const p = line.trim().split(/\s+/); const v = V[+p[0]];
    if (v) { v[0] += w * +p[1]; v[1] += w * +p[2]; v[2] += w * +p[3]; }
  }
};

const mean = (V, ids) => { const c = [0, 0, 0]; ids.forEach(i => { c[0] += V[i][0]; c[1] += V[i][1]; c[2] += V[i][2]; }); return c.map(x => x / ids.length); };

// Linear blend skinning with the MakeHuman default rig: only the arms move, down from the rest pose, so the figure
// stands as a person stands and fits a box twice as tall as wide.
function pose(V, skel, weights, angles) {
  const head = {}, tail = {};
  for (const [n, b] of Object.entries(skel.bones)) { head[n] = mean(V, skel.joints[b.head]); tail[n] = mean(V, skel.joints[b.tail]); }
  const world = {};
  const m4 = n => {
    if (world[n]) return world[n];
    const b = skel.bones[n];
    const parent = b.parent ? m4(b.parent) : new THREE.Matrix4();
    const a = angles[n];
    const local = new THREE.Matrix4();
    if (a) {
      const h = new THREE.Vector3(...head[n]);
      local.makeTranslation(h.x, h.y, h.z)
        .multiply(new THREE.Matrix4().makeRotationFromEuler(new THREE.Euler(a[0], a[1], a[2])))
        .multiply(new THREE.Matrix4().makeTranslation(-h.x, -h.y, -h.z));
    }
    return (world[n] = parent.clone().multiply(local));
  };
  const out = V.map(() => [0, 0, 0]); const sum = new Float32Array(V.length);
  const p = new THREE.Vector3();
  for (const [bone, list] of Object.entries(weights)) {
    if (!skel.bones[bone]) continue;
    const M = m4(bone);
    for (const [i, w] of list) {
      p.set(...V[i]).applyMatrix4(M);
      out[i][0] += w * p.x; out[i][1] += w * p.y; out[i][2] += w * p.z; sum[i] += w;
    }
  }
  const posed = V.map((v, i) => sum[i] > 1e-5 ? out[i].map(x => x / sum[i]) : v.slice());
  const joints = {};
  for (const n of Object.keys(skel.bones)) {
    joints[n] = { head: new THREE.Vector3(...head[n]).applyMatrix4(m4(n)).toArray(), tail: new THREE.Vector3(...tail[n]).applyMatrix4(m4(n)).toArray() };
  }
  return { posed, joints };
}

// One level of Catmull-Clark. Holes (eyes, mouth) keep a plain boundary rule.
function subdivide(V, F) {
  const edge = new Map();
  const key = (a, b) => a < b ? a + '_' + b : b + '_' + a;
  const n = V.length;
  const facePts = F.map(f => mean(V, f));
  const P = V.map(v => v.slice());
  const fCount = new Int32Array(n), fSum = V.map(() => [0, 0, 0]);
  F.forEach((f, fi) => f.forEach((a, j) => {
    const b = f[(j + 1) % f.length], k = key(a, b);
    if (!edge.has(k)) edge.set(k, { a: Math.min(a, b), b: Math.max(a, b), faces: [] });
    edge.get(k).faces.push(fi);
    fCount[a]++; for (let c = 0; c < 3; c++) fSum[a][c] += facePts[fi][c];
  }));
  let idx = n + F.length; facePts.forEach(p => P.push(p));
  const eSum = V.map(() => [0, 0, 0]), eCount = new Int32Array(n), boundary = new Uint8Array(n);
  const bSum = V.map(() => [0, 0, 0]), bCount = new Int32Array(n);
  edge.forEach(e => {
    const mid = [0, 1, 2].map(c => (V[e.a][c] + V[e.b][c]) / 2);
    let pt = mid;
    if (e.faces.length === 2) pt = [0, 1, 2].map(c => (V[e.a][c] + V[e.b][c] + facePts[e.faces[0]][c] + facePts[e.faces[1]][c]) / 4);
    else {
      boundary[e.a] = boundary[e.b] = 1;
      for (let c = 0; c < 3; c++) { bSum[e.a][c] += mid[c]; bSum[e.b][c] += mid[c]; }
      bCount[e.a]++; bCount[e.b]++;
    }
    e.id = idx++; P.push(pt);
    for (let c = 0; c < 3; c++) { eSum[e.a][c] += mid[c]; eSum[e.b][c] += mid[c]; }
    eCount[e.a]++; eCount[e.b]++;
  });
  for (let i = 0; i < n; i++) {
    if (!fCount[i]) continue;
    if (boundary[i]) { for (let c = 0; c < 3; c++) P[i][c] = V[i][c] * .5 + .5 * bSum[i][c] / bCount[i]; continue; }
    const m = eCount[i];
    for (let c = 0; c < 3; c++) P[i][c] = (fSum[i][c] / fCount[i] + 2 * eSum[i][c] / m + (m - 3) * V[i][c]) / m;
  }
  const out = [];
  F.forEach((f, fi) => f.forEach((a, j) => {
    const b = f[(j + 1) % f.length], z = f[(j + f.length - 1) % f.length];
    out.push([a, edge.get(key(a, b)).id, n + fi, edge.get(key(z, a)).id]);
  }));
  return { V: P, F: out };
}

function smoothAround(V, F, spots) {
  // Mannequin, not anatomy: small features inside each sphere are ironed out, which also keeps the figure non-sexualised.
  const nb = V.map(() => new Set());
  F.forEach(f => f.forEach((a, j) => { const b = f[(j + 1) % f.length]; nb[a].add(b); nb[b].add(a); }));
  for (const { at, r, iters } of spots) {
    const weight = new Map();
    V.forEach((v, i) => {
      const d = Math.hypot(v[0] - at[0], v[1] - at[1], v[2] - at[2]);
      if (d < r) weight.set(i, 1 - (d / r) ** 2);
    });
    for (let t = 0; t < iters; t++) {
      const next = new Map();
      weight.forEach((w, i) => {
        const avg = [0, 0, 0]; nb[i].forEach(j => { avg[0] += V[j][0]; avg[1] += V[j][1]; avg[2] += V[j][2]; });
        next.set(i, V[i].map((x, c) => x + .6 * w * (avg[c] / nb[i].size - x)));
      });
      next.forEach((p, i) => { V[i] = p; });
    }
  }
}

// The base mesh leaves an opening for each eye. A mannequin has none: each is closed with a fan around its centre.
function fillEyes(V, F, centres) {
  const count = new Map(); const key = (a, b) => a < b ? a + '_' + b : b + '_' + a;
  const next = new Map();
  F.forEach(f => f.forEach((a, j) => { const b = f[(j + 1) % f.length], k = key(a, b); count.set(k, (count.get(k) || 0) + 1); }));
  F.forEach(f => f.forEach((a, j) => { const b = f[(j + 1) % f.length]; if (count.get(key(a, b)) === 1) next.set(a, b); }));
  const seen = new Set();
  for (const start of next.keys()) {
    if (seen.has(start)) continue;
    const loop = []; let c = start;
    while (c !== undefined && !seen.has(c)) { seen.add(c); loop.push(c); c = next.get(c); }
    const m = mean(V, loop);
    if (!centres.some(e => Math.hypot(m[0] - e[0], m[1] - e[1]) < .45)) continue;
    const id = V.length; V.push([m[0], m[1], m[2]]);
    loop.forEach((a, i) => F.push([next.get(a), a, id]));
    console.log('  closed an eye opening of', loop.length, 'edges');
  }
}

// The unisex chest: a depth blur seen from the front, so it does not depend on how dense the mesh is. Takes out the
// breast and the nipple on each side and leaves the plane of the chest.
function flattenChest(V, floorY, top) {
  const H = top - floorY, front = [];
  V.forEach((v, i) => { if (v[1] > floorY + H * .54 && v[1] < floorY + H * .9 && Math.abs(v[0]) < H * .105 && v[2] > 0) front.push(i); });
  for (const side of [1, -1]) {
    let tip = null;
    front.forEach(i => { const v = V[i]; if (v[0] * side > H * .03 && v[0] * side < H * .09 && (!tip || v[2] > tip[2])) tip = v; });
    const R = H * .085, K = H * .04;
    const near = front.filter(i => Math.hypot(V[i][0] - tip[0], V[i][1] - tip[1]) < R);
    const next = near.map(i => {
      let sum = 0, wt = 0;
      for (const j of front) {
        const d = Math.hypot(V[j][0] - V[i][0], V[j][1] - V[i][1]);
        if (d < K * 2) { const w = Math.exp(-(d * d) / (2 * K * K)); sum += w * V[j][2]; wt += w; }
      }
      const f = (1 - (Math.hypot(V[i][0] - tip[0], V[i][1] - tip[1]) / R) ** 2) ** 2;
      return V[i][2] + f * (sum / wt - V[i][2]);
    });
    near.forEach((i, n) => { V[i][2] = next[n]; });
  }
}

function normals(V, F) {
  const N = V.map(() => [0, 0, 0]);
  F.forEach(f => {
    for (let t = 1; t < f.length - 1; t++) {
      const a = V[f[0]], b = V[f[t]], c = V[f[t + 1]];
      const u = [b[0] - a[0], b[1] - a[1], b[2] - a[2]], w = [c[0] - a[0], c[1] - a[1], c[2] - a[2]];
      const n = [u[1] * w[2] - u[2] * w[1], u[2] * w[0] - u[0] * w[2], u[0] * w[1] - u[1] * w[0]];
      [f[0], f[t], f[t + 1]].forEach(i => { N[i][0] += n[0]; N[i][1] += n[1]; N[i][2] += n[2]; });
    }
  });
  return N.map(n => { const l = Math.hypot(...n) || 1; return n.map(x => x / l); });
}

// The studio: a big soft key from upper left front, a fill from the right, a bright room. Radiance per direction.
const norm = v => { const l = Math.hypot(...v); return v.map(x => x / l); };
const KEY = norm([-.45, .75, .85]), FILL = norm([.8, .2, .6]), BACK = norm([0, .5, -1]);
const dot = (a, b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
const sky = d => .52 + 1.9 * Math.max(dot(d, KEY), 0) ** 6 + .45 * Math.max(dot(d, FILL), 0) ** 3 + .35 * Math.max(dot(d, BACK), 0) ** 4;

function bake(V, N, F, floorY, rays) {
  const tris = []; F.forEach(f => { for (let t = 1; t < f.length - 1; t++) tris.push(f[0], f[t], f[t + 1]); });
  const geo = new THREE.BufferGeometry();
  geo.setAttribute('position', new THREE.BufferAttribute(new Float32Array(V.flat()), 3));
  geo.setIndex(tris);
  const bvh = new MeshBVH(geo, { maxLeafTris: 8 });
  // Fibonacci hemisphere around +Y, cosine weighted, rotated to each normal with a per-vertex twist.
  const dirs = [];
  for (let i = 0; i < rays; i++) {
    const u = (i + .5) / rays, r = Math.sqrt(u), ph = 2.399963 * i;
    dirs.push([r * Math.cos(ph), Math.sqrt(1 - u), r * Math.sin(ph)]);
  }
  const ray = new THREE.Ray();
  const E = new Float32Array(V.length);
  const trace = (o, n, seed) => {
    const up = Math.abs(n[1]) < .9 ? [0, 1, 0] : [1, 0, 0];
    let t = norm([up[1] * n[2] - up[2] * n[1], up[2] * n[0] - up[0] * n[2], up[0] * n[1] - up[1] * n[0]]);
    const b = [n[1] * t[2] - n[2] * t[1], n[2] * t[0] - n[0] * t[2], n[0] * t[1] - n[1] * t[0]];
    const c = Math.cos(seed), s = Math.sin(seed); let sum = 0;
    for (const d0 of dirs) {
      const x = d0[0] * c - d0[2] * s, z = d0[0] * s + d0[2] * c;
      const d = [t[0] * x + n[0] * d0[1] + b[0] * z, t[1] * x + n[1] * d0[1] + b[1] * z, t[2] * x + n[2] * d0[1] + b[2] * z];
      ray.origin.set(o[0] + n[0] * .012, o[1] + n[1] * .012, o[2] + n[2] * .012);
      ray.direction.set(d[0], d[1], d[2]);
      const hit = bvh.raycastFirst(ray, THREE.DoubleSide);
      if (hit) { sum += .34; continue; }              // one soft bounce off the body itself
      if (d[1] < 0) { sum += (ray.origin.y - floorY) / -d[1] < 60 ? .72 : .62; continue; } // the pale floor
      sum += sky(d);
    }
    return sum / rays;
  };
  for (let i = 0; i < V.length; i++) {
    E[i] = trace(V[i], N[i], i * 1.61803);
    if (i % 50000 === 0) console.log('  baked', i, '/', V.length);
  }
  // Light through skin: a few averaging passes take the grain out and soften the terminator.
  const nb = V.map(() => new Set());
  F.forEach(f => f.forEach((a, j) => { const b = f[(j + 1) % f.length]; nb[a].add(b); nb[b].add(a); }));
  for (let pass = 0; pass < 8; pass++) {
    const nxt = new Float32Array(E.length);
    for (let i = 0; i < E.length; i++) { let s = 0; nb[i].forEach(j => s += E[j]); nxt[i] = nb[i].size ? .4 * E[i] + .6 * s / nb[i].size : E[i]; }
    E.set(nxt);
  }
  // Floor: how much of the room each floor point still sees.
  const floor = [], size = 96, half = 7, zhalf = 5;
  const floorDirs = [];
  for (let i = 0; i < 400; i++) { const u = (i + .5) / 400, r = Math.sqrt(u), ph = 2.399963 * i; floorDirs.push([r * Math.cos(ph), Math.sqrt(1 - u), r * Math.sin(ph)]); }
  for (let j = 0; j <= size; j++) for (let i = 0; i <= size; i++) {
    const x = -half + 2 * half * i / size, z = -zhalf + 2 * zhalf * j / size;
    let open = 0;
    for (const d0 of floorDirs) {
      ray.origin.set(x, floorY + .01, z); ray.direction.set(d0[0], d0[1], d0[2]);
      if (!bvh.raycastFirst(ray, THREE.DoubleSide)) open++;
    }
    floor.push(x, floorY, z, 1 - open / floorDirs.length);
  }
  const n1 = size + 1;
  for (let pass = 0; pass < 4; pass++) {
    const o = []; for (let i = 3; i < floor.length; i += 4) o.push(floor[i]);
    for (let j = 1; j < size; j++) for (let i = 1; i < size; i++) {
      const c = j * n1 + i;
      floor[c * 4 + 3] = (o[c] * 2 + o[c - 1] + o[c + 1] + o[c - n1] + o[c + n1]) / 6;
    }
  }
  return { E, floor: { size, data: floor } };
}

// Region weights per vertex (0 to 1), in the posed body. Capsules between joints, so they follow the body's shape.
const smooth = (a, b, x) => { const t = Math.min(1, Math.max(0, (x - a) / (b - a))); return t * t * (3 - 2 * t); };
function capsule(p, a, b, r, soft) {
  const ab = [b[0] - a[0], b[1] - a[1], b[2] - a[2]], ap = [p[0] - a[0], p[1] - a[1], p[2] - a[2]];
  const t = Math.min(1, Math.max(0, dot(ap, ab) / (dot(ab, ab) || 1)));
  const d = Math.hypot(ap[0] - t * ab[0], ap[1] - t * ab[1], ap[2] - t * ab[2]);
  return 1 - smooth(r, r + soft, d);
}
function regions(V, J, top, floorY) {
  const H = top - floorY, y = f => floorY + H * f;
  const both = (n, fn) => Math.max(fn(n + '.L'), fn(n + '.R'));
  const hd = J['head'].head;
  // Everything is seen from the front, so distances are measured in the picture plane.
  const flat = q => [q[0], q[1], 0];
  const cap = (p, a, b, r, soft) => capsule(flat(p), flat(a), flat(b), r, soft);
  const oval = (p, cx, fy, rx, ry, soft) => 1 - smooth(1 - soft, 1 + soft, Math.hypot((p[0] - cx) / (rx * H), (p[1] - y(fy)) / (ry * H)));
  return {
    // The scalp: above a hairline that sits higher at the forehead than at the back of the head.
    hair: p => smooth(top - H * .058, top - H * .034, p[1] + (hd[2] - p[2]) * .45) * (p[1] > J['neck03'].tail[1] ? 1 : 0),
    skin: p => oval(p, 0, .91, .04, .05, .35),
    'weight-loss': p => oval(p, 0, .6, .085, .075, .4) * armless(p, J),
    muscle: p => Math.max(
      both('upperarm01', n => cap(p, J[n].head, J['lowerarm01' + n.slice(-2)].head, H * .022, H * .02)),
      both('upperleg01', n => cap(p, [J[n].head[0] * 1.15, y(.45), 0], J['lowerleg01' + n.slice(-2)].head, H * .036, H * .022)),
      armless(p, J) * oval(p, 0, .735, .085, .05, .45),
      both('lowerleg01', n => cap(p, [J[n].head[0], J[n].head[1] - H * .04, 0], [J[n].tail[0], J[n].tail[1] + H * .05, 0], H * .018, H * .018) * .8)),
    recovery: p => Math.max(
      both('lowerleg01', n => cap(p, J[n].head, J[n].head, H * .022, H * .026)),
      both('upperarm01', n => cap(p, J[n].head, J[n].head, H * .022, H * .026))),
    libido: p => oval(p, 0, .515, .08, .055, .6) * armless(p, J),
    longevity: p => Math.max(.2, oval(p, 0, .72, .075, .075, .6) * armless(p, J)),
    // The five goals of 8 Nov 2026 (design/pages/goal.md, Pins on the body figure).
    'growth-hormone': p => cap(p, J['neck02'].head, J['neck03'].tail, H * .02, H * .018),
    sleep: p => oval(p, 0, (J['eye.L'].head[1] - floorY) / H, .05, .016, .5),
    testosterone: p => oval(p, 0, .555, .075, .04, .5) * armless(p, J),
    energy: p => armless(p, J) * oval(p, 0, .735, .085, .05, .45),
    menopause: p => oval(p, 0, .555, .075, .04, .5) * armless(p, J),
  };
}
const armless = (p, J) => (Math.abs(p[0]) < Math.abs(J['upperarm01.L'].head[0]) * 1.02 ? 1 : 0);

(async () => {
  fs.mkdirSync(WORK, { recursive: true });
  const { V: base, F, eye } = parseObj(await get('3dobjs/base.obj'));
  const skel = JSON.parse(await get('rigs/default.mhskel'));
  const weights = JSON.parse(await get('rigs/default_weights.mhw')).weights;
  const g = SEX;
  // 'neutral' is the figure on Home: about half the female and half the male shape, so it reads as neither. No breast target.
  const mix = g === 'neutral' ? [['female', .56], ['male', .44]] : [[g, 1]];
  for (const [sex, k] of mix) {
    // An even blend of the three reference populations: a clay figure should not read as one ancestry.
    for (const race of ['african', 'asian', 'caucasian']) applyTarget(base, await get(`targets/macrodetails/${race}-${sex}-young.target`), k / 3);
    applyTarget(base, await get(`targets/macrodetails/universal-${sex}-young-averagemuscle-averageweight.target`), k * .9);
    applyTarget(base, await get(`targets/macrodetails/universal-${sex}-young-averagemuscle-minweight.target`), k * .1);
    applyTarget(base, await get(`targets/macrodetails/proportions/${sex}-young-averagemuscle-averageweight-idealproportions.target`), k * .5);
  }
  if (g === 'female') applyTarget(base, await get('targets/breast/female-young-averagemuscle-averageweight-mincup-averagefirmness.target'), .25);

  const eyeL = mean(base, [...eye['joint-l-eye']]), eyeR = mean(base, [...eye['joint-r-eye']]);
  const down = g === 'female' ? .58 : (g === 'male' ? .68 : .64);  // radians, arms towards the body
  const ang = {
    'upperarm01.L': [0, 0, -down], 'upperarm01.R': [0, 0, down],
    'lowerarm01.L': [-.2, 0, 0], 'lowerarm01.R': [-.2, 0, 0],      // a slight bend at the elbow
    'upperleg01.L': [0, 0, -.06], 'upperleg01.R': [0, 0, .06],     // feet under the hips
    'foot.L': [0, 0, .06], 'foot.R': [0, 0, -.06],
    'orbicularis03.L': [LID, 0, 0], 'orbicularis03.R': [LID, 0, 0], // closed lids: calm, no stare
    'orbicularis04.L': [-LID / 3, 0, 0], 'orbicularis04.R': [-LID / 3, 0, 0],
  };
  // Relaxed hands: each finger joint curls a little towards the palm; the thumb comes in.
  for (const [side, sign] of [['L', -1], ['R', 1]]) {
    for (const fg of [2, 3, 4, 5]) for (const j of [1, 2, 3]) ang[`finger${fg}-${j}.${side}`] = [0, 0, sign * (j === 1 ? .1 : .2)];
    ang[`finger1-1.${side}`] = [-.25, 0, sign * .2]; ang[`finger1-2.${side}`] = [0, 0, sign * .2];
  }
  const { posed, joints } = pose(base, skel, weights, ang);
  const used = new Uint8Array(posed.length); F.forEach(f => f.forEach(i => { used[i] = 1; }));
  const remap = new Int32Array(posed.length).fill(-1); const V0 = [];
  posed.forEach((v, i) => { if (used[i]) { remap[i] = V0.length; V0.push(v); } });
  const F0 = F.map(f => f.map(i => remap[i]));

  const ys = V0.map(v => v[1]); const floorY = Math.min(...ys), top = Math.max(...ys);
  // Chest: iron out the nipples; pelvis: no detail at all (design book: non-sexualised).
  const CHEST = g === 'neutral' ? { r: 0, iters: 0 } : { r: .55, iters: 12 };
  const spots = [
    { at: [joints['breast.L'].tail[0], joints['breast.L'].tail[1], joints['breast.L'].tail[2]], r: CHEST.r, iters: CHEST.iters },
    { at: [joints['breast.R'].tail[0], joints['breast.R'].tail[1], joints['breast.R'].tail[2]], r: CHEST.r, iters: CHEST.iters },
    { at: [0, floorY + (top - floorY) * .49, Math.max(...V0.filter(v => Math.abs(v[0]) < .3 && Math.abs(v[1] - (floorY + (top - floorY) * .49)) < .6).map(v => v[2]))], r: 1.0, iters: g === 'female' ? 18 : 40 },
  ];
  smoothAround(V0, F0, spots);
  if (g === 'neutral') flattenChest(V0, floorY, top);

  fillEyes(V0, F0, [eyeL, eyeR]);
  // A slightly narrower head than the population blend gives; the rest of the body is untouched.
  const chinY = joints['neck03'].tail[1];
  V0.forEach(v => { if (v[1] > chinY - .5) { const t = Math.min(1, (v[1] - chinY + .5) / .9); v[0] *= 1 - .07 * t * t * (3 - 2 * t); } });
  // The lids become one calm surface.
  smoothAround(V0, F0, [{ at: [eyeL[0], eyeL[1], eyeL[2] + .1], r: .48, iters: 8 }, { at: [eyeR[0], eyeR[1], eyeR[2] + .1], r: .48, iters: 8 }]);
  let s = { V: V0, F: F0 };
  s = subdivide(s.V, s.F);
  s = subdivide(s.V, s.F);
  console.log(g, 'verts', s.V.length, 'quads', s.F.length, 'height', (top - floorY).toFixed(2));
  const N = normals(s.V, s.F);
  const rays = +(process.env.BODY_RAYS || 96);
  const { E, floor } = bake(s.V, N, s.F, floorY, rays);

  // Torso centre depth for the region capsules.
  const chestBand = s.V.filter(v => Math.abs(v[0]) < 1.5 && Math.abs(v[1] - (floorY + (top - floorY) * .65)) < 1);
  const czs = chestBand.map(v => v[2]);
  const V = s.V; V.cz = (Math.min(...czs) + Math.max(...czs)) / 2;
  const rf = regions(V, joints, top, floorY);
  const W = {};
  for (const [k, fn] of Object.entries(rf)) { W[k] = new Float32Array(V.length); V.forEach((p, i) => { W[k][i] = fn(p); }); }

  const tri = []; s.F.forEach(f => { for (let t = 1; t < f.length - 1; t++) tri.push(f[0], f[t], f[t + 1]); });
  const out = path.join(WORK, g); fs.mkdirSync(out, { recursive: true });
  fs.writeFileSync(path.join(out, 'pos.bin'), Buffer.from(new Float32Array(V.flat()).buffer));
  fs.writeFileSync(path.join(out, 'nor.bin'), Buffer.from(new Float32Array(N.flat()).buffer));
  fs.writeFileSync(path.join(out, 'irr.bin'), Buffer.from(E.buffer));
  fs.writeFileSync(path.join(out, 'idx.bin'), Buffer.from(new Uint32Array(tri).buffer));
  for (const k of Object.keys(W)) fs.writeFileSync(path.join(out, `w-${k}.bin`), Buffer.from(W[k].buffer));
  fs.writeFileSync(path.join(out, 'meta.json'), JSON.stringify({ top, floorY, cz: V.cz, floor, joints, regions: Object.keys(W) }));
  console.log('done', out);
})().catch(e => { console.error(e); process.exit(1); });
