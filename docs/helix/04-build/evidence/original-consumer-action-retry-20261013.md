# Original consumer action retry — 2026-10-13

The unchanged action.idempotent-retry-returns-the-original case now runs through public Truss groups. Its exact-fixture-bound AddUseCase handler submits create(code,name), leaves optional practiceArea absent, and supplies the original fresh KeyAbsent precondition. The consumer key maps directly to the request ID. The host retains only canonical invocation inputs/request; every repeated step calls native apply. Changed-input and unsupported action/dry-run cases refuse before case writes.

Receipt comparisons follow the original consumer's authored-field semantics. Initial/replay disposition and version come from each actual native result, committed recovery requires semantic equality, and token_is compares the second real token with the first saved committed token. The final original query checks actual row_count without inventing expected rows. It returns one object.

Nine original read/action workflows passed together through installed public packages in one basic native test (15.098seconds): runtime0.34, Weft0.4.7, DocumentDrivenDX pgserver-pg18 18.6.1/PostgreSQL18.6 and psycopg3.3.6. No corpus/model/SQL/expected observation was edited. Astra Ultra reviewed the plan and completed source; it confirmed no host-cached result, correct token equality, KeyAbsent/optional omission, case/control guards and row-count handling. No extra verification campaign was added.

This selected successful retry is not complete consumer adapter/corpus qualification, all flaky-network paths, independent interchange or protected security activation. The original consumer dry-run case remains unsupported by this handler; the existing public caller-rollback group workflow remains available and separately tested.
