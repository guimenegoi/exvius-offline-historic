# Decision: historical content maturity, current offline client UI

Status: **Accepted as product direction, 2026-11-09**.
Research branch: research/historical-ui-investigation.
Runtime development: feature/historical-progression.

## Decision

Use the stable FFBE Offline client UI as the only supported playable
interface. Hide features, controls and content that did not exist in
the selected Global month. Do not rebuild every historical native
screen or overlay sprites from different eras. The offline-only
Season/Archive selector must be unobtrusive, not masquerade as an
original Global control.

**Historical correctness means what a player can access and earn
at the account's maturity, not the exact pixel geometry of 2016.**

Availability is conjunctive:

1. **Global first-release date** no later than the saved historical
   month. Events, summon banners and real-money Shop bundles have
   only a START date. Once introduced, they remain accessible via
   the offline archive. Never simulate live-service expiry.
2. **Actual account progression** where evidenced by original rules:
   rank, cleared story missions, world switches, owned inventory,
   unlocked Colosseum grades and purchase limits. Advancing the month
   must never silently advance rank, grant units or clear missions.
3. **Verified contents and acquisition channels**: units/rarities,
   summons, awakenings, items, recipes, espers, events, paid bundles,
   and rewards require source-backed Global identities. Missing dates
   and unknown eligibility do not implicitly mean launch-era access.
   Do not invent rank limits or quests without a source.

Preserve upstream nonhistorical behavior, saves, and existing
transaction boundaries. Match visual filters with server-side action
guards: hidden controls alone are not access control.

## Evidence preserved

- Signed GL APKs 1.2.0 (Nov 2016), 1.4.1 (Jan 2017), 2.0.0
  (Feb 2017); SHA-256, signing certificates, native methods and
  extracted CPKs were verified.
- Pre-2.0 Home uses a separate native HomeScene with craft actions.
  Global 2.0 introduces HomeRotateMenuList. Later native interfaces
  are not pixel-compatible with the launch client.
- Original headers/footers, Cocos CSV layouts and partial atlases were
  recovered. Some signed-APK UI sprites contain Japanese labels;
  authentic English runtime replacements and the old central Home
  body were not fully recovered.
- Dated May 2016 Global gameplay footage establishes layouts of
  Home, Units, Summons and Vortex. Video upload/archive dates are
  not claimed as proven capture dates.
- A 2024 package preserves an older Home craft CSV candidate with
  Forge, Abilities and Synthesize controls, but its survival does
  not verify exact 2016 geometry.
- The partial pre-2.0 Home shell prototype is a diagnostic only,
  not an approved or playable historical UI.
- Vision Card items launched in Aug 2020; their Home ornament
  was added in Sep 2022 and has a distinct feature gate.
- Native early orb artwork, Season selector, multiple header
  variants and Vortex presentation were studied.

Research files: historical_ui_snapshots.md, historical_ui_audit.md,
content/historical_ui_snapshots.json, audit_historical_client_apks.py,
preview_historical_home_shell.py and corresponding tests. Original
APKs, downloaded imagery and gameplay frames are kept outside Git.
This research branch preserves the work and its limitations.
It is **not an integration branch to merge wholesale**.

## Development consequences

- Resume from feature/historical-progression, cherry-picking only
  individually reviewed fixes that support the new policy.
- Reuse historical_progression.py, existing PlayerState mission
  progress/switches, historical_summons.py, event_archive.py and
  verified indexes. No second calendar or speculative renderer.
- Prioritize Global release metadata and account maturity checks
  for summons, events, rank/story access, unit awakenings, inventory
  and recipes, paid Shop bundles, and all reward/grant paths.
- Town shops follow original town/story access; they are different
  from real-money premium offers.
- Historic month unlocks availability; original account requirements
  still govern access, costs and rewards. Advancing a period cannot
  create resources or substitute a mature player state.
- Tests must cover pre-charge/pre-grant denial without mutation,
  progression-preserving month updates, ordinary offline parity
  and Android runtime before release.
- The final client may hide premature controls but must keep coherent
  navigation, without dead space or future actions.

## Deliberate exclusions

Historical pixel-accurate UIs are **no longer a release gate**.
Do not transplant later artwork into earlier screens and call it
authentic. Do not invent dates, rewards or minimum ranks.
Do not merge research experiments into the game wholesale.

Historical UI research can continue independently if desired,
without blocking the playable content-maturity project.
