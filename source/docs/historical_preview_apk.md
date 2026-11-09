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
- Python **3.10** compiles the seven changed `.py` modules to `.pyc`.
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
