# FFBE Offline Historic — minimal gate on the official v0.1.30 engine

**Audit:** November 9, 2026. **Target:** Global 2016–2024.
**Branch:** feature/minimal-historical-gate-v0130.
**Current result:** clean official base + source-backed chronology.
**Playable historical APK on this branch:** NOT YET. The tested historical
9088 APK remains on feature/historical-progression.

## 1. Source version and exact official binary

- Upstream project: https://github.com/Elvlin/exvius-offline
- Official v0.1.30 tag: 621b386e007240598314b83682a501ed2f128d10
- Latest upstream main: 4ae567fc6a4e346e5378975872f43fdc0fb9775a
  (publishes update metadata and notes; no additional changes to source/).
- Official release APK: exvius-offline-v0.1.30.apk
- VersionCode: 9070; exact size: 106,360,530 bytes.
- Verified SHA-256:
  98875e7b8ebcd04794b36392f8afa71c207bebeba2f90d939ee9572f034e95e2
- Official APK was downloaded outside Git, and its SHA matched
  release/app.json. Do not commit or redistribute this binary.
- The existing playable Historic Preview 9088 was built using
  original v0.1.24 (versionCode 9064) and Python 3.10 Chaquopy overlay,
  separately signed; it is NOT based on the v0.1.30 engine.

## 2. Binary architecture change — verified

| Piece | 0.1.24 base for preview 9088 | Official 0.1.30 |
| --- | --- | --- |
| Embedded Python code | assets/chaquopy/app.imy | ABSENT |
| Python runtime native library | libpython3.10.so | ABSENT |
| Embedded Frida JavaScript | libexviustest.js.so | ABSENT |
| Native game library | lib/arm64-v8a/libgame.so | Present |
| Offline game rules | Python/Chaquopy server | Java JNI gateway into native engine |
| Bundled rules | No assets/rules namespace | 138 assets/rules entries |
| New Java DEX | No DirectRules / NativeRules DEX | Both present in classes7.dex |

The official 0.1.30 classes7.dex was inspected using JADX 1.5.6 (outside Git).
DirectRules.respond resolves local files, then dispatches the network
request into NativeRules.localRequest. The latter invokes a native
request(method, path, body, content_type) JNI method that is registered by
the app library during JNI_OnLoad. The binary also contains NativeContent,
which verifies and installs the bundled native-content archive.

**Critical:** the public source tree at the v0.1.30 tag does NOT include
the DirectRules.java or NativeRules.java engine source, or a corresponding
buildable implementation of the replacement JNI game-rule engine.
The tag points to the existing pre-migration source tree even though
the published APK has moved to a new runtime.

Therefore the old historical package() approach (replacing app.imy and
a Frida SO) cannot be applied directly to v0.1.30. Attempting an
asset-only JSON filter would NOT constitute a historical gate:
unverified direct missions, guaranteed summons, rewards and purchases
could still bypass the visual content list. No such unsafe patch
has been shipped.

## 3. Minimal implementation architecture, when source is available

Retain unmodified official UI, quests, combat, payload serialization,
game state and reward routines. The fork should own only:

1. A single documented Global release index containing approved dates,
   original IDs and original account requirements.
2. One policy module: released(content, selected_month, saved_account),
   default-deny for unknown historically restricted entities; no
   change to nonhistorical saves.
3. Narrow checks at the existing native engine boundaries:
   - visible events and banners;
   - direct battle attempt / energy and orb consumption;
   - summon rolls and guaranteed/selection/bonus awards;
   - first-clear and event rewards before grant;
   - feature availability for the saved historical period.
   Store, bundles, prices, purchases and offline currency rules are explicitly
   delegated to the unchanged original offline engine.
4. One existing-style period selector, saved atomically with progress
   and never clearing rank or completed missions.
5. Tests for denial BEFORE debit/grant, and one Android end-to-end run
   with saved progress across restart.

DO NOT port native UI overlays, historical mock Home art, visual-only
scene gates, alternate Colosseum layouts or local CSS overrides into
the new baseline. The final v0.1.30 UI should be retained, with
unavailable features hidden by its original mechanisms.

## 4. Clean-branch boundaries

This new branch starts at exact latest upstream main
4ae567fc6a4e346e5378975872f43fdc0fb9775a.
No original gameplay source file, Java class, C++ binary, Frida hook
or APK is modified.

What is deliberately NOT copied over from the old research branch:
- Original-era UI experiments and Android-specific Frida hooks;
- a hard-coded June/July 2016-only login calendar;
- a synthetic historic roster or incorrectly dated 2017 rerun missions;
- a second source-specific server for the now-native v0.1.30 engine;
- approx. 40,000 lines of mixed research and prototype data.

The historical Preview 9088 and its source are preserved as rollback
references. **After local cleanup**, there is a single active checkout at
~/Projetos/exvius-offline-historic on feature/minimal-historical-gate-v0130;
main matches official v0.1.30 and is kept as a clean upstream mirror.

The former 9088 source remains locally at
archive/historical-preview-9088 (and remotely at
origin/feature/historical-progression). Previously separate UI,
pre-2.0 Home and selector worktrees were removed: their exact commits
and both old stashes are retained under local Git refs/archive/*.
Unversioned GL master extracts, legacy imagery and 9088 Android smoke
evidence are preserved outside the source checkout in
~/.local/share/ffbe-android-test/archives/2026-11-09-fork-cleanup/.
The signed, tested 9088 APK and checksum remain in ~/Downloads/.

These archives are **not** inputs to the v0.1.30 production build.
Do not treat the clean branch as playable until a native gate exists
and passes the same Android progression tests.

## 5. Explicit blocker and next acceptance criteria

**Blocking source:** obtain the corresponding official NativeRules
JNI engine source/build instructions (or independently establish and
validate an ABI-safe, source-controlled integration point). Decompiled
DEX code is only for analysis, not a substitute for a verified native
implementation of account-aware, transactional release enforcement.

Before offering a 0.1.30-based test APK:
- Demonstrate that a June 2016 account cannot list, launch or
  receive later gated events/banner units/rewards via direct requests.
  Store and bundle behavior remains governed by Exvius Offline.
- Verify rank/story conditions and permanent unlocks after debut.
- Reconcile original 2016 mission rewards independently of 2017 reruns.
- Preserve save on upgrade and verify restart and completed battles.
- Confirm new APK signing and package/version isolation.
- Run source tests and a real Android/Waydroid battle, not only build.

See the single chronological source-of-truth research document:
CRONOLOGIA_GLOBAL_2016_2024.md.

## 6. Scope decision (November 9, 2026): upstream store is authoritative

The fork's historical filter covers **events and summon banners**, not the
offline game's cash-shop replacement. Do not reconstruct original real-money
offers, rewrite bundle prices, gate shop transactions, or apply a historical
release date to shop content. The separate historical bundle comparison in
`historical_core/audit_2016.json` is archival evidence only, never a runtime
rule. A restricted summon must still be denied at the authoritative summon
execution boundary; this does not grant permission to alter the shop.

The Python implementations under `source/server/` are retained upstream source
and are **not** the published v0.1.30 APK's JNI rules implementation.
Python-only integration would be deceptive: standalone policy tests passing
does not prove that the official APK enforces historical availability.
