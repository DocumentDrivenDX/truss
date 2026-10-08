---
ddx:
  id: ADR-006
  type: adr
  activity: design
  status: accepted
  authoring:
    home: repo
  links:
    - id: ADR-002
      kind: informed_by
    - id: CONTRACT-001
      kind: informed_by
    - id: CONTRACT-007
      kind: informed_by
    - id: US-007
      kind: informed_by
---

# ADR-006: Exact numeric tokens in typed value carriers

## Owner decisions — 2026-10-07

Accepted numeric direction: preserve exact authored integer/decimal tokens and reject silent precision loss. The JavaScript facade uses safe number values by default where lossless, bigint for larger integers and an exact decimal carrier preserving spelling. A number supplied for a decimal is admitted only when its actual binary value is exactly representable in the selected declared decimal domain; unsafe integer numbers, out-of-domain values and rounding refuse. Explicit float domains remain separately qualified. Number-origin input cannot recover spelling already lost before admission. Reads preserve original token custody and permit number conversion only with an explicit lossless check.

Reuse UMF's existing integer/decimal/float distinctions, facets, exact literal tokens and portable key semantics. The owner reports UMF is adding decimalToken-related convenience primitives; a daily follow-up is scheduled. Pin and review their actual public API/evidence before reuse, without waiting for unspecified core changes or duplicating UMF semantics. This accepts the carrier/API direction, not the separate proposed Truss compact decimal key profile or unqualified float/record/native support.


**Status:** accepted carrier/API direction; codec/storage/Weft profile qualification remains required. **Date:** 2026-10-05.

## Exact JavaScript decimal admission algorithm

The convenience adapter must evaluate the actual IEEE-754 binary64 value, not `Number.toString()` or a JSON serialization of that value. For a finite number, obtain its sign, exponent and significand through browser-compatible bit inspection and derive the exact integer rational numerator/denominator. Do not use a decimal parser on the shortest printed representation as proof of exactness.

For an admitted decimal field with selected scale s, calculate numerator × 10^s using bounded bigint operations and require exact divisibility by denominator. The resulting integer coefficient supplies the decimal-domain candidate; no rounding is permitted. Apply the pinned UMF field validator to the exact token candidate, including precision, range, allowed values and other admitted facets. Truss's storage/native profile admission remains a separate check. Missing scale semantics or an unsupported facet refuses convenience conversion instead of guessing a domain.

Examples must name their declared domain: 12.5 fits decimal(3,1), while the actual number 0.1 does not fit decimal(3,1). This is domain-specific: a sufficiently large decimal scale/precision can represent the actual binary value of 0.1 exactly, but that value still differs from an authored decimalToken spelling `0.1`. Preserve the supplied exact token unchanged when token input is used. Number-origin input carries only the derived exact value and its number-input provenance; it cannot invent an original authored spelling.

Integer convenience uses `Number.isSafeInteger` before bigint conversion and then pinned UMF width/signedness/range/allowed-value checks. A larger integer is supplied as bigint or an admitted exact integer token. NaN/infinity, unsafe integer numbers and any failed exact-domain check refuse before native mutation or request canonicalization. Float fields do not inherit decimal convenience admission. Signed-zero/token-spelling policy and the public carrier constructor/export names remain explicit selected-profile outputs; do not silently normalize them while waiting for UMF's convenience API.

The [independent seven-example rational oracle](../../04-build/evidence/design-audit/number-decimal-domain-examples.json) checks domain representability with Python Fraction, independently of a future TypeScript adapter. Reproduce with `python3 docs/helix/04-build/evidence/design-audit/check-number-decimal-domain.py`. It does not qualify UMF facet admission, browser behavior or native storage.

Reserve finite conversion work before bigint scaling or token construction. Source token limits, scale/precision limits and intermediate-size estimates come from the selected resource/domain profile; JavaScript numeric magnitude alone cannot override those limits. Read conversion to number separately reconstructs and compares the exact binary rational to the retained exact token value. A round trip through shortest printed decimal text is insufficient; retained original token custody survives a successful convenience conversion.

## Problem

JSONB retains supported numeric value but cannot archive arbitrary authored number spelling. Host JSON numbers can also round before validation. The lexical promises of US-007 and unknown-content preservation therefore cannot be met by a raw JSONB numeric map alone. Mathematical key identity and SQL comparisons require typed numeric values, while readback must retain authored tokens.

## Proposed decision

Represent declared integer/decimal leaves as exact token strings in the catalog-directed stored value profile. A numeric property is distinguished by its pinned type definition, not by guessing string contents. Recursively encode numeric leaves in structured values, sequences and maps; preserve real strings unchanged. Native SQL lowering casts the numeric token only through a qualified exact-or-error domain path. Returning the string token preserves author spelling; key derivation uses separate mathematical canonicalization.

This proposal is a new explicit encoding profile. It does not reinterpret existing JSONB numeric leaves as strings or claim current layout data already conforms. Weft mappings must name the encoding and casts/result carriers; generic JSONB number extraction is not interchangeable. Qualify numeric domains, resource bounds and storage verification before execution.

## Presence and shape

Absent property is omitted from the property map; present JSON null remains a present null and requires declared null permission. Empty list/map remains present, not absent/null. Compound values use their pinned recursive descriptors. No embedded string tag is magic: the catalog knows which leaves are numeric. Unknown content without a descriptor cannot safely use this untagged typed encoding; preserve its exact source/value representation with a separately versioned opaque carrier rather than silently normalize it. The opaque extension format and complete nonnumeric scalar profile remain D-05 gates.

## Numeric rules and examples

Validate the exact lexical grammar and UMF family/facets before storage. No binary floating-point conversion occurs. Integer/decimal token grammar, accepted exponent/leading-zero forms and finite/nonfinite behavior follow the selected source semantics; one universal guessed JSON grammar is insufficient for every native adapter. Reject unsupported selected forms explicitly.

| Authored decimal tokens | Stored typed tokens | Mathematical key text | Consequence |
| --- | --- | --- | --- |
| 1.0 and 1.00 | "1.0" and "1.00" | 1 | Distinct lexical readback, same numeric business-key identity |
| 1e2 and 100.00, if profile accepts exponent | "1e2" and "100.00" | 100 | Numeric comparison uses value, never lexical string order |
| -0.00 | "-0.00" | 0 | Readback retains sign/scale; key identity canonicalizes zero |
| 9007199254740993 | "9007199254740993" | 9007199254740993 | No host-number precision loss |

Lexical edits with equal mathematical value are real stored-value changes when the declared lexical-preservation profile is selected; they bump version/journal according to mutation semantics. Derived business key remains equal. CONTRACT-004 now supplies the conditional stored-value/no-op handoff: mathematical equality cannot suppress an original token change. Exact source/home/codec and event/key implementation/profile adoption remain prerequisites; this authored reconciliation does not accept the ADR. SUM/comparison cannot claim arbitrary unbounded PostgreSQL numeric capacity: capability evidence names exact domain and aggregate bounds.

## Native enforcement and migration

### Candidate compact decimal equality profile

**UMF portable-key ownership:** UMF CONTRACT-040 already specifies `umf-key-tuple-v1`, including mathematical integer/fixed-scale decimal equality, exact coefficient/scale admission and rejection of null/absent/float/temporal components. Truss must consume that qualified UMF profile when selecting portable authored keys; it must not implement this proposal as a replacement universal UMF encoder. The compact tuple below is a separate candidate for a declared Truss finite-decimal storage/key profile outside that portable subset, or for internal comparison evidence where explicitly bound. It requires its own source/native/domain/migration review. At fixed scale, no rounding is permitted and authored precision/scale governs admission before normalization. A broader mathematical tuple cannot make an out-of-domain value portable.

For a selected finite base-ten decimal family, propose equality identity `(sign, coefficient, exponent)` representing `sign * coefficient * 10^exponent`. First admit the original token under its exact source grammar/facets/resource profile. Remove the decimal point to obtain digits, adjust the explicit exponent by the fractional digit count, remove leading zero digits, then remove trailing coefficient zeros while increasing the exponent by that count. All zero spellings normalize to `(zero,"0","0")`; otherwise coefficient is nonempty ASCII digits with neither leading nor trailing zero, sign is positive/negative, and exponent is canonical signed decimal text without a plus or leading-zero aliases. Keep the original stored token unchanged. Arithmetic on exponent/count metadata must be exact; no host floating-point conversion occurs.

| Admitted token | Independently expected equality tuple |
| --- | --- |
| `1.00` | `(positive,"1","0")` |
| `100.00` and `1e2` | `(positive,"1","2")` |
| `0.00120` and `1.20e-3` | `(positive,"12","-4")` |
| `-0.00` and `0e100` | `(zero,"0","0")` |
| `-12.30` | `(negative,"123","-1")` |
| `9007199254740993` | `(positive,"9007199254740993","0")` |

The compact identity does not expand exponent zeros. Its selected component encoding must be domain/family/version separated and injective inside the complete key profile; the tuple itself is not an accepted legacy `k` encoding. Mathematical ordering is a separate operation: compare sign, then exact adjusted magnitude `coefficient digit count + exponent`, then coefficient digits with conceptual right-zero padding, reversing nonzero magnitude order for negatives. Implement padding by bounded digit comparison, never allocating a string proportional to the exponent. Equality/ordering cannot use tuple-byte lexicographic order.

Qualification independently covers equal spelling variants, signed zero, differing signs, adjacent large coefficients, positive/negative exponents and resource refusal. The normalization subset requires source/native storage/domain admission first; a mathematically representable compact tuple does not establish PostgreSQL cast/aggregate support. A very large exponent is an algorithm/resource control fixture, not a supported database-domain claim. Review this profile with Weft before exporting numeric equality/order bindings; native derivation, reserved-key migration and byte encoding remain separate gates.

Sign order is negative < zero < positive. For equal nonzero signs and equal adjusted magnitude, compare digits through the longer coefficient length, treating omitted trailing digits as zero, then reverse for negatives. The [bounded independent rational design check](../../04-build/evidence/design-audit/check-decimal-design.ts) confirms nine authored tuple meanings and eight comparison outcomes by cross-multiplying integer fractions rather than implementing the proposed normalizer/comparator; [receipt](../../04-build/evidence/design-audit/decimal-design.json). Its JSON-number fixture grammar and exponent bound are oracle scope, not the selected production/source domain. Reproduce with `bun docs/helix/04-build/evidence/design-audit/check-decimal-design.ts`. Weft scoped equality/order review has been requested; no agreement is inferred while pending.

### Candidate decimal key component bytes

Propose component profile `truss-decimal-key/0.1.0`: the exact UTF-8 bytes of a four-string compact JSON array `[domain,sign,coefficient,exponent]`, with domain literally `truss-decimal-key/0.1.0`, canonical tuple grammar above and no whitespace/BOM/newline. All four strings in this profile contain only the admitted ASCII domain/sign/digit syntax, so no alternate Unicode/escape spelling is canonical. Example component text is `["truss-decimal-key/0.1.0","positive","1","2"]` for both admitted `1e2` and `100.00`; canonical zero is `["truss-decimal-key/0.1.0","zero","0","0"]`.

When used in CONTRACT-001's composite string-array encoding, this complete component text is one string component, escaped once by the composite canonical string procedure. Never splice the inner array as extra key components, use raw authored numeric text as its equality identity or accept different whitespace/escape aliases as canonical stored bytes. Full ordered key definition/encoding/source-epoch pins remain the enclosing identity context. The decimal component domain does not replace that context or make different key definitions comparable. Bind derivation and lookup/reservation locking to this exact profile; native helpers must emit/verify the same bytes on every qualified writer path.

Activating this component profile requires rebuilding and validating current keys/reservations under an explicit migration boundary while preserving original historical encodings/pins. Detect equal mathematical identities that collide under the new profile before activation; report all affected typed records rather than discarding a reservation or selecting a winner. Readonly metadata must not silently rewrite existing `k` values. This candidate is not accepted layout compatibility or a change to the historical native-cast key format. Native resource/domain/guard and migration procedure review remain required.

Catalog-aware validation is engine enforcement unless an unavoidable native profile checks token grammar/domain for all writers. JSONB string shape alone does not establish valid numeric meaning. Raw SQL changing a numeric string to invalid content must cause explicit domain refusal at execution or be prevented by qualified native guards; support reports distinguish these guarantees.

Migration reads old values exactly and records any lexical information already lost as unrecoverable; never manufacture original spelling from normalized JSONB output. New writes/profile activation require refreshed model/mapping pins, corpus and native evidence. Rollback cannot safely cast strings into numeric JSON while promising lexical preservation. Keep incompatible profiles disabled rather than reinterpret stored data.

## Alternatives and design acceptance

A separate lexical receipt alongside numeric JSONB permits convenient SQL access but doubles consistency obligations and requires every raw SQL/journal path to maintain the receipt. Exact raw JSON text per value preserves unknown tokens but changes access/index/domain strategy. Both remain explicit alternatives for review; a raw JSONB numeric-only profile cannot satisfy the full lexical requirement.

Before profile activation, publish exact recursive value schema, grammar/facets/null/resource rules, unknown opaque carrier, no-op equality and Weft extraction/decoder profile. Independent examples must cover nested numbers, real numeric-looking strings, duplicate/missing members, lexical-only edits, invalid native writes and mathematical key collisions. Real browser and PostgreSQL evidence is a build gate, not supplied by this proposal.
