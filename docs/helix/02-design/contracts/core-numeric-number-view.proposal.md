# Pure core lossless number view proposal

Select `viewNumericAsNumber` as a proposed public pure-core operation alongside the existing numeric data carriers. Its public standalone entry takes one original ExactNumericToken under a fixed qualified per-call resource profile; it returns either the existing LosslessNumericNumberView or an explicit invalid-token, lossy-number, nonfinite-number, unsupported-profile or resource refusal. The exact argument/result declaration is authored; parser/resource-profile producer binding remains required before publishing the export. No I/O, host globals, native driver or database authority is involved, and construction/import performs no work.

This operation converts an exact source representation into an optional convenience view. It does not validate an authored Field's UMF domain, assert that the input came from an admitted read, mutate a value, choose integer versus decimal meaning from spelling or round into a Field. Field input admission remains the existing UMF-owned semantic boundary and CONTRACT-010's declared-domain procedure. NumericReadValue remains the default exact carrier; successful output retains the original wrapper and exact spelling.

Admit exactly one numeric wrapper and its selected original lexical profile. Reserve complete token inspection, binary/rational conversion and output/copy work before allocation. Unknown profiles, unsupported source grammar, nonfinite candidate or capacity exhaustion refuse without a view. Construct the candidate JavaScript number, decode its actual binary64 sign/exponent/significand into an exact rational, and compare with the original token's exact rational meaning under admitted bounded arithmetic. Accept only exact equality; a decimal string round trip or formatted equality is insufficient. Integer safety and mathematical equality are distinct: a representable integer outside JavaScript's safe-integer range still refuses the integer convenience view. Preserve original signed-zero spelling in `original`; the view cannot establish lexical/source equality for keys.

Pure expected examples include integer 42 and decimal 0.5 accepting; integer 9007199254740993 refusing; decimal 0.1 refusing exact binary-rational equality; negative zero preserving the original token and its selected signed-zero meaning. Invalid grammar and resource overflow are separate from lossiness. Before export, independently author full exponent, subnormal, underflow, overflow, signed-zero, safe-integer boundary and lexical variants using the existing exact comparison procedure. Browser execution must exercise the real packed public helper, not a host-side substitute. These are proposed behavior and future test inputs, not an implemented helper or qualified numeric profile.

Implementation must reuse admitted UMF numeric semantics where they apply and the existing Truss binary-rational comparison design, with no copied UMF validator/encoder or JavaScript coercion fallback. Bind exact original resource and parser procedures before runtime delivery. The broader pure planner/codec API selection remains separate; one convenience helper cannot qualify the complete browser core or toolkit.


## Existing resource profile composition

Use the existing [numeric admission resource profile](bindings/numeric-admission-resource-v0.1.candidate.json), not a second convenience-only budget. Its reference limits include 4096 input token bytes, 65536 intermediate integer bits, 33554432 simultaneously retained owned bytes and 2000000 cumulative charged work units. Apply all limits conjunctively with its original producer/dependency and every-pass rules. A token-size allowance cannot guarantee successful conversion when remaining work/peak is smaller. The standalone helper binds its fixed resource definition in the packaged implementation; internal enclosing-context binding remains required; raw caller counters, a matching profile label or shape-valid artifact cannot prove an enclosing operation reservation.

Before scanning, reserve complete required token visits and all simultaneous original/candidate/binary/rational/output custody under the selected producer bounds. Before scaling or multiplication, derive conservative bit/token/work bounds using exact checked arithmetic. Overflow/excessive exponents never authorize a huge pow10 allocation first and a refusal afterward. Admit complete source grammar before using a zero shortcut; preserve original zero spelling and do not normalize a large-exponent zero through Number formatting. Numeric source/profile support remains independently admitted, rather than inferred from an all-zero mantissa.

When invoked inside a Truss read or mutation context, repeated convenience attempts charge that same original enclosing work/peak account, including failed attempts and copies. A per-call local allowance cannot reset shared spent work. A standalone pure consumer receives only the helper's qualified own-work guarantee; it does not acquire a native operation ledger, Field validation or database support from that result. Unknown producer bounds refuse the relevant profile before conversion. Exact context/dependency binding and implementation observations must precede a published capability.


## Selected standalone declaration boundary

The [draft declaration](bindings/truss-numeric-number-view-v0.1.d.ts) selects viewNumericAsNumber(input) with a closed lossless/refused result and no caller budget/domain override. The standalone entry binds the existing reference numeric resource profile as part of its exact packaged implementation/definition; profile admission is library-owned, not inferred from token type. Each standalone call owns its qualified local work account and supplies no claim about an enclosing database operation. Refusal retains its reason; success retains original token and value.

Internal Truss readers/mutations must invoke the same conversion procedure with their original shared accounting integration, not call the standalone entry to obtain fresh budgets. That internal integration is independently reviewed under existing executor/resource custody and is not another public callable or a second converter. The public draft closes argument/result shape; lexical/profile/dependency/producer and packed/browser runtime evidence remain required. Compile-only controls reject raw numbers, conflicting wrappers, caller budget expansion and reasonless refusal.


## Field facets and standalone rational conversion

The resource profile's selectedDecimalPrecision and selectedDecimalScale bound an authored UMF decimal Field admission. The standalone helper has no Field and must not infer either facet from the token's digits or exponent. It applies the token, intermediate-bit, derived-token, peak and cumulative-work ceilings and the qualified parser's own admitted lexical bounds. This interpretation does not enlarge any Field's admitted precision/scale or bypass its UMF validation. Internal Field operations enforce their actual domain separately before invoking the shared conversion.

An exact decimal spelling of the smallest binary64 subnormal has scale 1074 and fits the standalone 4096-byte token ceiling. It is therefore a semantic lossless candidate under a qualified standalone profile; it is not a decimal(1000,1000) Field value. A missing producer bound still refuses before conversion. The independent numeric oracle includes exact minimum-subnormal, half-minimum-subnormal, minimum-normal, maximum-finite and maximum-finite-plus-one constructions. Their expected semantic outcomes remain conditional on complete lexical/resource admission and do not claim runtime execution.

## Selected refusal order and observation meaning

The standalone helper uses this ordered admission procedure. It never executes later phases merely to obtain a more specific reason after an earlier refusal:

1. Admit the packaged lexical/resource/dependency profile. Missing or unsupported profile yields unsupported_profile before interpreting the token.
2. Admit the closed exactly-one-wrapper carrier and complete source-byte inspection reservation. A structurally invalid carrier yields invalid_token when its bounded shape can be inspected; insufficient reservation or excessive token/producer bounds yields resource_limited before full grammar inspection. TypeScript declarations alone do not validate runtime callers.
3. Inspect the complete admitted token under the selected grammar. Malformed syntax yields invalid_token. No prefix parse, trimming or Number coercion supplies grammar validity.
4. Reserve the remaining exact rational and binary64 conversion work/peak before each required operation. Exhaustion yields resource_limited, including for otherwise malformed or lossy inputs whose relevant later meaning has not been established. After exact source interpretation, an integer wrapper with nonintegral mathematical meaning yields invalid_token before constructing the binary64 candidate; valid JSON number syntax alone does not validate that wrapper.
5. Produce the candidate binary64 value under the admitted conversion procedure. A nonfinite candidate yields nonfinite_number. For a finite candidate, exact rational inequality or an integer wrapper outside the safe-integer range yields lossy_number. Otherwise return the lossless original-preserving view.

A refusal is a statement about the phase actually reached, not a complete diagnosis of the source. In particular, resource_limited cannot imply valid grammar, invalid UMF meaning or representability; unsupported_profile cannot imply invalid_token. Nonfinite_number does not grant a float-domain value. A finite negative-zero candidate must retain the selected source signed-zero meaning before success. The integer safety restriction remains wrapper-specific; a decimal wrapper's exact finite integer meaning is governed by exact binary64 equality rather than by inventing an integer Field.

Repeated internal attempts retain the enclosing account's spent work even when they reach different refusal phases. They cannot retry with reordered checks to obtain a successful view outside that account. Qualification must separately exercise malformed over-limit tokens, unknown-profile malformed tokens, finite unsafe integers, overflow and underflow, and resource exhaustion before candidate/rational comparison. These cases test the declared precedence; no expected semantic outcome is substituted for missing producer or profile evidence.


## Selected token-family meaning

Use UMF's existing exact JSON numeric syntax for both wrappers, including exponent notation, with complete-token matching and no whitespace, leading plus, leading-zero integer part, missing fraction digits or nonfinite spellings. The integer wrapper additionally requires an exact mathematical integer; 1.0 and 1e3 qualify, whereas 1e-1 does not. Preserve their original spelling on successful views. Decimal wrappers carry exact base-ten meaning without requiring a fractional spelling; decimalToken 9007199254740992 is an exact finite binary64 candidate, while the same integerToken refuses the safe-integer convenience rule. This does not change either wrapper's Field or key admission.

Authority: UMF main 16c35e8d943769ccfa7bb57d16785aa7159abe65, CONTRACT-040's key tuple operation boundary and src/model/schema-literals.ts schemaCoefficient. Its existing scale-zero interpretation supplies the integer semantic requirement. Reuse admitted owner primitives where applicable, with exact selected resource/error translation; do not copy its parser or assume its scale-zero coefficient routine implements arbitrary standalone decimal rationals. The standalone parser/producer binding remains a specific implementation dependency, rather than an unresolved choice of lexical syntax. UMF's bounded exponent and zero-shortcut behavior must remain explicitly scoped when selecting that dependency.

## Concrete binary64 decomposition procedure

Inspect the actual candidate number through a browser-compatible eight-byte IEEE-754 view with explicit byte order. Treat the bits as one unsigned 64-bit pattern; decode sign bit, 11-bit exponent E and 52-bit fraction F with exact integer bit operations. Reserve the view/copies and arithmetic work before allocation. Host decimal formatting and native driver parsers do not participate.

For E=2047, refuse nonfinite_number. For E=0 and F=0, retain the actual sign of zero separately and use mathematical zero for rational comparison. For E=0 and F>0, the exact signed value is sign × F × 2^-1074. For 1<=E<=2046, it is sign × (2^52+F) × 2^(E-1075). Keep this bounded coefficient/power-of-two representation until an admitted comparison needs expansion. The coefficient has at most 53 bits; exponent lies in -1074..971. These bounds describe this binary decoding stage, not the original token parser or complete helper's memory/work guarantee.

When exact comparison requires a rational, a nonnegative power shifts the coefficient into the numerator; a negative power creates an exact power-of-two denominator. Preflight every shift/allocation and cross-product under the selected account; never multiply before checking conservative result/work bounds. Compare with the fully admitted source rational, retaining wrapper integer-safety and signed-zero rules. The eight-byte pattern and fixed bit bounds do not waive full token interpretation or shared-account charges. No UMF decimal parser/encoder is recreated by this procedure.

Independent bit witnesses are positive/negative zero (0000000000000000 / 8000000000000000), half (3fe0000000000000), minimum subnormal (0000000000000001), minimum normal (0010000000000000), maximum finite (7fefffffffffffff), positive infinity (7ff0000000000000) and a NaN pattern (7ff8000000000000). Their required mathematical outcomes are respectively signed zero, 2^-1, 2^-1074, 2^-1022, (2^53-1)*2^971 and nonfinite refusal. Test actual candidate bit inspection and independent original token comparison separately; agreement between two implementations of this decoder cannot replace the independent rational oracle.

## Current UMF numeric producer adoption handoff — 2026-10-08

Committed UMF `e3555b9aac9e4c3caa952203958c4b0c33cdf519` exports
`admitJavascriptNumber`, `exactDecimal`, `integerFromBigInt`,
`integerToBigInt` and `numericToNumberLossless` from its public index.
`src/adapters/javascript-numeric.ts` performs exact binary64/decimal value
comparison, preserves token spelling in constructors and optionally applies
current Field-context checks. This supersedes the earlier absence of a
concrete owner conversion producer. Consume these APIs at an immutable
source/build pin; the binary decomposition above remains an independently
specified oracle/design explanation, not a directive to implement a second
Truss numeric parser or converter.

The wrapper's successful view retains the original Truss exact carrier and
uses only the owner-returned number. Safe integer admission and integer bigint
conversion use their respective owner functions; decimal constructor admission
uses exact text. There is no round-to-nearest fallback: ordinary decimal
`0.1` refuses a number view, whereas its exact binary64 decimal expansion can
qualify. Integer `9007199254740992` refuses the safe-number view while the
same decimal carrier can qualify by exact value. Field-context validation
requires the separately admitted current 0.8 document/transition and is not
implied by context-free numeric conversion. Native storage text and lexical
source remain canonical custody regardless of convenience output.

Two integration boundaries remain explicit. First, the owner converter
refuses negative zero, including decimal `-0.000`, although its exact decimal
constructor retains that spelling. Preserve signed zero in the default exact
carrier; a signed-zero number view is unavailable through this producer. Do
not add local special-case conversion until the selected signed-zero view
profile is reconciled with the owner. Second, owner text/exponent bounds and
internal allocation are not the Truss shared operation account. Qualify
conservative producer admission/allocation/work bounds and charge them before
invocation; otherwise the operation-bounded convenience capability refuses
as unsupported. Do not invoke first and claim post-call counting proves the
precharged resource profile. Unknown owner errors must not be classified as
lossy_number; pin tested error translation before public export.

Execution controls compare the actual pinned owner call and packed Truss
wrapper with independently authored exact carrier/value expectations:
safe-integer limits; decimal half; decimal 0.1; exact binary expansion of 0.1;
integer versus decimal 2^53; exact minimum-subnormal token; overflow and
underflow; signed zero preservation with refused view; exponent lexical
variants; invalid wrapper/getter input; unknown Field qualifiers; and
resource refusal before any owner call. Cover current Field-context admission
separately from context-free view conversion. Run the real public wrapper in
Chromium and supported host packages; upstream unit tests alone cannot qualify
the wrapper, account, native read custody or complete toolkit. These controls
are planned, not_run.

The selected owner producer now has [eleven real Chromium observations](../../04-build/evidence/design-audit/umf-numeric-browser.json)
against independently specified exact tokens: safe integer/half/decimal 2^53/
exact binary expansion positives, unsafe integer/decimal 0.1/signed-zero/
overflow/underflow refusals and exact int64 bigint round-trip. Reproduce an
isolated owner build with `bun scripts/build-umf-runtime.ts /path/to/umf numeric-current`,
then set `TRUSS_UMF_NUMERIC_PRODUCER` to its output and run
`bun scripts/check-current-umf-numeric-browser.ts`. The receipt pins original archive,
bundle and dependencies. These context-free observations do not qualify the
Truss wrapper, Field context, native values or precharged operation accounting.
Historical record/numeric/value build modes retain their separate pins.

## Existing Truss registration reconciliation

The existing `packages/umf-bun` registration already captures these owner
functions at immutable 9e4bed3e. Its adapter, schema-literal and Field-properties
source files are unchanged at reviewed remote e3555b9a, as pinned in the
[registration sync](../../04-build/evidence/design-audit/umf-numeric-registration-sync.json).
Preserve that runtime registration; the newer isolated browser source is a
separate observation, not a compulsory runtime repin. Fresh execution of
`tests/umf-numeric-runtime.test.ts` passes four tests/21 assertions; the original
16-case Chromium corpus also passes, including scoped current Field context
and registration-substitution refusal. Thus owner API capture and scoped
Field-context bridge checks already exist. The public standalone wrapper,
complete source/native admission and conservative shared-resource/error
qualification remain separate obligations. Do not rebuild a second registration
or report the already implemented bridge as missing design.
