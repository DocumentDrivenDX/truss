# Exact scalar container query tranche — 2026-10-13

The next feature release adds projection-only flat scalar arrays/maps and complete
entities through existing Weft Value descriptor transport0.2.4. Original UMF
Sequence/Map item identities are admitted by exact dependency closure with
required singular scalar availability; item-only Fields receive no native
property IDs. No nested values, unnesting or container comparisons are claimed.

Weft backend0.4.14 / wheel0.4.9 selects native0.44-candidate. Prior .4.13/.43
and all earlier pairs retain their original behavior. Arrays use explicit
ordinality; empty aggregates yield []/{}; numeric items remain exact JSON strings
until Python int/Decimal decoding. Optional outer presence envelopes distinguish
absent/null/empty. Returned tuples and sorted immutable string-key mappings use
existing QueryRows; timestamps/binary keep exact TextValue carriers.

Native query_objects validates the complete actual source before caller
predicates, using the same property/item definitions and exact value validation
as direct reads. Native query_scope requires current property/item interpretation
authority before and after buffering. Native numeric-domain checks are reserved
for singular comparable fields, not exact numeric item transport. Existing
logical scan/output byte and row limits remain. No new protocol schema.

Astra Ultra reviewed the plan and source. Corrected capability advertisement in
the manifest (not merely additions), explicit item dependency coverage and the
native manifest version. The original .43 archive is retained byte-exact for
upgrade and all seven prior flat-value helper identities/ACLs are captured.
Initial basic original UMF0.7/0.8 projections passed two tests36.469 seconds.
Final installed-wheel presence/upgrade/scalar regressions are recorded below.

Final installed Truss0.0.7.dev0/Weft0.4.9 wheels: five tests passed55.932 seconds,
including exact arrays/maps, complete entity projection, absent/null/empty,
.43→.44 additive upgrade and scalar numeric queries. Module boundaries passed933
imports; focused query mypy passes with optional compiler/driver imports ignored.
