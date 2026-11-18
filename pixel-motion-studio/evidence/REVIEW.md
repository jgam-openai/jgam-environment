# Browser checks and visual review

## Automated checks

Playwright exercised the final standalone viewer in Firefox 153 with networking disabled and a direct `file://` URL, plus Chromium 156 with only the loopback document request allowed. Managed Chromium policy blocks `file://`. Its interaction checks used the same built HTML served from a temporary loopback-only process. The server shut down after the run.

- 34 distinct poses within the four clips, correct 96 × 96 RGBA frames, binary alpha and exact sheet-crop matches. Manifest rectangles, per-clip durations, actual alpha bounds and stated floor contacts matched the PNGs. All visible pixels stayed within the intended action bounds.
- Idle first render, autoplay and reduced-motion pause, pause stability, four distinct canvas renders, action switching, current frame labels, seek and button and keyboard stepping. Arrow stepping exercised focused action, transport and timeline controls.
- All five rates against an instrumented timestamp clock, one-shot stop, explicit loop wrap, all three integer zooms with smoothing off, three backdrop modes and the ground guide.
- Shared time across both panes, correct secondary pose at 480 ms, final-pose hold and status at 650 and 980 ms, return to one pane.
- No console errors, failed requests or unexpected HTTP(S) requests during the desktop interaction runs. The 360 px test checked reduced motion, visible keyboard focus, and internally scrollable 4× canvases without horizontal page overflow.
- The Firefox walkthrough is a recording of the actual standalone viewer. The GIF is a separate sprite preview generated from PNGs and their authored holds, with a title beat at each action change.

Raw logs are in `test-results.txt` and `chromium-results.txt`. The optional contact-sheet caption fix affects evidence labels only. The checked bundle is rebuilt from the same source and artwork.

## Visual inspection

The builder inspected all four rows in the contact sheets, the desktop opening, the shared-clock comparison, and the 360 px opening. A fresh reviewer independently inspected the opening, comparison, mobile and all four contact sheets, and checked the source and recorded tests. That reviewer did not rerun Playwright.

- **Appearance.** The hood, orange scarf, face and bag track through the four clips. The tiny envelope is clearest at rest and blends into the cream sleeve in a few active poses.
- **Idle and run.** Idle keeps both soles fixed and returns with a small scarf displacement. Run progresses from front contact through load and pass to airborne push, using an in-place cycle. The near and far strides are distinguished by limb shading and asymmetric arm and knee positions. Holding the last run pose freezes it airborne by design, with a visible Hold label during comparison.
- **Jump and attack.** Jump reads from crouch through planted extension and apex to dust and landing. The revised apex has three native pixels of headroom. Attack has a brief strike hold, follow-through and a return to its starting lead-foot contact. No strike effects touch the canvas edge.
- **Copy and layout.** The action tabs and transport controls read on first inspection. Comparison now identifies the Shared Clock and marks the shorter pane Hold. The review also prompted focused arrow stepping, removal of a desktop background seam, clearer sheet captions and a shorter caption for Attack's follow-through. On a narrow screen, comparison stacks the stages and puts the common transport below them.

## PR verification

Run `python build.py` and `python src/draw_sprites.py` from the project directory. A temporary copy reproduced the standalone HTML and every file in `assets/` byte-for-byte. The final Firefox and Chromium runs both passed the Playwright checks above. They also verified arrow stepping on action buttons and keyboard panning of both overflowing 4× stages while the frame remains fixed.

- `python -m ruff check --no-cache build.py src/draw_sprites.py evidence/verify.py` passed with Ruff 0.17.5. `node --check src/viewer.js` passed. ESLint 9 passed with `no-undef`, `no-unused-vars` and `no-unreachable`, using the browser globals referenced in the viewer.
- Python Coverage 7.17.2 scored the two build scripts at 99% with branch measurement enabled. The runs were `python -m coverage run --branch --include=build.py build.py` and `python -m coverage run --append --branch --include=src/draw_sprites.py src/draw_sprites.py`. The report showed 222 of 222 statements executed and one partial branch out of 28.
- Chromium DevTools precise coverage during the desktop interaction suite found 7,389 of 7,867 UTF-16 source units executed in the inline viewer JavaScript (93.9%). This is a source-range measurement from one browser run.
- axe-core 4.14.0 reported zero violations on desktop and in the 360 px comparison view at 4×, using its WCAG 2.0 and 2.1 A/AA tags. It flagged color contrast over the page gradient and the icon-only step controls for manual review. The text palette's lowest contrast against the lightest page gradient color is at least 7.4:1. Both step controls have descriptive accessible names. Screen-reader testing and a full conformance review remain open.
