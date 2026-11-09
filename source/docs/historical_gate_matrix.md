# FFBE Global historical UI / authorization inventory — Preview 9067

**Status:** source audit and restricted test APK, not a complete restoration
of the Global launch interface. **Date:** 2026-11-08.
This document lists every one of the 22 native F_FUNCTION_MST controls and
every dispatcher request currently registered by the offline engine.

## Sources and interpretation

- [Square Enix, Global Neo Vision launch, August 20 2020](https://na.finalfantasy.com/news/1462)
  includes Vision Cards, Brave Shift and EX awakenings.
- [2016–2021 Global news archive](https://exvius.fandom.com/wiki/News/Archives/2016_-_2021)
  establishes Arena (November 2016), Advanced Colosseum (September 2016)
  and future Equipment Enhancement/other events.
- [Contemporary 2016 screenshots](https://www.mobygames.com/game/79645/final-fantasy-brave-exvius/screenshots/)
  are required to compare actual menu order, icons and layout.
- Recovered Global 9.0.0 native master `F_FUNCTION_MST.ndjson`, original
  client game ELF, `exvius_actions` and its registered family modules.
  A 2024 native flag proves only a later available control, **not** its debut.

## All 22 native capability controls

| Global final-client feature key | Policy in 2016 preview | Earliest audited month |
|---|---|---|
| `FUCNTION_CRAFTER_ITEM` | Original crafting — preserve story switch | — |
| `FUNCTION_COMEBACK_QUEST` | **Gate: comeback_quest** | No approved 2016 date |
| `FUNCTION_CRAFTER_EQUIP_ITEM` | Original crafting — preserve story switch | — |
| `FUNCTION_CRAFTER_MATERIA` | Original crafting — preserve story switch | — |
| `FUNCTION_DLC_PROMPT_ANDROID` | Download service — MUST remain operational | — |
| `FUNCTION_DLC_PROMPT_IOS` | iOS-only download service | — |
| `FUNCTION_EMBLEM_EVENT` | **Gate: emblem_event** | No approved 2016 date |
| `FUNCTION_EXPLORE` | Original exploration — preserve story switch | — |
| `FUNCTION_GOOGLE_ID` | Account platform integration — keep original | — |
| `FUNCTION_PANEL_QUEST` | **Gate: panel_quest** | No approved 2016 date |
| `FUNCTION_REEL_BEAST` | Original Espers — preserve story switch | — |
| `FUNCTION_REEL_COLOSSEUM` | Original Colosseum — routed by month | — |
| `FUNCTION_REEL_DIMENSION` | Original Vortex — date-filter archive | — |
| `FUNCTION_REEL_EXPEDITION` | **Gate: expedition** | 2017-06 |
| `FUNCTION_REEL_WORLD` | Original World — preserve story switch | — |
| `FUNCTION_REPORTS` | Achievements/reports — needs visual review | — |
| `FUNCTION_ROOM_OF_SEALED` | Disabled by original master — keep locked | — |
| `FUNCTION_SELECT_WORLD_DIVISION` | **Gate: world_season_selector** | No approved 2016 date |
| `FUNCTION_SHOP_MAGIC_KEY` | **Gate: late_shop_magic_key** | No approved 2016 date |
| `FUNCTION_SP_CLASSUP` | **Gate: modern_unit_growth** | No approved 2016 date |
| `FUNCTION_THIRDWORLD_CHANGE` | **Gate: world_season_selector** | No approved 2016 date |
| `FUNCTION_WORLD_CHANGE` | **Gate: world_season_selector** | No approved 2016 date |

The UI hook reuses the native `FunctionMstList.isValid` call. Some
functions are routed by other code (notably the custom Home carousel);
native function gates alone never guarantee their availability. Download
prompts are not blocked, to avoid interfering with required game assets.

## Server action routes

The merged dispatcher registers **116** action IDs.
**81** are assigned to a central dated/unknown feature gate;
blocked actions refuse before their handler executes or changes money/saves.
The rest (**35**) include original gameplay and
uncatalogued surfaces; they must **not** be called proof of historical
fidelity merely because their dispatcher stays functional.

| Request ID | Current handler | Status |
|---|---|---|
| `1nbWRV9w` | `friend_refuse` | Keep for launch gameplay / **content-date review pending** |
| `1oE3Fwn4` | `friend_favorite` | Keep for launch gameplay / **content-date review pending** |
| `3siZRSU4` | `friend_search` | Keep for launch gameplay / **content-date review pending** |
| `3zgbapQ7` | `clsm_end` | Keep for launch gameplay / **content-date review pending** |
| `4uCSA3ko` | `clsm_start` | Keep for launch gameplay / **content-date review pending** |
| `5g0vWZFq` | `clsm_entry` | Keep for launch gameplay / **content-date review pending** |
| `79xDN1Mw` | `craft_cancel` | Keep for launch gameplay / **content-date review pending** |
| `7kG0JAvE` | `friend_detail` | Keep for launch gameplay / **content-date review pending** |
| `7tWdn9zH` | `sacrifice` | Keep for launch gameplay / **content-date review pending** |
| `9KN5rcwj` | `gift_update` | Keep for launch gameplay / **content-date review pending** |
| `G1hQM8Dr` | `mission_update` | Keep for launch gameplay / **content-date review pending** |
| `GfI4LaU3` | `mission_restart` | Keep for launch gameplay / **content-date review pending** |
| `Gr9zxXk5` | `craft_start` | Keep for launch gameplay / **content-date review pending** |
| `LJhqu0x6` | `mission_unlock` | Keep for launch gameplay / **content-date review pending** |
| `PKDhIN34` | `craft_exe` | Keep for launch gameplay / **content-date review pending** |
| `QkN1Sp64` | `craft_add` | Keep for launch gameplay / **content-date review pending** |
| `RQ5BjDE0` | `party_update` | Keep for launch gameplay / **content-date review pending** |
| `Tvq54dx6` | `mission_switch_update` | Keep for launch gameplay / **content-date review pending** |
| `Un16HuNI` | `clsm_lottery` | Keep for launch gameplay / **content-date review pending** |
| `VTbX14dD` | `<lambda>` | Keep for launch gameplay / **content-date review pending** |
| `WIuvh09n` | `craft_end` | Keep for launch gameplay / **content-date review pending** |
| `a2d6omAy` | `friend_delete` | Keep for launch gameplay / **content-date review pending** |
| `cVRHU84e` | `<lambda>` | Keep for launch gameplay / **content-date review pending** |
| `d9Si7TYm` | `item_sell` | Keep for launch gameplay / **content-date review pending** |
| `ey8mupb4` | `update_profile` | Keep for launch gameplay / **content-date review pending** |
| `iAs67PhJ` | `friend_suggest` | Keep for launch gameplay / **content-date review pending** |
| `j0A5vQd8` | `friend_request` | Keep for launch gameplay / **content-date review pending** |
| `j5JHKq6S` | `mission_update` | Keep for launch gameplay / **content-date review pending** |
| `k5v0hMd8` | `<lambda>` | Keep for launch gameplay / **content-date review pending** |
| `kx13SLUY` | `friend_agree` | Keep for launch gameplay / **content-date review pending** |
| `nQMb2L4h` | `dungeon_liberation` | Keep for launch gameplay / **content-date review pending** |
| `otgXV79T` | `option_update` | Keep for launch gameplay / **content-date review pending** |
| `pB3st6Tg` | `unit_equip` | Keep for launch gameplay / **content-date review pending** |
| `sxK2HG6T` | `item_buy` | Keep for launch gameplay / **content-date review pending** |
| `wukWY4t2` | `trophy_reward` | Keep for launch gameplay / **content-date review pending** |

These are only `exvius_actions` action IDs. Reply transforms, battle
requests, story map/chapter content, login, mail, item shops and gacha
have **separate** pipelines. Their relevant 2016 gates have been inspected
and partially connected; do not count them as one of these endpoints.

## Coverage added for June–July 2016

1. **Unit rewards:** centralized `historical_reward_allowed` runs on
   `PlayerState._can_credit`, `_grant_items`, and `grant_unit`.
   Only dated preview units and the original Story Rain/Lasswell/Fina roots
   may be newly granted. Later Vision Cards, unit series points and
   event emblems fail closed; unmarked saves retain normal upstream rules.
   Original item/equipment/materia reward **release dates still need
   a master timeline**; a type-20 item is not automatically date-verified.
2. **Paid bundle offers:** upstream's authored offline Lapis/FP bundles are
   hidden for historical saves; purchase requests are denied without charge.
   The historical Global 2016 shop catalog is still missing, so this is a
   deliberately restricted preview, not authentic store parity.
3. **Event systems:** late mode handlers (TFA, tournament, tower, glory,
   parade, survival, RM and Equipment Enhancement) refuse in 2016 even if a
   malformed or stale UI attempts to call them.
4. **Unit/menu systems:** NV / EX awakenings / Vision Cards, unit points,
   late exchange and box-select summons, comeback & crest quests and 2024
   world-season switches are unavailable through the known action, native
   function and reward paths.
5. **2016 original systems:** World, Friends, crafting, ordinary inventory
   & equipment, Daily Quests, base Espers and Colosseum are retained; their
   actual story, rank and inventory catalogue is **not fully audited**.
6. **Persisted progression:** June/July preview retains dated 69 summonable
   candidates, Story roots and native Colosseum; gate parameters come from
   `meta.historical_month`, not client device date.

## Still not historically complete — tracked blockers

- **World/story/esper chronology:** original chapter, town, esper and
  exploration release dates must be linked to native mission IDs and checked
  at *load* and *reward* time. Story missions from later years can still be
  present on the 2024 master map.
- **Core item catalogs:** dated acquisition/reward data for Equipment,
  Materia, consumables, recipes and Esper awakenings.
- **Vortex:** reconstruct active 2016 events and the era-specific
  permanent chambers. The archive's 757 late-client areas currently have
  no approved June/July release metadata and are conservatively hidden.
  The native Vortex layout still originates from the final client.
- **Classic awakenings and ability enhancement:** 2016 unit awakening
  existed, but the preview allows only audited base rarities; the source
  and timing of all awakening chains still need checking.
- **2016 event exchange / premium bundles:** requires source-specific
  dated inventory and rate schedules. Stale 2024 offers must not appear.
- **Coherent final-client UI:** suppress unavailable features without
  dead controls or empty holes; verify Home, Units, Shop, Summons, Vortex
  and Colosseum navigation. Historical layout reconstruction is separate
  research, not a content-release blocker.
- **Per-account content eligibility:** release-date gating differs from
  real saved rank, mission progress and story unlocks. Event listings
  and paid Shop bundles now support OPTIONAL sourced account_requirements:
  minimum_rank and/or cleared_missions. Malformed entries fail closed.
  The current event index contains no verified account prerequisites;
  never invent thresholds from the final client data.

- **Upstream Java automatic APK prompts:** the fork's earlier
  `DataUpdates.java` correction is not included in the bytecode-overlay
  runtime. **Do not accept a prompt to install a non-historical upstream
  APK.** Ordinary game-data downloads stay available.

No APK is called a final historical release until those content indexes
and end-to-end Android tests are verified. Future patches must use the
same gate mechanisms rather than add per-screen overrides.
