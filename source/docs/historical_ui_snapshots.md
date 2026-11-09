# FFBE Global — authentic historical UI snapshot inventory

This is an **evidence registry**, not an era skin, UI implementation, or an
assertion that a screenshot accurately represents every month in an era.
Goal: reconstruct real **Global** UI revisions across 2016–2024, including
Home, Summons, Vortex, units, shops, menus and their native interactions.

## Evidence-first rules

1. Every visual reference needs **region, surface, source URL, capture/release
   date or explicit unknown, local file hash, and confidence**.
2. An update announcement proves a transition, **not pixel geometry**. Do not
   use Japanese UI launch dates as Global release dates without corroboration.
3. A screenshot must be checked for aspect ratio, artwork, hierarchy, labels,
   buttons, scroll/touch hit regions, overlays and navigation. If a transition
   happened mid-month, month-only gameplay progression cannot select its
   exact UI without a finer-grained date model.
4. Unknown periods remain **unverified**. Do not silently map them to a known
   era and claim historical fidelity. The existing final-client UI may remain
   as a clearly labeled compatibility fallback during development.
5. Prefer recovered native layouts, atlases, scene definitions and original
   interaction mechanisms. A new Frida overlay is a last resort, isolated to
   the pinned client build, after comparing screenshots and runtime behavior.
6. Keep source screenshots **out of Git** unless redistribution rights are
   established. Store only URLs, checksums and authored annotations in Git.
7. Visual snapshots and content availability are separate: the existing
   `historical_progression.py` remains the authority for gameplay gates.
   Do not enable a feature because it appears in an unverified screenshot.

## Current evidence and gaps

- **Launch 2016:** one candidate Home screenshot archived by MobyGames,
  saved locally under `data/ui-snapshots/references/`; exact capture date
  unverified. Do not call the layout pixel-accurate yet.
- **Global 2.0 (February 23, 2017):** reported redesign of Home, quests and
  Summons. Individual screenshots still needed.
- **September 2022 Global UI:** contemporary community lead, not yet a
  verified set of screenshots. Requires direct captures and version evidence.
- **Final Global 9.0.0:** preserved native client and upstream Home screenshot
  provide a comparison baseline, not an original historical snapshot.
- **Other transitions, 2017–2024:** **unmapped**. The listed eras are research
  anchors, not a claim that UI was unchanged between them.

Registry: `source/server/content/historical_ui_snapshots.json`.
This inventory intentionally does **not** alter `offline_menu.status`,
`home_carousel.js`, `summon_menu.js`, or the APK.

## Acceptance gate for an era/surface

1. Obtain a dated **Global** capture, preferably a video and still images.
2. Match UI elements to recoverable native layout/atlas assets.
3. Document a screen specification and compare a Waydroid screenshot with
   the historical reference (geometry, labels, art, gestures).
4. Test render, touch, navigation, and server request/award gates.
5. Only then mark the surface verified and activate a versioned renderer.
   Different screens can transition at different times.
6. Test the previous and next historical dates, plus nonhistorical saves.
   Never replace the final client or change save data without migration tests.

## Compatibility

Upstream is the base; history data/policy and per-client UI adapters are
separate. Native offsets and the mapped GL9 resolver are pinned to a binary.
A future upstream update requires symbol/layout checks and screenshot
regressions, not automatic reuse of these offsets.

This first evidence-inventory patch deliberately does **not** ship a new APK.
