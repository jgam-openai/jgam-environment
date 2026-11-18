# Lark · Pixel Motion Studio

Open **index.html** directly in a browser. The page embeds its sprite sheets, CSS and JavaScript. It works from disk with networking disabled.

Choose Idle, Run, Jump or Attack. Use the transport buttons or drag the timeline. Space toggles playback outside controls that use Space for activation. Left and Right step poses, including when an action button or timeline has focus. When reduced motion is enabled, the viewer opens paused. At 4× on narrow screens, focus a stage and use Left and Right to scroll its canvas.

Compare adds a second action to the same elapsed-time clock. The shorter action displays **Hold** at its final pose until the longer action ends or the clock wraps. Single-pane Idle and Run default to Loop. Jump and Attack default to one pass.

| Clip | Poses | Duration | Default |
| --- | ---: | ---: | --- |
| Idle | 6 | 960 ms | Loop |
| Run | 8 | 640 ms | Loop |
| Jump | 11 | 1,360 ms | One pass |
| Attack | 9 | 1,200 ms | One pass |

Each PNG frame is 96 × 96 with hard alpha edges. The ground anchor is (44, 78). Timing uses 80 ms ticks and explicit per-pose holds.

## Edit or rebuild

- Edit `src/template.html`, `src/studio.css` and `src/viewer.js` for the viewer.
- Edit poses, palette or holds in `src/draw_sprites.py`. Run `python src/draw_sprites.py` with Pillow 13 to redraw the sheets, 34 frame PNGs, contact sheets, GIF and manifest. The renderer uses native-pixel polygons and lines, with independently authored joint, scarf and effect poses.
- Run `python build.py` with Python 3 to update the self-contained HTML. You can also edit `assets/manifest.json` or replace the sheet PNGs directly before bundling. Keep the sheet rectangles, frame PNGs, bounds and contact metadata in sync.
- To reproduce the disk checks, install Playwright and run `python -m playwright install firefox ffmpeg`, then `python evidence/verify.py`. For a Chromium cross-check, serve this directory on loopback and set `STUDIO_TEST_URL` to its full `http://127.0.0.1:PORT/index.html` address. See the [verification report](evidence/REVIEW.md) for results and review notes.

The design began with an OpenAI image-generation concept made for this project. The animation pixels were redrawn as native-resolution pose art in Pillow using that concept for costume, palette and facing. No art was taken from the reference viewer.

The generated concept is displayed in the build chat. The editable pose drawings and exported animation art are included in this bundle. The original concept PNG could not be transferred to the cloud checkout.
