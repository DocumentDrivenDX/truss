# Current portable Python preview — 2026-10-13

Public preview0.10 selects installed native runtime0.38-candidate/Weft0.4.8/layout0.16 candidate. The two existing JSON examples retain22 basic and10 exact-scalar observations. Structural comparison against0.9 confirms only format, profile.runtimeRelease and expected installation release change; both original UMF fixtures are byte-identical. Prior0.9 files remain unchanged. The current runner explicitly selects0.10 and refuses other profiles.

Both existing basic installed-package tests (`test_public_preview_corpus_native`) pass in16.749seconds using truss-toolkit0.1.0.dev38 loaded from the clean CPython3.12.14 environment, committed Weftcb10d8e, DocumentDrivenDX pgserver-pg18==18.6.1/PostgreSQL18.6 and psycopg3.3.6. The examples cover public catalog/group/replay/read/refusal/dry-run/import/feed/ACK and exact string/integer/decimal/boolean/timestamp/binary values with absent/null distinction. Actual native identities come from public results, never fixture fabrication.

This refresh makes existing portable examples reproducible on the current installed candidate. No new runtime functionality or test cases, stable-layout support, independent interchange or full consumer conformance claim is introduced. Correct0.10 commands are documented separately rather than copying historical0.9 README references.
