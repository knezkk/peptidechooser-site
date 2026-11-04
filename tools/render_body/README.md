# Body figure renders

Offline only. Makes the images in `assets/body/`; nothing in this folder ships to the page, and no 3D code runs in the browser.

**Model:** MakeHuman, `makehumancommunity/makehuman` on GitHub, `makehuman/data` (base mesh, targets and default rig), commit `a8bc2d54ff0ac92e78ff71431b1023eda42bf482`. `LICENSE.ASSETS.md` in that repository is CC0 1.0: commercial use, no attribution needed. The `.obj` header says the asset was released as CC0 in September 2020.

## What it does

1. `mesh.js <neutral|female|male>` downloads the data it needs into `BODY_WORK`, shapes an adult figure (`neutral`, the one on Home, is about half female and half male with a flattened chest; even blend of MakeHuman's three reference populations, average build), lowers the arms with the rig, closes the eyes, irons out nipples and pelvis detail, smooths the mesh twice, and bakes the studio light into each point by ray casting. It also stores a soft region weight per point for each goal.
2. `render.js` draws the baked body in headless Chromium with three.js, and writes WebP files and `manifest.json`: full body at three sizes, a close-up and a highlight per goal, pin positions.

Close-ups use the same camera as the full body, cropped with `setViewOffset`, so they line up exactly with a scaled full image.

## Run

```bash
npm i --prefix "$BODY_WORK/npm" playwright@1.49.1 three@0.170.0 three-mesh-bvh@0.8.3 sharp@0.33.5
export NODE_PATH="$BODY_WORK/npm/node_modules"
export MH_COMMIT=a8bc2d54ff0ac92e78ff71431b1023eda42bf482
BODY_RAYS=200 node tools/render_body/mesh.js neutral
BODY_RAYS=200 node tools/render_body/mesh.js female
BODY_RAYS=200 node tools/render_body/mesh.js male
node tools/render_body/render.js
python3 build.py
```

These packages are for this tool only, installed outside the repo. To change a goal's zoom, edit `VIEWS` in `render.js`; to change a goal's highlighted area, edit `regions` in `mesh.js`.
