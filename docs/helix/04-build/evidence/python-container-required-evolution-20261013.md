# Flat-container requiredness tranche — 2026-10-13

SDK0.0.13/native0.50/layout0.16 pairs with Weft0.4.15/backend0.4.20. Local
planner tightening accepts unchanged flat array/map cardinality and supported
item definition; original item reference/declaration/pin, field meaning, key and
new-required-field restrictions remain. Existing locked property.required counts
include missing/null; empty containers remain present. No new value mechanism.

Astra Ultra reviewed plan/source. Both original UMF public workflows pass2
tests51.146s: missing+null counts2 for each field, public empty/nonempty repair,
acceptance/retry, exact object-row preservation, direct reads, empty SQL
projections and original receipt replay. This test proves replay availability,
not independent historical reconstruction or old-report byte equality.
Immediate .49→.50 upgrade passes1 test18.738s, retaining original facts, receipts,
feed and continued mutation with rollback/commit. Source .49 archive byte-exact;
Python933-import boundaries pass. No full corpus/managed-target claim.
