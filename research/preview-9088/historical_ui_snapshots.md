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

## Original signed client binaries (static evidence, 09 Nov 2026)

Three original **Global**, not Japanese, APKs were recovered from
[Appchive](https://appchive.net/apk/com.square_enix.android_googleplay.FFBEWW/ffexvius/36)
into a private local test folder (never Git). Their SHA-256 values were
verified against the archived files' identifiers. The
[Softpedia 1.4.1](https://mobile.softpedia.com/apk/final-fantasy-brave-exvius/1.4.1/)
and [Softpedia 2.0.0](https://mobile.softpedia.com/apk/final-fantasy-brave-exvius/2.0.0/)
list the **same APK hashes**, independently corroborating two of the
samples. The three APKs also share the original signing-certificate SHA-1
d3aed7cbd8f386cd56edcb749d5a2684496e52b8, matching the
Softpedia fingerprint. All ZIP entries passed integrity validation.

| Global client | HomeScene exports | GateScene exports | HomeRotateMenuList exports | Native findings |
| --- | ---: | ---: | ---: | --- |
| 1.2.0, November 2016 | 74 | 38 | 0 | HomeScene::drawCraft(int) present; no native rotating menu |
| 1.4.1, January 2017 | 74 | 38 | 0 | Same Home/Gate exported structure as 1.2 |
| 2.0.0, February 2017 | 51 | 37 | 27 | Rotating Home menu, orb controls introduced; drawCraft absent |

**Architectural implication:** the pre-2.0 Global Home and the post-2.0
Home are **different native scene implementations**. Hiding 2024 buttons
on the final client's Home cannot create the authentic 2016 layout.
The early source uses Cocos2d CCArray and CCPoint methods, whereas
the pinned final client and its Frida adapters use later types and
layouts. Native offsets and pointer ownership **cannot** be shared
blindly across these binaries. A versioned layout adapter or recovery
of original native scenes is necessary.

The APKs contain ELF libraries for x86 and ARM and tutorial CPK
resources. Some main-game art historically came from additional
downloads, so possession of the APK alone does not prove the pixels of
every live interface. The bundled common.cpk exists in 1.2 and 1.4.1
but not in 2.0. This is a packaging observation, **not** proof of a
specific layout change.

The original **1.2.0** was installed in Waydroid under its own package
com.square_enix.android_googleplay.FFBEWW, separate from
com.exvius.offline.test. It reached native startup but not a usable
game screen; broad device-storage permission was denied, and the old
online service is no longer functional. No historical runtime UI
screenshot has been authenticated from that launch. The offline app's
save and version 9085 were left unchanged.

To reproduce the static symbol/signature audit, place the three
locally obtained APKs in an external folder and run:

~~~bash
python3 -B source/exvius/audit_historical_client_apks.py \
  --directory "$HOME/.local/share/ffbe-android-test/historical-apks" \
  --keytool "$HOME/.local/share/ffbe-android-test/java/jdk/bin/keytool"
~~~

The version/hash/signature/scene summary is stored in
source/server/content/historical_ui_snapshots.json under
client_builds. **No APK bytes, client ELF or original art are tracked
or redistributed** by this change. layout_verified: false remains
explicit for every client build.

The already-recovered July 2016 French Global
[Vortex of Desires guide](https://www.supersoluce.com/soluce/final-fantasy-brave-exvius/vortex-dimensionnel)
has also been registered in the same index with a local image hash.
Its screenshot shows a continuous list, not the final client's
multi-tab Vortex. The image is a reference, not an activated renderer.

## Verified embedded original UI resources (09 Nov 2026)

Using the existing CriCodecs CPK reader on the signed client APKs,
the **Global 1.2.0 and 1.4.1 common CPKs are byte-for-byte identical**.
The 148-entry original common package contains genuine UI resources:

- image/ui/common/common.png and its plist: 119 sprites
- image/ui/header/header.png and its plist: 8 sprites
- image/ui/footer/footer.png and its plist: 14 sprites, including
  original Home, Units, Items, Shop, Summon and Friends buttons

These atlases, their original SHA-256 values and the original CPK
container hashes are indexed in the client_builds cpk_evidence field.
A private copy of the 1.2.0 atlases was extracted under the local
historical-apks/recovered-assets directory; none is tracked in Git.

The embedded tutorial resource package also matches byte-for-byte
between versions 1.2.0 and 1.4.1 (250 files). In the 2.0.0 APK,
the former common.cpk is no longer bundled, and the tutorial resource
package contains **292 files** with changed area/world layout CSVs.
This is direct evidence of file/package changes, **not proof** that
the missing early UI atlas is absent from the game's downloadable data.

An independent asset check can be run with the already-used CPK
decoder installed outside the repository:

~~~bash
PYTHONPATH="$HOME/.local/share/ffbe-android-test/historic-cpk-deps" \
  "$HOME/.local/bin/python3.10" -B \
  source/exvius/audit_historical_client_apks.py \
  --directory "$HOME/.local/share/ffbe-android-test/historical-apks" \
  --keytool "$HOME/.local/share/ffbe-android-test/java/jdk/bin/keytool" \
  --verify-cpk
~~~

The auditor validates the original APK SHA-256, signing certificate,
ELF symbols, CPK hashes, selected atlas/layout bytes and plist frame
counts. Verification is optional so the basic auditor works without
the external CriCodecs dependency.

**Development constraint:** reuse these actual atlases to restore the
pre-2.0 Home and menu components. Do not inject the older footer
sprites into the final client's Home in isolation and mark the scene
historically correct: geometry, navigation and unlocks still need
source-backed versioned reconstruction and Android validation.

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
