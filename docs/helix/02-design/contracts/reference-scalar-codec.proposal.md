# Account/Item scalar codec proposal

This proposes exact lexical admission for the [four-field row-home reference](reference-row-home-binding.proposal.md), under CONTRACT-010 and ADR-006. It is not a universal UMF or native-adapter grammar. Original field definitions, source bytes and actual native profiles remain independently required. Registry identities and native bindings are not allocated by this document.

## String payload

For Account.code, Item.code and present-string Item.note, preserve the exact sequence of Unicode scalar values in `text_value` and retain the original source artifact bytes separately. Reject unpaired surrogates before UTF-8 encoding. PostgreSQL text cannot represent NUL: refuse that native realization explicitly rather than removing the character or altering the UMF field. Empty text is valid. No normalization, trimming, case folding or JSON escape spelling becomes business identity. Original serialized source spelling and decoded string meaning are separate observations.

Select the string dispatch only after complete original Field/home/codec coupling and ownership admission. All other scalar payload slots must be SQL NULL. Required code fields refuse absent/null; Item.note follows its separately admitted absence/null/root rules. A string payload with SQL NULL is malformed, not logical null.

## Decimal token

For required Item.amount, propose the complete ASCII token grammar `-?(0|[1-9][0-9]*)(\.[0-9]+)?([eE][+-]?[0-9]+)?`, anchored to the entire token with no whitespace, BOM or trailing newline. The grammar permits negative zero, trailing fractional zeros and exponent spelling; it excludes plus-prefixed mantissas, leading-zero integers, nonfinite names and incomplete fractions/exponents. This selects a reference lexical subset; unsupported source forms must be reported explicitly and retained when applicable, never silently rewritten into this grammar.

Retain the exact admitted token in `numeric_token`. Derive its finite mathematical value using bounded exact sign/mantissa/exponent interpretation, then apply the [decimal(21,3) domain](reference-amount-domain-binding.proposal.md): scaled coefficient integral and absolute coefficient below 10^21. Apply admission before native conversion. Do not allocate exponent-sized zero padding. Decimal lexical admission grants no equality/order/key/SUM operation by itself.

Independently compare finite `numeric_value` with the exact admitted token value under ADR-006's selected exact comparison procedure. Native representation may lose spelling or zero sign; that projection is never the token-preserving read source. Every other scalar slot is SQL NULL. Required amount refuses absent/null, missing token/projection, NaN/infinity, rounding or disagreement. Native cast success cannot substitute for grammar or domain admission.

| Independent token | Expected reference lexical/domain result |
| --- | --- |
| `9007199254740993.000`, `0.00`, `-0.01` | Admit the original M03 tokens exactly. |
| `1e2`, `100.00`, `1.2300`, `-0.000` | Admit; preserve spelling, exponent and zero sign separately from mathematical equality. |
| `+1`, `01`, `.1`, `1.`, `NaN`, `Infinity`, `1e`, `1\n` | Refuse lexical admission without coercion. The final example denotes an actual trailing newline. |
| `1e-4`, `1e18` | Lexically valid, then refuse scale or precision respectively. |

## Original token work and zero-exponent boundary

Admit original token byte length and the enclosing operation’s cumulative scan/copy budget before invoking the owner coefficient function. Charge the retained original token, UTF-8 transport copy, regex/mantissa intermediates and coefficient/native projection simultaneously where live; the 23-byte native projection does not bound the original source. A refused resource admission cannot retry the same operation with a reset per-field account. No public numeric coercion, exponent-sized padding or native cast may precede admission.

Preserve the pinned UMF function’s exact control order: after full grammar validation, an all-zero mantissa yields coefficient zero before the nonzero exponent-length check. Thus `0e999999999999999999999999999999999` and its negative-zero counterpart are mathematically zero if their original source/work budget is admitted; retain the entire lexical spelling. A nonzero token with that same 33-digit exponent is refused by the pinned owner function’s bounded exponent rule. Do not apply an unconditional exponent-length filter that silently narrows admitted zero semantics, and do not claim arbitrarily long zero tokens are free: source and scan admission still bounds them.

The [owner observation](../../04-build/evidence/design-audit/reference-zero-exponent-owner-observation.json) confirms these three independently expected outcomes by directly invoking the pinned UMF function. It covers coefficient behavior only; actual resource admission and native parity remain planned.

For nonzero values, reuse the owner’s exact coefficient interpretation after original budget admission. The owner’s existing 32-character exponent limit is a pinned implementation capability bound, not a new UMF field facet or permission to allocate large padding. Native producer/parser implementations must establish equivalent admitted meaning under their own finite resource profiles. Keep resource exhaustion, unsupported implementation subset, lexical invalidity and decimal domain violation separately observable under the existing refusal contract.

## Producer and qualification obligations

### Proposed native decimal construction

Keep the existing 0.12 `row_home_scalar.numeric_value` declaration as unconstrained `pg_catalog.numeric`; do not replace this shared column with a field-specific typmod. PostgreSQL 17 documents that unconstrained numeric does not coerce a chosen scale, whereas a declared scale rounds excess fractional digits. It also admits nonfinite special values. [PostgreSQL numeric documentation](https://www.postgresql.org/docs/17/datatype-numeric.html). The field validator must therefore enforce finite decimal(21,3) meaning independently; the column alone cannot.

After exact original token/domain admission, construct the native input from the admitted signed coefficient at scale three, rather than passing arbitrarily long original exponent spelling to PostgreSQL's numeric parser. Use the coefficient's bounded magnitude digits: pad on the left to at least four digits, split exactly three fractional digits, prefix minus only for a negative coefficient, and emit no exponent or plus. Zero yields `0.000`. The largest native input is 23 ASCII bytes including sign and decimal point. This is a private mathematical projection, not a replacement lexical source or portable UMF encoder. Retain `-0.000` or other original zero spelling independently in the token/source slots.

Bind that private input as an explicitly typed native parameter under the selected descriptor/profile; never interpolate it into SQL. Read back the stored numeric through the admitted exact native output grammar and independently establish equality with the original coefficient/1000 before publication. Constructing a bounded input does not prove PostgreSQL transport, parser, native resource or writer-path qualification. Direct/bypass writes still require the complete finite/domain/token agreement checks and mandatory integrity enforcement promised by their own profile. Weft comparator and result-decoder registration remain compiler-owned.

Independent projection expectations are `9007199254740993.000` for coefficient 9007199254740993000, `0.000` for mathematical zero, `-0.010` for coefficient -10, and `-999999999999999999.999` for the negative boundary. RD-01/03 and LC-01/04 must compare these mathematical native inputs separately from the original token spellings; differing fractional spelling is permitted only for the private projection, never the token-preserving public result.

The [UMF compatibility receipt](../../04-build/evidence/design-audit/reference-codec-umf-compatibility.json) pins primary UMF commit 16c35e8 and the inspected coefficient source/dependencies. Existing `schemaCoefficient(token, 3, 21)` agrees with seven independently authored coefficient expectations and refuses eight malformed tokens plus two domain violations. Reproduce with `bun docs/helix/04-build/evidence/design-audit/check-reference-codec-umf.ts` using the pinned UMF primary checkout. This imports the existing owner function; it introduces no Truss coefficient encoder. It does not qualify the complete public UMF package, native conversion, resource producers or compiler registration. The fixture preserves lexical zero sign separately because mathematical coefficient zero discards it.

The codec producer must bind original grammar/domain definitions, full source artifacts, selected native column descriptors and complete parser/conversion/operator/security dependencies before registering this dispatch. The native admission path must enforce these same rules for every promised writer path, and owner-wide read prerequisites must detect independently inserted corruption before predicates or publication.

Select finite token/source/string scan, exponent work, UTF-8 encoding, copy and exact comparison limits through the enclosing qualified resource profile. Exhaustion refuses the complete operation; limits cannot reset per field or retry. Exact limits, native parser/producer bodies, immutable registered bytes and their hashes, driver transport evidence and Weft registration remain delivery work. The lexical proposal resolves the fixture grammar choice but does not close those outputs.

RD-01–04 and the complete M03–M07 assessor must include these independent lexical vectors alongside domain, presence, owner and settlement observations. Actual qualification remains unexecuted; Weft's current null exclusion remains an explicit prerequisite for complete Item projection.
