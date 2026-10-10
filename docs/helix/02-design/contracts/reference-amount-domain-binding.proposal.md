# Reference Item.amount domain binding proposal

Original fixture: document truss.integration.account-items.v1, module integration, field Item.amount, /modules/0/elements/2 in the [field inventory](reference-account-items-field-inventory.proposal.json). Preserve required decimal precision 21 and scale 3. UMF CONTRACT-040 defines a fixed-scale value as integer coefficient times 10^-scale, with absolute coefficient below 10^precision and no implicit rounding. This proposal consumes that meaning; it introduces no portable encoder or alternative decimal semantics.

Admit mathematical value v only when c = v × 1000 is an exact integer and |c| < 10^21. Thus the inclusive extremes are ±999999999999999999.999. Compute admission with the existing selected exact UMF/value profile under finite token/work bounds, never floating-point multiplication. Missing lexical/grammar/source admission refuses. Preserve the original decimal token separately from the mathematical coefficient/native projection: trailing zeros and an admitted negative-zero spelling cannot be silently rewritten during readback or history capture. Equality and portable key semantics, if separately selected, follow the original mathematical UMF operation rather than token spelling.

| Independent vector | Required coefficient/domain result |
| --- | --- |
| 9007199254740993.000 | coefficient 9007199254740993000; admitted exactly, original token retained; no JavaScript number conversion |
| 0.00 | coefficient 0; admitted at scale 3 without rewriting original spelling to 0.000 |
| -0.01 | coefficient -10; admitted exactly, original token retained |
| 999999999999999999.999 and its negative | coefficients ±999999999999999999999; admitted boundary |
| 1000000000000000000.000 and its negative | coefficients ±1000000000000000000000; refuse precision overflow |
| 0.0001 | scaled value 0.1 is not an integer coefficient; refuse scale violation rather than rounding |
| 1.2300 | coefficient 1230; mathematical admission does not reject a spelling merely for redundant trailing zero; exact original lexical profile must also admit the token |

Native binding must select the original storage home, exact decimal codec/token grammar, numeric projection domain and complete dependency/resource profile. Validate the original value and finite native output before any narrowing cast or public decoding. A stored native numeric projection must equal the independently admitted exact coefficient/1000, be finite and satisfy the domain; SQL NULL, NaN/infinity, rounding or token/projection disagreement refuses. A native typmod declaration, successful cast or rounded projection cannot establish original admission. Every selected field's owner-wide integrity/domain guard precedes query predicates and publication.

The reference requires exact storage/readback of the three M03 amount tokens, independent whole-operation failure on overflow/nonrepresentable scale, and complete private result/publication checking. Native equality, ordering, key membership and SUM are separately registered capabilities with their own required semantics; this projection binding grants none implicitly. Item.amount is not a key component in the original fixture.

V2 must bind native codec/storage and direct-read evidence; V4 must register the exact decimal(21,3) original definition with Weft. The accepted sales decimal(28,2) receipt cannot qualify this domain, and changing the fixture precision/scale to match it is forbidden. Independent tests retain original definition/token/projection bytes, exact descriptors, full owner prerequisite traces and native failure/settlement observations. These vectors are planned domain expectations, not native executions or proof of compiler adoption.
