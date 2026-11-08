# Historical Global mode — fork implementation plan

This fork remains narrowly based on Elvlin/exvius-offline. `main` tracks the upstream source; development is in `feature/historical-progression`.

## Player experience

- Start at the Global launch month (June 2016, through June 30).
- At the existing Android title screen, show one compact **Historical content** control with the current period and the next unlock. Use the existing `OfflineMenu.java` button and `AlertDialog` conventions; no extra Cocos overlays.
- Offer **Unlock next update** and **Choose later month** in the same compact dialog. Both actions require confirmation, preserve earlier content and never silently rewind.
- Store `meta.historical_month` in the existing PlayerState save; updating the APK never resets it.
- A period change must not delete the player's unlocked items, quests, or units.

## Minimal integration points (after release-index audit)

1. `player_state.expand_pool` / every guaranteed, bonus and selection-award path: filter against a **verified Global unit release index**. Do not expose a partially gated mode. Deny empty pools without spending currency.
2. `ffbe_gacha.all_banners` and the summon archive: show dated banners up to the current month; audit any permanent exceptions separately.
3. `event_archive`, `ffbe_player.serve_event_gate` and battle-entry actions: show and enforce only released events, with undated rows pending classification.
4. Other grants (shops, event rewards, tickets, units, equipment), late mechanics, and story gates require additional provenance audit before claiming historical fidelity.
5. `offline_menu` / `android_game.title_action` / `OfflineMenu.java`: small title-menu control after server-side enforcement is verified; save atomically and refresh the screen.

## Evidence/known gaps in upstream 0.1.25 (2026-11-08)

- `gacha_campaigns.json`: 78 monthly campaigns, first July 2016; launch month needs explicit coverage.
- `event_archive.json`: 757 event areas; 626 dated, **131 undated**. Never treat missing dates as launch-era.
- `gacha_community.json`: 369 dated banners. A banner's featured-unit date is evidence of *availability by that date*, not proof of the unit's earliest original Global release.
- The current `player_state.expand_pool` expands unbounded rarity tiers from the final client master catalogue. Filtering banners alone cannot prevent future units.
- Source checkout has no downloaded `data/mst_decoded` or `data/text_decoded` tables. Full integration and Android APK validation require the original client data and build tools.

## First isolated implementation

`server/historical_progression.py` contains pure month progression, strict date checks, banner selection and pool filtering helpers. These are **not connected to gameplay yet**: current release dates and guaranteed/bonus routes must be covered before activation. Unit launch metadata must be verified and explicit, not inferred from a unit ID or an undated banner. Unit tests are asset-free.

## Compatibility rule

Minimize modifications to upstream files. Prefer one central policy and narrow calls to it. Review `git diff upstream/main` when syncing, run both upstream and historical tests, and never silently default an invalid policy to the full catalogue.

## Personal Obsidian chronology investigation (2026-11-08)

Source: `FFBE Global - Cronologia de eventos e banners (2016-2024).md`, personal vault / `A00 INBOX`.
The note cites the [Global Update History](https://exvius.fandom.com/wiki/Update_Schedule)
and [FFBE Summon history](https://exvius.fandom.com/wiki/Summon). The raw personal note is
**not** copied to the public fork.

- `source/exvius/import_global_history.py` parses dated **Unidades lançadas** lines.
  `source/server/content/historical_unit_debuts.json` is the generated, source-hashed result.
- **940** distinct name/release/rarity records spanning **98** months (July 2016–August 2024).
- **Five** records have editorial restrictions (e.g. Fan Festa exclusives or delayed availability).
  These are marked `access: conditional` and cannot be assumed to be normal summons.
- **Two** repeated unit names have different debut dates (`Y'shtola`, `Aurora Fryevia`);
  resolve actual identities via the original Global master tables instead of selecting an arbitrary date.
- **Two** malformed note entries omit separators between adjacent units. The importer
  logs them under `parse_warnings`, rather than inventing IDs or release dates.
- Cross-checking all 369 community banners finds **260 reused numeric unit IDs that
  refer to different unit names** across their authored entries. A same-name/same-day
  match is only evidence, not an authoritative ID map.
- The note lists no individual launch-month units; constructing an accurate June 2016
  roster requires additional source evidence.
- The note dates the initial Global launch to June 29, 2016, as does the community
  wiki. Square Enix's official worldwide launch announcement and product press sheet
  use June 30, 2016. Month-granularity availability is unaffected.

Regenerate the evidence (without editing the vault note):

```bash
python3 source/exvius/import_global_history.py \
  --note "/path/to/FFBE Global - Cronologia de eventos e banners (2016-2024).md" \
  --community source/server/gacha_community.json \
  --output source/server/content/historical_unit_debuts.json
```

**Safety gate:** this is source evidence, **not** an active summon allowlist.
To activate historical mode, obtain original Global `F_UNIT_MST` and
`F_TEXT_UNITS_NAME` extracted tables, link names to real base-unit series and
rarity variants, verify launch availability and every summon award path, then
enforce server-side blocking. Until then the fork retains the original playable
behavior; a cosmetic filter alone would create a false guarantee.
