# FFBE Global economy: shops, bundles, items and awakenings (2016–2024)

The objective is authentic **Global** availability at the selected point in
history, not a modern client with items hidden. Economic snapshots and visual
snapshots are separate, but must use the same historical date.

## Required scope and evidence

| Surface | Historical data required | Current state |
| --- | --- | --- |
| Town shops | Town and store ID, product kind/master ID, original gil price, first/last dates | First approved Mitra Potion entry; other stock unknown |
| Premium bundles | Offer ID, original art, exact start/end day, currency/price, contents, limits | Unverified local stand-ins already hidden |
| King Mog/event/exchange shops | Event window, currency, products, reset schedule and limits | Final client offers gated; archived stock not restored |
| Unit awakening | Unit source/target master IDs, each GL rarity date, gil, materials | Classical awakening blocked until each transition is audited |
| Ability awakening | Skill, unit, GL awakening release, material ranks and prices | System gate exists; per-skill records missing |
| NV/EX awakening | Form, fragments, pearls, EX level and related feature date | First Global NV release gated, item details missing |
| Items and crafting | Item/equipment/materia/recipe ID, acquisition channel and validity | Common reward gate incomplete for historic stock |
| Quests, drops, mail | Original reward set per event and date | Incomplete historical audits |

## First checked stock

The [contemporary Town of Mitra guide](https://playerassist.com/ffbe-town-of-mitra-quest-guide/)
and [Global item-shop entry](https://exvius.fandom.com/wiki/Town_of_Mitra)
both list Potion at 100 gil. Town 1101 and kind 20 / item 101000100
are linked to the original native client. The new transaction guard checks
town, item, kind, price and current period *before* charging gil.
Unlisted stock remains unavailable in historical preview until audited.
Existing nonhistorical saves remain unchanged.

- Runtime catalogue: source/server/content/historical_commerce.json
- Calendar and eligibility: source/server/historical_progression.py
- Transaction gate: source/server/exvius_actions_shops.py
- APK inclusion: source/exvius/build_historical_preview_apk.py

**Known limitation:** the current native town store may still draw stock
from the final client even when the server refuses its purchase. A later UI
adapter must project the approved catalogue into the actual shop list.

## Global source milestones

- [August 20, 2020 — Square Enix](https://na.finalfantasy.com/topics/183):
  newly introduced Special Shops include a gil awakening-material shop for
  units up to 5-star rarity. This proves the system milestone **not** each
  inventory row, permanent duration or price.
- [August 20, 2020 — Square Enix](https://na.finalfantasy.com/news/1462):
  Neo Vision and EX Awakening launched in Global. These must not be confused
  with ordinary rarity awakenings that already existed in earlier years.

A general FFBE Update Schedule may describe **JP**, not Global. Never
import a JP shop, event or awakening date without corroboration.

## Time precision and safe progression

The current save advances monthly, and the preview currently reaches July
2016. A limited-time bundle may start or expire mid-month, so monthly
progression is not precise enough to reproduce timed commerce. No limited
bundle or individual awakening recipe is approved in this catalogue yet.
A future day-level model should explicitly handle intra-month availability,
expiry and resets without changing normal upstream saves.

Before activating each historical offer: verify screenshot, Global
announcement, actual source unit/item IDs, price, currency, contents, start
and end **dates**, per-account limit, and atomic purchase/reward behavior.
Item availability also needs its **acquisition channel**, so a prize
obtainable through an event is not automatically sold everywhere.

This patch is a deliberately narrow first step, not a claim that the whole
2016–2024 economy has been reconstructed.
