# FFBE Global economic archive — first availability, not expiry

**Scope:** Premium Shop bundles sold for real-world money, other archived
event/exchange offers, item introduction, and unit/ability awakening.
The existing FFBE Offline project provides persistent historical access.
The calendar decides only **when each offer is introduced**.

## Historical release contract

1. Every Global event, summon banner and premium Shop offer has an
   introduction date. Before it, the offer is unavailable; from that month
   onward it stays accessible for the rest of the historical progression.
   The historical archive does **not** model live-service expiration.
2. Reuse the original FFBE Offline **event/Summons dropdowns**. Original
   offline purchase quotas and acquisition state remain active (a once-only
   bundle cannot be bought repeatedly), but no calendar-driven removal.
3. Premium bundles require an authentic Global launch date, product identity,
   original real-money amount/currency, contents, art and source. FFBE
   Offline already converts cash packs to local Lapis cost for offline use;
   do not present this conversion as the historic cash price.
4. Unverified or JP-only offers never appear automatically in historical
   mode simply because the last Global client contains them. Existing
   nonhistorical saves retain upstream behavior unchanged.
5. **Town shops are not Premium Shop:** the original town/store masters
   govern their products. Town access is a story/unlock concern, not an
   independent time gate per item. The previous Potion-only restriction
   was reverted.
6. The save currently has month resolution. A future day-level history
   position can improve **first unlock precision**, not add end dates.

## Current implementation

- source/server/historical_progression.py: approved Global paid-bundle IDs,
  authorized from their start date onward; unverified index remains closed.
- source/server/historical_summons.py: dated banners remain in subsequent
  months instead of vanishing one month after release.
- source/server/event_archive.py: existing persistent event archive and
  dropdown remain unchanged.
- source/server/ffbe_player.py: premium Shop uses the approved historical
  whitelist while retaining original offline cost/reward/purchase-limit logic.
  Local Friend Points Shop stand-in is not inserted into historical mode.
- source/server/exvius_actions_shops.py: reverted to original town-shop
  purchase validation, which uses native town/store master records.
- source/server/content/historical_commerce.json: evidence and introductions
  for real-money Shop offers. There are **no approved offers yet**, pending
  original GL evidence and a validated master-to-offer mapping.
- source/exvius/build_historical_preview_apk.py: carries the catalogue
  inside the Chaquopy ZIP for an eventual runtime build.

## Follow-up evidence work

Recover original Global Shop screenshots and notices and correlate original
bundle art, contents, original price, currency and identity with the offline
offer implementation. Once audited, approve each start date and test its
display, purchase limits and rewards in Android.

Awakening rarity/skill dates, materials, recipes and items' original
acquisition channels remain separate historical research tasks, and have not
been claimed complete by this patch.

Contextual GL milestones (not individual bundle approval):

- https://na.finalfantasy.com/topics/183 — Special Shops, August 2020
- https://na.finalfantasy.com/news/1462 — Neo Vision, August 2020
