# FFBE Global Historic — experimental Android preview

**Status:** A signed installable APK was assembled from the upstream v0.1.24
offline package with an overlaid Python 3.10/Frida script bundle. This is a
**TEST-ONLY 2016-06/2016-07 vertical slice**, not a historical reconstruction
or a full v0.1.25 build. It has **not been launched on an Android device yet**.

## What is implemented

- First **Start Historic** action on the original title creates a fresh,
  backed-up local save tagged `meta.historical_month=2016-06` and
  `meta.historical_preview=true`.
- **Continue** resumes the current save. If the save is a preview in June,
  the first title button displays **Unlock Jul 2016**. Activating it advances
  cumulatively by one month, saves the change, then begins play.
- July 2016 is the *last* audited period for this narrow preview. Do not
  present August–December 2016 as playable until their sources and rates
  have been reviewed.
- 63 *provisionally* launch-era summonable base units are split into
  38 Rare/Lapis-ticket and 25 Standard/Friend Point identities, using the
  original Global IDs and a later-acquisition-category cross-check.
- Six explicit original Global unit identities debut during July:
  Kefka, Golbez, Chizuru (July 8) and Artemios, Hayate, Locke (July 22).
- Only the **initial/native rarity** is authorized, regardless of later
  awakenings. Base unit availability is assumed June 30 for the early roster:
  **this is a testing approximation, not a verified original release date**.
- Summon pools, guaranteed choices, fixed guarantees and some bonus routes
  are checked server-side before charging. Banners without trustworthy
  dates are hidden (except the evergreen Standard and Rare).
- The previous full-catalogue save is preserved as a backup when the
  title action starts a new historical preview.

## Known omissions

Events, quests, story chapters, mail, shops, tutorial grants and awakening
actions are **not yet globally date-restricted**. Current lottery rates,
season bonuses and currency availability do not recreate 2016 faithfully.
Several non-unit and advanced summons fail closed. This is an **experimental
summon and progression test**, not a completed historical game.

The preview includes content from the original FFBE client and is for
personal compatibility testing; do not upload/rehost modified client APKs
without checking the corresponding rights and permissions.

## Where to test on Mene-Notebook

Signed APK:
`~/Projetos/exvius-offline-historic/source/build/historical-preview/signed/historic-preview-aligned-debugSigned.apk`

Convenience copy:
`~/Downloads/FFBE-Global-Historic-Preview-2016-TEST.apk`

Signed with an embedded **Android debug certificate**, not the official
upstream signing key. Android will refuse to install it **over an existing
version of the same package signed with a different certificate**. Do not
uninstall an existing installation without exporting important saves. Use a
separate test device/profile if possible.

### Preserving the 14.5 GB on subsequent test builds

The updater stores unpacked packs in the app's private
`files/exvius/data/static/` folder and tracks pack id/SHA-256 in
`files/exvius/data/installed.json`. Android updates can retain both when
the **application ID and signing certificate stay identical** and the new
APK has an **increased versionCode**. Do not uninstall or clear storage.
A changed upstream pack hash can still trigger a separate data download;
reuse is not an unconditional guarantee.

The first experimental APK has the debug certificate fingerprint
`1e08a903aef9c3a721510b64ec764d01d3d094eb954161b62544ea8f187b5953`
(SHA-256). **Before providing the next APK**, compare its package name,
versionCode and certificate to the installed preview and verify data
retention on-device. Rebuilding with another temporary key without matching
the certificate will not update the installed app.

**Important:** the first preview APK was created before the fork's source
change that stops offering the *official Elvlin APK* as an update. Until a
new Android runtime build includes that fix, do not accept an in-app prompt
to replace this Historic preview with the regular upstream APK. Completing
the normal *game data* download is unaffected.

On first start the game may still download the normal offline data packages,
approximately 14.5 GB, needing about 18 GB of free space. Wi-Fi is advised.

### Manual device test

1. Install the APK on an ARM64 Android test device that does not have a
   conflicting signer installed. Grant only necessary app/file permissions.
2. Let the original offline asset download finish. On the title screen,
   tap **Start Historic**, then confirm the save is newly created.
3. Verify the native Standard (Friend Point) and Rare (Lapis) summons do not
   give characters from later years or the opposite acquisition channel.
4. Return to the title and use **Unlock Jul 2016**. Confirm the game can
   resume and the state remains July after fully closing/restarting the app.
5. Verify the July units become eligible at the monthly cutoff, but August
   and later banners/units remain blocked. If a pool is empty, it must
   refuse the purchase *before* consuming currency.
6. Report the exact screen, phone model, Android version, error/log and
   whether this was a clean installation when something fails.

**Do not treat a clean signature check as successful runtime/device testing.**

## Rebuilding this short-term preview

The full supported build process in `source/README.md` still needs the
verified FFBE Global 9.0.0 client, Java/Android SDK, Frida and apktool.
This experimental wrapper deliberately **reuses the already released v0.1.24
APK** as a bytecode/Frida host; no original APK was sourced or reconstructed.

Build components:

- `source/exvius/build_historical_preview.py` generates
  `historical_unit_releases_preview.json` and importable
  `historical_preview_data.py` from the audit-only native crosswalk.
- Python **3.10** compiles the source modules to `.pyc` (nine in the Vortex fix).
  Use exactly this version: the embedded Chaquopy importer rejects 3.12.
- `frida-compile 19.1.0 -S -c -T none` bundles
  `source/exvius/android_test.js`; the wrapper strips its progress header.
- `source/exvius/build_historical_preview_apk.py` overlays only those
  existing `.pyc` modules and the Frida bundle, plus three new modules, in
  the existing APK. This creates an **unsigned** file.
- `uber-apk-signer 1.3.0` performs zip alignment, debug signing and v2/v3
  verification. Signer and compilation dependencies are installed under the
  notebook's user cache, not committed to the repository.

All build outputs remain in gitignored `source/build/historical-preview/`.
Use the original source-controlled scripts and tests to reproduce builds;
never commit Android private signing keys or raw extracted master tables.

## June/July 2016 preview: Vortex and Panel Quest test update (9066)

APK: `~/Downloads/FFBE-Global-Historic-Preview-9066-Vortex-Fix-TEST.apk`

This patch addresses the first confirmed on-device defects:

- `event_archive.py` loads its JSON with `pkgutil.get_data` from the bundled
  Chaquopy ZIP (`app.imy`). A normal `Path(__file__)` failed on Android, so
  the original Vortex season selector could not be initialized.
- The existing eight-group season dropdown remains intact. The native
  event archive has **no audited 2016 release rows**; future/unknown events
  are hidden until they have reliable dates. Some native permanent chambers
  are still supplied by the original client, separately from that archive.
- Clash of Wills' later-game rewards are not loaded when the selected era has
  no Clash events.
- The original native function `FUNCTION_PANEL_QUEST` is disabled only while
  the saved account is tagged `historical_preview`, keeping the 2021+ rookie
  panel grid out of the 2016 opening era.

The APK changes **only** Android manifest `versionCode` from the original
`9064` to **`9066`**; its package name, underlying client and certificate
are unchanged. The v2/v3 signer certificate fingerprint matches the first
preview, SHA-256:
`1e08a903aef9c3a721510b64ec764d01d3d094eb954161b62544ea8f187b5953`.

**Install as an UPDATE over the current Historic APK. Do not uninstall it or
clear app data.** The downloaded game-data directory and existing player save
should survive this version upgrade. If Android refuses the update, STOP
instead of uninstalling; capture the error so the signature/package can be
compared with the installed APK. On-device install and Vortex appearance still
require a user test.

This test wrapper has not rebuilt the Android Java runtime: the earlier
`DataUpdates.java` fork fix for automatic *official app* update offers is not
included here. Do not accept an automatic APK replacement by the official
upstream application. Game-data downloads and repairs remain separate.

## Preview 9067 — Historical UI / action safety sweep

**Current install-test APK on Mene-Notebook:**

`~/Downloads/FFBE-Global-Historic-Preview-9067-TEST.apk`

APK SHA-256:
`757086b6039d3e3aa2b4daba50d031aa0cf2adcd7372bead718ded351c42d573`
(74,266,971 bytes / 70.83 MiB).

The install manifest has the **same package name and every byte unchanged**
from 9066 except Android `versionCode` (9066 -> **9067**). The signature
remains the previously installed debug certificate SHA-256
`1e08a903aef9c3a721510b64ec764d01d3d094eb954161b62544ea8f187b5953`;
zip alignment and signature v2/v3 were independently verified.

**UPDATE over the installed Historic APK. Do not uninstall, clear
storage or agree to install a differently signed upstream APK.**
Game assets and `installed.json` are app-private, so this update is
designed to retain all previously downloaded game data and saves. An
on-device installation and real UI test are **still required** to confirm
this, and changes to upstream pack hashes can independently download assets.

What changed relative to preview 9066:

- Source includes all post-9066 Colosseum work: original `ClsmVsCpuEntryScene`
  route before Arena, three starting orbs, five beginning November 2016,
  1 orb/hour recovery, rank-up refills, and Beginner/Intermediate/Advanced
  month gates with deferred progress promotion on the title timeline.
- 22 native `F_FUNCTION_MST` controls and all 116 dispatcher routes were
  inventoried in `source/docs/historical_gate_matrix.md`. 81 request IDs
  now have centrally resolved period gates, evaluated before handlers.
- Story Rain/Lasswell/Fina and dated candidate summon units remain
  obtainable; future/unknown unit rewards, late event emblems, Vision Cards
  and EX growth rewards are refused by the shared grant path.
- Non-period-certified premium bundles and exchange catalogues cannot
  charge historical saves; native future-world/menu functions also hide
  their entries when the preview marker is active.
- The final APK's Chaquopy runtime does **not ship PyYAML**, but old
  `ffbe_friends.py` imported it eagerly and prevented the entire Arena
  family from loading. Its optional import now safely returns an empty
  curated friends list inside the APK, preserving the normal YAML loader
  when PyYAML is installed in a source checkout. This is an **authored
  companion-list omission**, not proof that 2016 lacked friends.
- The event archive ZIP loader and original Colosseum encounter ZIP loader
  remain fixed from earlier patches.

Validation:
- 78 Python tests (63 historic, 6 import-history, 5 roster audit, 4 master-table
  Range/CRC tests) and JavaScript Home, repeat, adaptive layout and syntax tests.
- 13 Python 3.10 modules compiled into the actual APK.
- Signed `app.imy` was imported in Python 3.10. All **116 handlers** registered,
  including the 7 Arena and 4 Colosseum routes; 81 central gates evaluated;
  69 preview units and 75 Colosseum encounters loaded.
- SHA-256 of the copy in Downloads equals the signed artifact.
- No phone test, full historic UI parity, complete story/event chronology,
  Arena economy suite or 14.5 GB retention test has been claimed.

The installed download's own embedded Java APK updater is still based on
upstream **0.1.24**. The fork's later `DataUpdates.java` Java-level fix is
not present in this overlay APK. **Never accept an offer to replace the
Historic APK with a regular Elvlin update.** Game-data downloads are separate.

**First Android checks:** verify the installation upgrades in place; resume
the same campaign and inspect stored assets; check Grid Quest is absent,
Vortex season selector returns, Colosseum opens after story unlock and shows
three starting orbs, no future banners/event tiles or modern bundle offers,
and Continue/Unlock Jul preserves the save. Capture screenshots/logs for
any mismatched or nonfunctional UI, including legacy friends.

## Preview 9068 — first real-device issues in 9067

The signed test artifact is
`source/build/historical-preview/fix-v6/signed/historic-preview-9068-aligned-debugSigned.apk`
in the connected workspace (not yet installed on the phone).
It is 74,271,067 bytes / 70.83 MiB,
SHA-256 `0cc7520f1629b2827a3f71628090633c49ff0a2514afc2f3491215117f103d58`,
Android versionCode **9068** and the same certificate as 9066/9067:
SHA-256 `1e08a903aef9c3a721510b64ec764d01d3d094eb954161b62544ea8f187b5953`.
The AndroidManifest change relative to upstream APK (9064) is only
versionCode 9064 -> 9068; Android classes and resources are byte-for-byte
identical. The APK signature and ZIP alignment passed the v2/v3 checks.

- **Panel Quest still visible:** found native
  `sgHomeIconUtils::isDispPanelQuestIcon()`; its response is now false on
  historical saves in the existing UI hook, rather than relying only on
  `FunctionMstList::isValid`.
- **Daily Login blank:** the previous historical filter intentionally produced
  zero rows for an unavailable modern calendar. The June/July **28-day Global
  screenshots** are now transcribed into a preview-specific calendar, selected
  by `meta.historical_month`. Mail payout for the first day of each month
  (June 500 Gil, July 125 Lapis) is tested with duplicate-claim prevention.
  **Limitations:** source screenshots show NRG points, while this offline server
  can award NRG Restore 10 items; those converted grants and an unidentified
  June-25 icon are *provisional substitutes*, not historic exact matches.
  No invented unit/rare ticket was granted for the unidentified icon.
- **Rare/Standard multiple banners / Limited Time empty:** the banner loader
  now reads embedded JSON from Chaquopy `app.imy` if no filesystem sibling
  exists. Its historical output is fail-closed, deduplicates community aliases,
  limits limited-time offers to their attested release month (exact end days
  are not yet verified), and assigns native tabs independently of APK runtime
  environment variables: June = Standard id 1 + Rare id 9; July additionally
  has featured id 12 + id 18 in Limited Time. The account and purchase gates
  remain independent of the visual classification.
- **Vortex empty event frames:** the captured endgame response was retaining
  2024 `SpDungeonCondMst` tiles even when the event archive listed none.
  The existing gate stage now cleans the captured rows and also restricts
  saved user policy IDs to the same dated event allowlist, preventing stale
  policies from re-adding modern areas. The confirmed native Chamber of
  Experience area 226 is preserved. Advanced Chamber of the Fallen entries
  (area 899) are conservatively hidden until per-trial dates are audited.
  The modern Survival response family is cleared for 2016.
- **NV+ Awakening tooltip:** **NOT YET FIXED**. Its precise renderer and
  trigger have not been objectively identified; do not hide an arbitrary UI
  region. A screenshot and runtime trace will help localize it safely.

**Checks:** 70 historical Python tests (one skipped), plus import, unit audit
and range/CRC tests, JavaScript native Home/mission/viewport tests; signed
Android ZIP runtime imported with Python 3.10 and verified 116 action handlers,
81 feature gates, 75 Colosseum rounds, 28 login rows for each preview month,
June/July banner IDs with distinct native tab codes and saved Vortex-policy
exclusion. These are **automated tests**, not a replacement for on-device UI
validation or proof that the 14 GB cache remains after installation.

Install this APK **over** 9067; do not clear app data, uninstall or accept an
upstream APK update. A forced uninstall prompt means abort the install.

## Preview 9069 — 2016 Vortex native scene + Home status repair

**Reason:** The first on-device test of signed 9068 on Nov 9, 2026
showed still-empty NEW tiles on Vortex/Event, a native crash after tapping
Enhance, a late-client Home with Panel Quest, Anniversary and Expedition,
and non-working Daily Login. The additional 50 KB asset prompt is an
independent symptom, not proof that the 2016 calendar loaded.

**Objective causes found and addressed in source:**

1. `summon_menu.js` previously returned the whole final-client
   `GateUtil::getInSessionAreaList` when historical event area count was
   zero. It also kept a cached event menu and manipulated a scene-owned
   Cocos array when switching tabs. The historical path now uses the native
   area allowlist even if empty; it does not mutate scene-owned arrays on
   tab switches. **This reduces one identifiable crash risk, but does not
   prove why Enhance crashed on Android.**
2. `event_archive.events` had **zero** 2016 areas, despite 2016 Global
   references and native original data verifying the classic Enhancement
   chambers: Riches (216 / 21110 / 2111001), Creation
   (224 / 21102 / 2110201), Awakening (225 / 21103 / 2110391),
   Experience (226 / 21104 / 2110401). They use native Enhancement tab 2;
   later permanent missions remain restricted. The native master
   `F_MISSION_MST.ndjson` and `F_DUNGEON_MST.ndjson` were checked through
   byte-range extraction of the original `data-001` pack.
3. The historic event server stage once filtered the captured 2024
   policy only *partially* and could re-add endgame areas on later
   responses. It now uses the current saved month to build one complete
   four-area policy, ignoring unrelated persistent endgame event policies.
4. **Superseded by APK 9081 (09/11/2026).** The earlier workaround
   reused the last client's numbered spd_bn_list artwork: those files
   existed, but contained **later-era images**, not the authentic original
   chamber banners. The 2016 originals were recovered and validated against
   the stored source hashes, then encoded with the existing overlay converter
   as event_216.png, event_224.png, event_225.png and event_226.png.
   The APK now supplies them through the existing native file materializer.
   No invented art or 14 GB data redownload was needed.
5. `title_menu.js` cached the historical feature flags too early.
   `home_carousel.js` now requests the existing server
   `titleAction('status')` on Home initialize and setup. The native
   Home-icon predicates for Panel Quests, Expedition, modern events,
   Emblems, Comeback Quests and ads summon share that same feature
   projection. Original Daily Login, Quests and downloads are untouched.
6. `historical_login_preview.py` supplied a blank `banner` field,
   which removed the `DailyLoginBonusBannerResponse` despite 28 valid
   reward rows. The historical calendar now uses the **existing bundled
   daily_login_banner_dailylogin_00.png** image as a visual fallback.
   This is **not verified original June/July 2016 calendar art**.

**Automated validation:** 71 historical Python tests (1 skipped) +
15 audit/import/master-table tests; Node.js Home carousel, historical
status, native mission and adaptive layout tests; Frida compilation;
signed ZIP import with the embedded Python 3.10 runtime verified 116
handlers, 81 feature gates, exact 4 Vortex chambers + tab 2 and
original CPK artwork names in BOTH 2016-06/2016-07 replies, 28 login
days and a nonempty calendar banner. No real Android Enhance crash
test was possible from the connected workspace.

**Important pending issues:** Android native backtrace of Enhance crash;
50 KB original game asset prompt; whether the native Daily Login dialog
appears at all; late-client Anniversary visual and precise tooltip
NV+ renderer; full historical visuals / missions / event exchange.
These are NOT marked fixed without device evidence.

**For installation:** VersionCode 9069, same Android package and
signer certificate SHA-256
`1e08a903aef9c3a721510b64ec764d01d3d094eb954161b62544ea8f187b5953`.
Install **over** 9068; never uninstall or wipe the 14 GB. If Android
requests uninstall, abort. Do not accept an upstream APK replacement.

### Extra fix after signed-ZIP audit: calendar PNG CDN 404

The first 9069 candidate failed a targeted embedded-resource audit:
`assets/banner_art/daily_login_banner_dailylogin_00.png` **was**
present in `app.imy` (100,451 bytes), while
`ffbe_gacha.banner_art_index()` only walks filesystem directories.
Because Chaquopy's source path is a ZIP archive, the login CDN request
would still return **404** despite the nonempty banner response.

The existing CDN image-response branch in `capture_server.py`
now falls back, for **only that exact /login/ PNG**, to
`pkgutil.get_data(__name__, 'assets/banner_art/daily_login_banner_dailylogin_00.png')`.
The patch is included in `capture_server.pyc` of the updated APK.
This serves the same shipped atlas artwork; it does not replace
original 2016 calendar art or add a new downloader. The user's original
14 GB game data is untouched.

The original 50 KB asset download prompt shown on Home remains a
separate, unconfirmed path, and the Daily Login native scene still
needs an on-device test. If Enhance still crashes, retrieve Android
logcat/bugreport before further native changes.
