// Offline only. Renders the baked body (mesh.js) in headless Chromium and writes WebP files to assets/body/.
// Usage: BODY_WORK=/some/dir node tools/render_body/render.js [--only female-clay] [--preview]
const fs = require('fs');
const path = require('path');
const http = require('http');
const { chromium } = require('playwright');
const sharp = require('sharp');

const WORK = process.env.BODY_WORK || '/tmp/pc-body';
const ROOT = path.resolve(__dirname, '../..');
const OUT = process.env.BODY_OUT || path.join(ROOT, 'assets', 'body');
const THREE_FILE = require.resolve('three').replace(/three\.cjs$/, 'three.module.js');
const arg = n => { const i = process.argv.indexOf(n); return i > 0 ? process.argv[i + 1] : null; };

// Skin looks (linear albedo; the shadow tint keeps the warm one from going grey). Figure: which body it uses.
const LOOKS = {
  clay: { albedo: [.86, .86, .87], shadow: [1, 1, 1.01] },
  warm: { albedo: [.80, .66, .57], shadow: [1.06, .94, .88] },
};
const VARIANTS = [
  { name: 'neutral-clay', body: 'neutral', look: 'clay', all: true },
];

// Where each goal's view goes: zoom (1 = whole figure) and the point of the figure at the centre of the box, as a
// fraction of the figure's height from the top. z = 1 means the whole figure stays and only the highlight comes.
const VIEWS = {
  hair: { z: 3.6, v: .125 },
  skin: { z: 1, v: .5, rim: true },
  'weight-loss': { z: 2.3, v: .405 },
  muscle: { z: 1.32, v: .4 },
  recovery: { z: 1.5, v: .42 },
  libido: { z: 1.7, v: .46 },
  longevity: { z: 1, v: .5 },
  // Two goals in one region share the figure's zoom onto it (design/pages/goal.md, Pins on the body figure).
  'growth-hormone': { z: 3.6, v: .125 },
  sleep: { z: 3.6, v: .125 },
  testosterone: { z: 1.7, v: .46 },
  energy: { z: 1, v: .5 },
  menopause: { z: 1.7, v: .46 },
};
// Pins: a point on the body per goal. World position, projected to the box by the page's own camera below.
const pinsFor = (m) => {
  const H = m.top - m.floorY, y = f => m.floorY + H * f, J = m.joints;
  return {
    hair: [0, m.top - H * .028, m.cz],
    skin: [H * .039, m.top - H * .115, m.cz + 1],
    muscle: [J['upperarm01.L'].head[0] * .5 + J['lowerarm01.L'].head[0] * .5, J['upperarm01.L'].head[1] * .5 + J['lowerarm01.L'].head[1] * .5, m.cz],
    longevity: [H * .035, y(.73), m.cz + 1],
    'weight-loss': [0, y(.61), m.cz + 1],
    libido: [0, y(.5), m.cz + 1],
    recovery: [J['lowerleg01.L'].head[0], J['lowerleg01.L'].head[1], m.cz + .5],
    'growth-hormone': [0, J['neck02'].head[1], m.cz + .5],
    sleep: [0, J['eye.L'].head[1], m.cz + 1],
    testosterone: [H * .04, y(.555), m.cz + 1],
    energy: [-H * .045, y(.735), m.cz + 1],
    menopause: [-H * .04, y(.555), m.cz + 1],
  };
};

const PAGE = `<!doctype html><canvas id=c></canvas><script type=importmap>{"imports":{"three":"/three.module.js"}}</script>
<script type=module>
import * as THREE from 'three';
const bin = async (u, T) => new T(await (await fetch(u)).arrayBuffer());
const canvas = document.getElementById('c');
const R = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true, preserveDrawingBuffer: true, premultipliedAlpha: false });
R.setClearColor(0, 0); R.outputColorSpace = THREE.LinearSRGBColorSpace;
const VS = 'attribute float irr; attribute float wgt; varying float vIrr; varying float vW; varying vec3 vN; varying vec3 vV; void main(){ vIrr=irr; vW=wgt; vN=normalize(normalMatrix*normal); vec4 mv=modelViewMatrix*vec4(position,1.); vV=normalize(-mv.xyz); gl_Position=projectionMatrix*mv; }';
const toS = 'vec3 toS(vec3 c){ return mix(12.92*c, 1.055*pow(max(c,vec3(0.)),vec3(1./2.4))-.055, step(.0031308,c)); }';
const SKIN = 'precision highp float; uniform vec3 albedo; uniform vec3 shadow; uniform float gain; varying float vIrr; varying vec3 vN; varying vec3 vV; '+toS+' void main(){ vec3 n=normalize(vN); float f=pow(1.-max(dot(n,normalize(vV)),0.),3.); float e=pow(vIrr*gain,1.5); vec3 tint=mix(shadow,vec3(1.),smoothstep(.45,1.,e)); vec3 c=albedo*tint*e; c*=1.-.22*f; c=c/(1.+max(c-vec3(.78),vec3(0.))*.9); gl_FragColor=vec4(toS(c),1.); }';
const GLOW = 'precision highp float; uniform vec3 tint; uniform float rim; uniform float wash; varying float vW; varying vec3 vN; varying vec3 vV; void main(){ vec3 n=normalize(vN); float f=1.-max(dot(n,normalize(vV)),0.); float r=pow(f,2.6); float a=max(vW*wash*(.85+.15*f), rim*r); gl_FragColor=vec4(tint,clamp(a,0.,1.)); }';
const FLOOR = 'precision highp float; attribute float occ; varying float vO; varying vec2 vP; void main(){ vO=occ; vP=position.xz; gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.); }';
const FLOORF = 'precision highp float; uniform float k; varying float vO; varying vec2 vP; void main(){ gl_FragColor=vec4(.32,.33,.36,clamp((vO-.03)*k,0.,.3)*smoothstep(4.6,2.2,length(vP))); }';
let S = {};
window.load = async (body) => {
  const b = '/work/' + body + '/';
  const [pos, nor, irr, idx] = await Promise.all([bin(b+'pos.bin',Float32Array), bin(b+'nor.bin',Float32Array), bin(b+'irr.bin',Float32Array), bin(b+'idx.bin',Uint32Array)]);
  const meta = await (await fetch(b+'meta.json')).json();
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.BufferAttribute(pos,3)); g.setAttribute('normal', new THREE.BufferAttribute(nor,3));
  g.setAttribute('irr', new THREE.BufferAttribute(irr,1)); g.setAttribute('wgt', new THREE.BufferAttribute(new Float32Array(irr.length),1));
  g.setIndex(new THREE.BufferAttribute(idx,1));
  const W = {}; for (const k of meta.regions) W[k] = await bin(b+'w-'+k+'.bin',Float32Array);
  const skin = new THREE.ShaderMaterial({ vertexShader: VS, fragmentShader: SKIN, uniforms: { albedo:{value:new THREE.Vector3()}, shadow:{value:new THREE.Vector3()}, gain:{value:1.08} } });
  const glow = new THREE.ShaderMaterial({ vertexShader: VS, fragmentShader: GLOW, blending: THREE.NoBlending, uniforms: { tint:{value:new THREE.Vector3()}, rim:{value:0}, wash:{value:1} } });
  const mesh = new THREE.Mesh(g, skin); mesh.frustumCulled = false;
  const scene = new THREE.Scene(); scene.add(mesh);
  const fs_ = meta.floor, n = fs_.size+1, fp = new Float32Array(n*n*3), fo = new Float32Array(n*n);
  for (let i=0;i<n*n;i++){ fp[i*3]=fs_.data[i*4]; fp[i*3+1]=fs_.data[i*4+1]; fp[i*3+2]=fs_.data[i*4+2]; fo[i]=fs_.data[i*4+3]; }
  const fi=[]; for(let j=0;j<n-1;j++)for(let i=0;i<n-1;i++){const a=j*n+i;fi.push(a,a+n,a+1,a+1,a+n,a+n+1);}
  const fg = new THREE.BufferGeometry(); fg.setAttribute('position',new THREE.BufferAttribute(fp,3)); fg.setAttribute('occ',new THREE.BufferAttribute(fo,1)); fg.setIndex(fi);
  const floor = new THREE.Mesh(fg,new THREE.ShaderMaterial({vertexShader:FLOOR,fragmentShader:FLOORF,transparent:true,depthWrite:false,uniforms:{k:{value:1.5}}}));
  floor.frustumCulled=false; floor.renderOrder=-1; scene.add(floor);
  // A long lens: what the box shows is a true view of the body, and a close-up lines up pixel for pixel with the whole.
  const H = meta.top-meta.floorY, frameH = H*1.05, fov = 11;
  const dist = (frameH/2)/Math.tan(fov/2*Math.PI/180);
  const cam = new THREE.PerspectiveCamera(fov, .5, dist*.3, dist*3);
  const cy = meta.floorY + H/2 - H*.005;
  cam.position.set(0, cy, meta.cz+dist); cam.lookAt(0, cy, meta.cz); cam.updateMatrixWorld();
  S = { meta, g, W, skin, glow, mesh, floor, scene, cam, H, frameH };
  return { top: meta.top, floorY: meta.floorY, cz: meta.cz, joints: meta.joints };
};
window.project = (p) => { const v = new THREE.Vector3(...p); S.cam.clearViewOffset(); S.cam.updateProjectionMatrix(); v.project(S.cam); return [(v.x+1)/2, (1-v.y)/2]; };
const shot = (w,h,view) => {
  R.setPixelRatio(1); R.setSize(w,h,false);
  if (view) { const W=1000, Hh=2000, vh=Hh/view.z, vw=W/view.z; const x=Math.min(W-vw,Math.max(0,(view.u===undefined?.5:view.u)*W-vw/2)), y=Math.min(Hh-vh,Math.max(0,view.v*Hh-vh/2)); S.cam.setViewOffset(W,Hh,x,y,vw,vh); }
  else S.cam.clearViewOffset();
  S.cam.updateProjectionMatrix(); R.clear(); R.render(S.scene,S.cam); return canvas.toDataURL('image/png').split(',')[1];
};
window.renderSkin = (look,w,h,view) => { const m=S.skin.uniforms; m.albedo.value.set(...look.albedo); m.shadow.value.set(...look.shadow); S.mesh.material=S.skin; S.floor.visible=true; return shot(w,h,view); };
window.renderGlow = (region,tint,rim,wash,w,h,view) => { const a=S.g.getAttribute('wgt'); a.array.set(S.W[region]); a.needsUpdate=true; const u=S.glow.uniforms; u.tint.value.set(...tint); u.rim.value=rim; u.wash.value=wash; S.mesh.material=S.glow; S.floor.visible=false; return shot(w,h,view); };
window.ready = true;
</script>`;

const clinic = () => {
  const t = fs.readFileSync(path.join(ROOT, 'design', 'tokens.json'), 'utf8');
  const hex = t.match(/"name":\s*"clinic",\s*"value":\s*"#([0-9a-f]{6})"/i)[1];
  return [0, 2, 4].map(i => parseInt(hex.slice(i, i + 2), 16) / 255);
};

async function write(b64, w, h, file, q, aq = 80) {
  await sharp(Buffer.from(b64, 'base64')).resize(w, h, { kernel: 'lanczos3' }).webp({ quality: q, alphaQuality: aq, effort: 6, smartSubsample: true }).toFile(file);
  return fs.statSync(file).size;
}

(async () => {
  const only = arg('--only'); const preview = process.argv.includes('--preview');
  const srv = http.createServer((q, r) => {
    const u = q.url.split('?')[0];
    if (u === '/') { r.setHeader('content-type', 'text/html'); return r.end(PAGE); }
    if (u === '/three.module.js' || u === '/three.core.js') { r.setHeader('content-type', 'text/javascript'); return r.end(fs.readFileSync(path.join(path.dirname(THREE_FILE), u.slice(1)))); }
    if (u.startsWith('/work/')) { const f = path.join(WORK, u.slice(6)); if (fs.existsSync(f)) return r.end(fs.readFileSync(f)); }
    r.statusCode = 404; r.end();
  }).listen(0);
  const port = srv.address().port;
  const br = await chromium.launch({ args: ['--use-angle=swiftshader', '--use-gl=angle', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
  const page = await br.newPage();
  page.on('console', m => { if (m.type() === 'error') console.log('page:', m.text()); });
  page.on('pageerror', e => console.log('pageerror:', e.message));
  await page.goto(`http://127.0.0.1:${port}/`); await page.waitForFunction('window.ready===true');

  const tint = clinic();
  const SS = 2;                 // supersampling for clean edges
  const FULL = [[540, 1080], [372, 744], [190, 380]];
  const CLOSE = [540, 1080];
  const sizes = {};
  const manifest = { source: 'MakeHuman (CC0 1.0), makehumancommunity/makehuman, makehuman/data', box: '1:2', views: VIEWS, pins: {}, variants: {} };
  fs.mkdirSync(OUT, { recursive: true });
  for (const v of VARIANTS) {
    if (only && v.name !== only) continue;
    const m = await page.evaluate(b => window.load(b), v.body);
    const dir = path.join(OUT, v.name); fs.mkdirSync(dir, { recursive: true });
    const pins = {};
    for (const [k, p] of Object.entries(pinsFor(m))) { const uv = await page.evaluate(x => window.project(x), p); pins[k] = uv.map(x => +x.toFixed(4)); }
    manifest.variants[v.name] = { pins };
    const b64 = await page.evaluate(([l, w, h]) => window.renderSkin(l, w, h, null), [LOOKS[v.look], FULL[0][0] * SS, FULL[0][1] * SS]);
    for (const [w, h] of FULL) sizes[`${v.name}/full-${h}.webp`] = await write(b64, w, h, path.join(dir, `full-${h}.webp`), 82);
    if (process.env.BODY_DEBUG) {
      const list = JSON.parse(process.env.BODY_DEBUG);
      for (let i = 0; i < list.length; i++) {
        const c = await page.evaluate(([l, w, h, vw]) => window.renderSkin(l, w, h, vw), [LOOKS[v.look], 800, 1600, list[i]]);
        await sharp(Buffer.from(c, 'base64')).flatten({ background: '#fff' }).resize(400, 800).png().toFile(path.join(OUT, `debug-${v.name}-${i}.png`));
      }
      continue;
    }
    if (preview) continue;
    for (const [k, view] of Object.entries(VIEWS)) {
      if (view.z > 1) {
        const c = await page.evaluate(([l, w, h, vw]) => window.renderSkin(l, w, h, vw), [LOOKS[v.look], CLOSE[0] * SS, CLOSE[1] * SS, view]);
        sizes[`${v.name}/${k}.webp`] = await write(c, CLOSE[0], CLOSE[1], path.join(dir, `${k}.webp`), 78);
      }
      const g = await page.evaluate(([r, t, rim, wash, w, h, vw]) => window.renderGlow(r, t, rim, wash, w, h, vw),
        [k, tint, view.rim ? .78 : 0, k === 'skin' ? .34 : (k === 'longevity' ? .62 : (k === 'libido' ? .36 : .6)), CLOSE[0] * SS, CLOSE[1] * SS, view.z > 1 ? view : null]);
      // A soft glow holds at a lower size; the skin's rim needs the full one.
      const [gw, gh] = view.rim ? CLOSE : [405, 810];
      sizes[`${v.name}/${k}-glow.webp`] = await write(g, gw, gh, path.join(dir, `${k}-glow.webp`), 40, 92);
    }
  }
  manifest.sizes = sizes;
  const mf = path.join(OUT, 'manifest.json');
  if (only && fs.existsSync(mf)) { const old = JSON.parse(fs.readFileSync(mf)); manifest.variants = { ...old.variants, ...manifest.variants }; manifest.sizes = { ...old.sizes, ...sizes }; }
  fs.writeFileSync(mf, JSON.stringify(manifest, null, 1));
  await br.close(); srv.close();
  const tot = Object.values(sizes).reduce((a, b) => a + b, 0);
  console.log('files', Object.keys(sizes).length, 'KB', Math.round(tot / 1024));
})().catch(e => { console.error(e); process.exit(1); });
