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

## Pre-2.0 Home shell — isolated evidence prototype (2026-11-09)

Branch: feature/historic-pre2-home-shell. The optional offline command

~~~bash
PYTHONPATH="$HOME/.local/share/ffbe-android-test/historic-cpk-deps" \
  "$HOME/.local/bin/python3.10" -B \
  source/exvius/preview_historical_home_shell.py \
  --apk "$HOME/.local/share/ffbe-android-test/historical-apks/GL-1.2.0-2016-11.apk" \
  --height 1024 \
  --output "$HOME/.local/share/ffbe-android-test/historical-apks/recovered-assets/pre2-shell-1024.png"
~~~

reads the actual 1.2.0 CPK and renders the embedded header and footer
from their **original CSV layout coordinates and original plist
sprite rectangles**, leaving the Home body transparent. Variants 640x960
and 640x1136 are supported with --height. The original atlas/container
hashes are verified against the existing client evidence inventory;
unverified clients are rejected. A companion JSON manifest records
each control and position and explicitly rejects historical fidelity.

All three 1.2.0 viewport previews were rendered. The 640x1024 preview
is byte-identical when rebuilt from the 1.4.1 APK (SHA-256
e21a584077e14b9eaefd521f63e5bf6448b570d8b600c54c23ef6916d5156ce3).

**Important localization blocker:** some text baked into the original
APK's embedded header/footer sprites is **Japanese**, whereas the
archived Global screenshot displays **English** Home, Units, Shop and
energy labels. Being included in a *signed GL APK* therefore does not
prove the image was selected at runtime. The client also ships an
en/sd/resources/resources_pretutorial.cpk with localized common/menu
resources, but **no English footer or header replacements** in that
embedded pack. The English retail images may have been delivered by
the additional content updater. The prototype is intentionally NOT
installed in the final client, and its manifest sets
global_english_localization_verified: false.

No original sprite PNG, original-layout CSV, or APK is committed. The
preview remains outside Git in the private historical-apks test folder.
The Home's central craft menu, character scene, touch targets, feature
availability, and full English localization remain **unverified**.
The final-client carousel remains a compatibility fallback until a
complete versioned adapter has passed visual and touch tests on Android.

## Conflicting signed Global 1.2/1.4 header layouts (2026-11-09)

The original CPK also contains
common_lang/sd/resources/resources_common_pretutorial.cpk.
The package is **byte-identical** in the signed GL 1.2.0 and 1.4.1
APKs, with 105 entries. Its footer CSV is identical to common.cpk,
but its header CSVs have different geometry:

- Main header_stamina_info: common = (61,79,92,19);
  pre-tutorial = (19,79,145,19).
- Main header_stamina_time: common = (156,79,70,20);
  pre-tutorial = (167,79,70,20).
- 640x1024 subheader sub_header_label: common = (130,172,226,31);
  pre-tutorial = (130,175,180,31).

The pre-tutorial stamina label even requests **145-pixel width**,
while the embedded mypage_stamina_info.png atlas frame is **92 pixels
wide**. Rendering that alternate variant with the common atlas would
therefore misrepresent the original client. The pre-tutorial original
might have used different artwork, a scaling operation, or another
runtime materialization path; none is verified. The original client
could also select headers according to its initialization state.

preview_historical_home_shell.py now validates both CPK checksums and
records row-level differences in its JSON manifest. The static preview
continues to show the common variant **only as a diagnostic** and
explicitly records header_variant_selected_by_original_client: null
and header_variant_runtime_verified: false. Neither variant is
approved for the playable historic UI yet. Do not overlay the
pre-tutorial header on the final client to "fix" its positioning.

The archived Global Home reference in the evidence catalogue is now
linked to its exact MobyGames screenshot page. The screenshot was
**added on July 12, 2016**; this is the archive entry date, not a
claim about its original capture day. The image confirms that the
retail Home displayed English UI labels, unlike several baked Japanese
labels in the embedded common CPK.

## Four original Global UI surfaces in a 2016 gameplay video

An early Global gameplay video, "Final Fantasy Brave Exvius Gameplay
Introduction" by Ushi Gaming Channel, was published on **2016-05-22**.
Source: https://www.youtube.com/watch?v=imdaYmRWe8s

A private 1280x720 H.264 copy (11 min 02 sec) has SHA-256
17754414096a28dc707edf0b4b44ab087fb7eadf20eb181508359b90d63210a2.
The actual Global client occupies the left 360x720 portion of the
recording; the right side shows the presenter. Four unretouched crops
are stored privately in data/ui-snapshots/references/video-global-2016-05-22/
with source timestamps and SHA-256 pinned by the existing JSON catalogue.
Neither video nor copyrighted frames are tracked in Git.

| Surface | Timecode | Directly observed original controls |
| --- | --- | --- |
| Home | 00:10 | Forge, Abilities, Synthesize at left; Colosseum/World/Vortex across center; six-button footer |
| Units | 00:35 | Cloud of Darkness; Equip, Trait, Magic, Special; resistance and Limit Burst detail |
| Summons | 01:20 | Galuf/Rakshasa Featured Summon; Lapis and ticket summon choices; six-button footer |
| Vortex | 04:05 | Creation, Awakening, Experience, Riches chambers in a continuous list, no five-tab control |

All four surfaces of the global-launch era now have early Global
references; previous MobyGames Home and SuperSoluce Vortex screenshots
remain independent references. This is **not** approval of a playable
historical layout. May 22 is the VIDEO UPLOAD DATE; the original
capture date remains unverified. The Galuf/Rakshasa banner and values
in the footage are not assumed to remain current for subsequent
historical months.

The video composites the native game at 360x720. It proves the visible
screen hierarchy and labels, not the original Cocos pixel coordinates.
Do not recover native layout geometry by scaling these video crops
without reconciling against original GL client resources and touch
behavior. Tests validate the timestamps, linked sources and frame hashes.

### Distinct Global UI transitions, not one worldwide layout toggle

- Pre-2017-02 Global: the older HomeScene native implementation
  with Forge/Abilities/Synthesize controls and a continuous Vortex.
- 2017-02-23 Global 2.0: new HomeRotateMenuList implementation,
  improved Summons and quest menu. The signed APK 2.0.0 symbols and
  contemporary Global release notes confirm this boundary.
- 2022-09-22 Global 7.5.0: Home Vision Card/BGM display, new Unit
  Enhance/Awaken workflow, and Shop, Friends, and Results redesign.
  https://exvius.fandom.com/wiki/Update_Schedule

Vision Card ITEMS were available starting 2020-08. The new Home
Vision Card ornament was introduced in 2022-09. The historic server
feature projection now exposes these independently; a pre-2022
historic save cannot accidentally show the final client's ornament.

The original Global end-of-service content archive offers later
resources such as Ver273_resources_common.cpk and
Ver202_resources.cpk. These have 2024-era assets and cannot be
silently substituted for the dated July 2016 resource pack references
Ver24_resources_common.cpk and Ver20_resources.cpk. The complete
English 2016 Home body atlases are still missing. Local APK-sourced
header/footer CPKs and the dated video do not solve the missing
runtime assets; source-backed reconstruction remains necessary.

Any completed UI snapshot still requires validated art, geometry,
navigation, server action gating, and Android screenshot regressions.
Until then the status remains evidence-inventory-not-a-renderer.

## Recovered three-button Home Craft layout from retained 2024 data

A read-only check of the Global end-of-service content server archive
found an obsolete CSV in the late 2024
Ver273_resources_common.cpk (2024-07-10). The archive retains
layout/home/layout_home_craft.csv although its Home was redesigned.
The CPK SHA-256 is
ae6af108e2d7597b03b7b71b7b019558f06e6049dafc074de550b75dc43fb649;
the original 757-byte CSV SHA-256 is
bc91fd7617b96c8c8cb8ae578aede73acf2c1ab990ab921d69a076195145e06e.

Its three **panel-local** rows are:

| Internal control | Referenced sprite | Cocos local rectangle |
| --- | --- | --- |
| home_btn_blacksmith | mypage_center_blacksmith1.png | (0, 0, 324, 128) |
| home_btn_ability | mypage_center_ability1.png | (0, 144, 324, 128) |
| home_btn_prepare | mypage_center_prepare1.png | (0, 288, 324, 128) |

Each also references three 40x40 timer sprites, with nine additional
relative rows. The 144-unit vertical spacing supports the visual order
in the May 22, 2016 gameplay footage
(https://www.youtube.com/watch?v=imdaYmRWe8s&t=10s),
where the old Home presents Forge, Abilities, Synthesize.
The signed GL 1.2.0 native library exports HomeScene::drawCraft(int)
and HomeScene::setCraftLayout(), confirming a dedicated old scene.

**This is a surviving layout candidate, not a verified 2016 snapshot.**
The resource is from the final 2024 archive, not the missing 2016
Ver24_resources_common.cpk. The coordinates are relative to an internal
craft panel; the screen-level panel anchor has not been verified.
The matching English button sprites are not in the signed
GL 1.2.0 common atlas or the two examined end-of-service CPK atlases.
Do not substitute late art, Japanese embedded footer labels or
unverified panel coordinates and then call the scene historically correct.

To validate the source geometry and attach it to an existing *private*
diagnostic manifest, without changing gameplay:

~~~bash
PYTHONPATH="$HOME/.local/share/ffbe-android-test/historic-cpk-deps"  "$HOME/.local/bin/python3.10" -B  source/exvius/preview_historical_home_shell.py  --apk "$HOME/.local/share/ffbe-android-test/historical-apks/GL-1.2.0-2016-11.apk"  --late-common-cpk "$HOME/.local/share/ffbe-android-test/historical-apks/late-client-reference/Ver273_resources_common.cpk"  --output "$HOME/.local/share/ffbe-android-test/historical-apks/recovered-assets/pre2-shell-with-craft-diagnostic.png"
~~~

The preview remains the original embedded header/footer, transparent
in its body. A companion JSON field legacy_craft_candidate reports
the preserved three-button layout and its unverified status.
Both original package and CSV checksums are verified.
The installed signed GL 1.2.0 client reaches a disconnected-network
initialization blocker; no executable Home layout has independently
validated the original craft-panel screen origin. The offline 9086
package and save are separate from that original installation.

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
