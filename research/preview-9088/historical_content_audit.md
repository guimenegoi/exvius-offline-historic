# FFBE Offline Historic — audit of historical content availability

**Audited:** 2026-11-09. **Branch:** feature/historical-progression.
**Status:** baseline investigation, not approval of new playable content.

## The rule

Playable Global content requires (1) documented Global first-release date,
(2) the saved account's actual rank/story/mission/item prerequisites and
(3) correctly mapped original identities, acquisition path and cost.
Month changes never auto-award items, clear missions or increase rank.
Events, banners and paid Shop bundles have a **start date only** and
remain accessible afterward through the offline archive.

**A Japanese release date is NOT a Global release date.**
Some pages called Update Schedule combine Japanese and Global lines:
they include many 2016 items released *before* the Global launch.
Verify region for each individual event, unit, mechanic, shop and reward.
Global worldwide launch: June 30, 2016 (Square Enix).

## Current development-data coverage

| Category | Source inventory | Historical coverage gap |
| --- | --- | --- |
| Event Vortex | 757 areas; 626 with dates from 2017–2024; 131 undated | **0 dated areas in 2016**; missing original Global first missions, event art and reward master mappings |
| Community banners | 369 dated offers, 21 from 2016, earliest July 8 | No June featured-banner index; per-offer pools, rates, guarantees and item grants need native GL audit |
| Unit debut chronology | 940 editorial name/date/rarity records | Names do not uniquely identify native form IDs or summon/story/preregistration acquisition |
| Early playable unit preview | 69 base identities | Restricted launch pilot, not the full 2016–2024 rarity/awakening calendar |
| Reported launch roster | 67 unverified source rows | Rare vs friend vs story vs registration source still ambiguous |
| Real-money Premium Shop | 0 approved; **2 candidates** | Original ID, item contents/quantities, cash price and artwork not all recovered |
| Unit and ability awakenings | 0 itemized entries | Exact GL form/ability availability and material recipes not audited |
| Individual item/recipe releases | 0 itemized entries | Event, chest, town and craft acquisition rules not fully audited |
| Competitive | 2016 Colosseum/Arena feature policy | Reconstructed orb/plate layers still present in Home; separate visual cleanup needed |

The four original June 2016 Vortex enhancement chambers have a distinct
approved launch exception. Their existence does not mean that the 757
later archived events are available at launch.

**Repeatable audit** from the project root:

~~~bash
python3 - <<'PY'
import json
from pathlib import Path
r=Path('source/server')
e=json.loads((r/'event_archive.json').read_text())['events']
b=json.loads((r/'gacha_community.json').read_text())['banners']
c=json.loads((r/'content/historical_commerce.json').read_text())
assert len(e)==757 and sum(not row.get('release') for row in e)==131
assert not any(str(row.get('release') or '').startswith('2016') for row in e)
assert len(b)==369
assert sum(str(row.get('release') or '').startswith('2016') for row in b)==21
assert not c['premium_bundles'] and len(c['premium_bundle_candidates'])==2
print('Current audit baseline matched')
PY
~~~

These counts are *current deficiencies*, not target final totals.
Update the baseline consciously as verified Global records are added.

## Reproducible 2016 summon cross-index audit

Run python3 -B source/exvius/audit_historical_2016.py to generate a
machine-readable, audit-only JSON report without changing game data.
The 2026-11-09 baseline is 21 community banners and 81 featured-name
mentions, with 20 review flags:

- 19 mentions lack a matching row in the editorial debut index.
  This is an incomplete cross-reference, NOT proof of unavailability.
- One identity mismatch: November 25, 2016, authored banner 9100016,
  lists Gilgamesh, Bartz, Exdeath, Faris but has only three
  community.unit_ids (205000103, 205000403, 205000703).
  Do NOT assume positional mapping or manufacture a fourth ID.
- No 2016 featured-name mention had an explicitly later editorial debut.
  This does not validate rates, pools, rewards or acquisition paths.

The audit cross-references existing evidence, without creating a second
approval system or changing any runtime master, gacha catalogue, or
unit-release preview. Its regression test protects the known November
discrepancy until original source reconciliation.

## First-release Global events versus archived reruns

A separate research-only file,
source/server/content/historical_2016_event_candidates.json,
records **five Global events** with a verified 2016 first-release
date and **seven archived 2017 area candidates**:

| Event | First Global appearance | Archived area IDs | Archive dates |
| --- | --- | --- | --- |
| The Giant of Babel | 2016-10-14 | 705 | 2017-06-05 |
| The Crystal Tower | 2016-11-04 | 707 | 2017-05-22 |
| Grand Gaia Chronicles | 2016-11-11 | 720, 913 | 2017-06-16 |
| Trial of the Creator | 2016-11-18 | 721 | 2017-06-23 |
| The Big Bridge | 2016-11-24 | 709, 6193 | 2017-06-19 |

First-release dates: Global column of
https://finalfantasy.fandom.com/wiki/Event_(Brave_Exvius)
and Global event listings in
https://exvius.fandom.com/wiki/Category:Events .
**The archived missions may be 2017 reruns with extra difficulties or
rewards.** For example, the archive explicitly labels Giant of Babel,
Crystal Tower and Big Bridge as reruns with new missions. Do not move
these area IDs to 2016 until a native-original mission/reward comparison
proves that doing so does not give a 2016 account later rewards.
The candidate file is not imported by event_archive.py.

## Premium Cash Shop audit

**Launch offer — Early Bird Bundle:** contemporary June 30, 2016
coverage confirms **USD $3.99, once per account**, plus other
regularly purchasable packages. Historical Global source:
https://digitalchumps.com/2016/06/30/final-fantasy-brave-exvius-now-available-for-mobile/
Corroboration:
https://gamingcypher.com/final-fantasy-brave-exvius-now-available-for-mobile-devices/
Worldwide launch confirmation:
https://www.jp.square-enix.com/company/ja/news/2016/html/5c990a7dc88c8195e729344a36be5445ac9c2502.html
The original in-client ID, items/counts and sprite **remain unknown**.

**December 21, 2016 — Holiday Seasonal Bundles:** announced in the
archived Global News, but individual original price, IDs, item sets
and icons remain unverified:
https://exvius.fandom.com/wiki/News/Archives/2016_-_2021
Community reports from December also discuss a different $47.99 cash
offer; those accounts are not proof of the original authored offer ID.

**False match hazard:** the *later* authored global_bundles.json has
"Early Bird Offer" ID **990000101**, **USD $1.99**, and a 2023-dated
icon. It must NOT be equated with the original **USD $3.99** Global
"Early Bird Bundle" just because the names are similar.

Candidate records live in
source/server/content/historical_commerce.json under
premium_bundle_candidates, **without a native numeric purchase ID**.
Only explicitly approved premium_bundles enter the original Shop purchase
pipeline. The historically empty Cash Shop is **an incomplete dataset**,
not evidence that paid offers did not exist. Do not fabricate rewards to
fill the shop. Original money prices and the offline Lapis conversion
must be kept distinct. Town merchants are unrelated and retain original
story progression.

**Offer promotion requires** the original GL item ID, exact item rewards
and quantities, original cash price/currency, purchase quota, artwork,
date and source. Test denial before release or insufficient account
progress, with **no charge/grant**, and continued availability afterward.

## Colosseum vs Arena

The period distinction and account gates are valid:
launch Colosseum, original **three-orb** cap, story unlock and graded
progress; Arena later with the **five-orb** cap. Advanced Colosseum
was announced in September 2016 and still required Intermediate clear.
Global archive: https://exvius.fandom.com/wiki/News/Archives/2016_-_2021

The current source/exvius/home_carousel.js reconstructs the native
carousel and adds (1) a historical Colosseum scene route (11000),
(2) a dynamically allocated legacy orb vector, and (3) a ten-slot
background plate that is hidden for pre-Arena dates.
Those extra layout/plate overrides are no longer required by the
product decision to use the coherent *final client UI*.

**Do not revert the whole carousel.** It also owns functional navigation,
scene lifetime and period gates. Capture separate native render/layout
evidence for a June 2016 save, November 2016 Arena save and an ordinary
nonhistorical save. Then remove only the obsolete visual layers, testing
orb amount and spending, Colosseum entry/return, Arena entry/return and
no overlapping art. The account/period logic must remain.

## Content audit priorities

1. **Recover and map 2016 GL events**, with their original first-release
   dates, area/dungeon/mission IDs, banners and item rewards. Avoid dates
   imported from Japanese-specific news.
2. **Recover paid bundles from launch onward** and tie actual 2016 cash
   offers to original IDs, artwork and contents before approving purchase.
3. **Audit unit and ability awakenings per form**, not just each base unit:
   historical rarity caps, awakening materials and account acquisition
   channels can be different from debut dates.
4. **Audit story and account maturity**, including stage access, town
   stores, crafting recipes and mission-clear prerequisites.
5. **Audit every summon/reward transaction path**, including rare/friend,
   bonuses, guarantees, tickets, selection and event shops. Banners
   must not grant units the player could not historically obtain.
6. **Simplify the competitive UI layer** separately, once on-device
   native layout evidence is captured.

Every approved entry must have a GL source date, original entity and
reward IDs, account condition (if applicable), actual acquisition path,
and pre-release/pre-maturity failure-without-mutation regression tests.
Unknown data stays unresolved; it must not become available by default.
