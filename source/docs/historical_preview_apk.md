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
