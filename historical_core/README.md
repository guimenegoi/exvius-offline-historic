# Historical Core — standalone prototype

This folder is intentionally independent of the Android application and the
unpublished v0.1.30 JNI rules engine. It contains **research data and a pure
availability policy**, not an APK modification or an enforced game gate.

- catalogue_2016.json: 14 original Global events from the chronology (no
  verified native IDs) and 21 community-indexed summon banners (Offline
  catalogue IDs, not proof of original Global IDs). All source-confidence
  grades and unresolved states are explicit.
- policy.py: pure fail-closed date/identity/account-precondition decisions.
  An allowed result means **historically eligible for further validation**,
  never permission to grant a unit, reward, transaction or save mutation.
- test_policy.py: standalone contract tests.

Run: python3 -m unittest discover -s historical_core -p 'test_*.py' -v

The initial banner entries are catalogue candidates, **not certified pools or
rates**. Banner 9100016 is blocked due to the unresolved featured-unit
mismatch. All 2016 events remain blocked after debut until their original
native IDs and mission/reward identity are established; 2017 reruns must not
be used as substitutes. All unlisted content is blocked. The core is not
integrated into native request paths, so **none of these restrictions is
currently enforced in-game**.

Integration prerequisites:
1. Obtain the current rules-engine source or prove a safe integration boundary.
2. Validate native IDs, original Global debut, account conditions and pools.
3. Enforce policy for event/banner listings and authoritative event-entry /
   summon-execution boundaries, before any gate-controlled debits or grants;
   keep all native account, currency, and entitlement checks.
   **Do not intercept cash-shop, bundle, price or purchase routes.**
4. Verify save compatibility, bypass resistance and actual Android gameplay.

Release changes should be evaluated, not automatically merged. A version
change alone is not evidence that the JNI API, save model or request schema
is compatible.

## Research index, 2017–2024

Run: python3 -m historical_core.build_candidates

The generated candidates_2017_2024.json includes 348 dated community banner
records and 637 Global-labelled community event occurrences. These are
**unverified candidates**, not certified first-release dates, original IDs,
reward tables, summon pools, or permissions. The community event source
includes reruns and update-log occurrences, so it cannot be used to infer
original debut or to grant access. Four malformed Global-labelled dates
(2022-06-31) are explicitly rejected and recorded for investigation.
JP-labelled/unlabelled event rows and JP/GL-mixed event_archive.json are not
promoted. The runtime policy does not load this candidate index by default,
and would deny its unverified statuses even if supplied explicitly.

## Release compatibility diagnostic

Run from the repository root:

    python3 -m historical_core.compatibility --repo . \
      --baseline upstream/main --candidate HEAD

Optionally add --apk /path/to/local.apk to inspect its SHA-256, library
names, and rule-asset inventory without copying the binary to the repo.
This is a **read-only structural report**; it does not verify native ABI,
game behavior, saves, entitlements or APK signing. A clean source diff
does not imply the published binary uses the same engine source.

## 2016 event identity and banner integrity audit

Run: python3 -m historical_core.audit_2016

The reproducible audit_2016.json compares 14 documented original Global
event names against the checked-in event_archive.json. Exact-name matching
finds eight archived area variants for six event names, **all dated after
the original 2016 debut**. The Hanging Edge (area 704, 2018-08-17) is
an additional later match beyond the previously documented 2017 reruns.
These matches do not establish equivalence of missions, waves, drops,
first-clear rewards, or native IDs. All original 2016 event identities
remain unresolved and blocked in the standalone policy.

The banner audit distinguishes early flat pools from later tiered pools.
Banner 9100016 still has four featured names but three community unit IDs;
the mismatch is recorded, not automatically repaired. The Offline Early
Bird Offer is USD 1.99 versus the independently documented original 2016
USD 3.99 offer, so it is not retroactively enabled.

This audit changes no gameplay data and provides no APK integration.

## Explicit fork boundary — shop delegated to upstream

HistoricalPolicy accepts only `event`, `banner`, and unverified research-only
`community_event` catalogue entries.
Cash shop, bundle offers, purchase prices, currencies, daily rewards, and
monetization replacements remain entirely owned by Exvius Offline v0.1.30.
The historical gate must neither hide nor rewrite store items, and it must not
alter any shop or bundle data/assets. This is a scope contract, **not** an
assertion that runtime integration has been completed.
