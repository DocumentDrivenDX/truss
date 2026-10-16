# Explicit graph target Key validation

Canonical UMF0.8 relationship targets require an authored Key. The physical graph
recipe helper previously allowed a missing authored key to compare equal to a
supplied null native target_key. With empty edge rows this could return complete
coverage over invalid supplied metadata. The new guard requires the explicit
nonempty string Key before any native query. Existing direction/witness/domain,
endpoint/Key correspondence and occurrence/census guards are unchanged.

The independent regression updates the original model, closure and content hash
together and supplies a matching invalid native value. Before the fix it fails
on missing-Key/null-native acceptance and unwanted edge queries; after the fix
all9 graph unit tests pass. Missing/null/empty/bool/integer target Keys refuse
before the cursor is used. Source AST comparison proves only the new target
binding/refusal was added; it does not prove whole program security.

These are supplied-metadata controls, not original UMF semantic admission or a
reachable native exploit. The original catalog/schema path may refuse earlier.
No SQL, native/performance run, registration or default consumer change occurs.
NSB-T06/T09 prerequisites only; shared158/34scope remains45implemented113missing.
The frozen diff receives one focused bounded Astra review, no implementation
ownership or nested delegation, max5minutes wall time. The tool has no token-cap
parameter; the requested20,000-token maximum is not independently enforceable.

The single bounded Astra review completed before its deadline with no findings.
It independently passes all9 tests and15 additional controls; no SQL is run.
All17 reviewer artifacts and exact source packets are retained. No re-review
was needed and the reviewer stopped on completion.
