# Typed relationship-key feature tranche — 2026-10-13

Implements required string/boolean/integer/decimal(18,4) relationship keys for
HAS_RELATED, bounded RELATED_KEYS and complete-entity relationship expansions.
Native0.45/layout0.16 matches Weft0.4.10/backend0.4.15. No new wire schema;
existing AuthoredKey.types drives exact list decoding. Pages remain string-only;
binary/timestamp and unfaceted decimal business keys remain unsupported.

Comparison/order uses typed scalar expressions; key projection keeps original
integer/decimal text and boolean JSON values. Native complete-list validation
admits strings/booleans only, not lossy JSON numbers, nulls or structures. Python
checks exact descriptor types, arity and bounds before int/Decimal/bool decoding.
Complete overflow still refuses the whole query; bounded results retain exact
bound+1 truncation behavior and relationship multiplicity.

Astra Ultra reviewed the plan and source. An initial COUNT(*)+HAS_RELATED test
found missing assessments for binding-derived key families; Mapping now retains
the exact capability set, and validation/assessment cover it identically without
weakening core checking. Original .44 manifest is byte-exact; upgrade retains
prior flat helpers and ACLs.

Installed Truss0.0.8.dev0/Weft0.4.10 wheels: both original UMF0.7/0.8 public
create/link/predicate/bounded+complete/read-only workflows and .44→.45 upgrade
passed three tests48.771 seconds. Existing string forward/inverse/bounded/read-only/
unlink workflow passed22.127 seconds. Focused two-module mypy and933-import
module boundaries pass. No broad corpus/managed-platform qualification claim.
