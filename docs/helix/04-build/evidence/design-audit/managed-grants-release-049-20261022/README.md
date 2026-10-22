# Managed platform grants v0.0.49 release qualification

This packet supports [PLAN-MANAGED-GRANTS-001](../../../managed-platform-grants-plan.md)
and [RELEASE-PYTHON-0.0.49](../../../releases/v0.0.49.md). v0.0.49 is published. The final public tag, assets, checksums, installed Mac
ARM64 verifier, and retained setup diagnostics are bound by the [retained public v0.0.49 proof](published-0.0.49/receipt.json).
The public Truss artifacts include wheel SHA-256
`7ea14b2787f02cbeec9ad99d835adbcc30c684fd5be8e0765a1d8198b50e7182`, sdist
`34ec940aa5ffac7466c1c73cd8cd330e82630d0901023cfe2cba3d353154570a`, and
HF archive `ae5726d745e6ce52f1229ad1d1b46ca6a5ff55d8cb0bb0aa73751f2dd8fd0eb6`.
The retained receipt binds all 17 public Truss assets to API digests and
checksums, tag commit `dd13e95804abc30202d449a756240c6a684ab942`, and the installed
Mac ARM64 proof. That Mac verifier passed its 30 declared supported-driver
tests, 21 worker collision/cleanup controls and HF62; the tag Linux campaign
passed managed130, HF62 and migrations106. The dated sections below preserve earlier candidate
checkpoints and their original limits; the public receipt is the current
release-status authority.

The [public Weft0.4.51 dependency audit](dependencies/public-weft-051/verification.json)
verifies all nine API asset digests and three wheel checksum/ZIP/RECORD/native
inventories. Public packaging metadata binds source557 separately from the
tag/workflow commitd4b. Mac ARM64 and Linux x86_64 match the selected Truss
cohorts; Linux aarch64 remains packaging-only. No native tests run in this
dependency audit. Current native2888 macOS ARM64 and branch Linux qualification
pass on the same exact wheel below. The final tag and public verifier now
qualify the published assets in the [retained public v0.0.49 proof](published-0.0.49/receipt.json); historical native35fd results retain their original scopes.

`preliminary/receipt.json` inventories the retained preliminary evidence and
records its limits, including earlier failed attempts and incomplete raw-log
retention. The integrated macOS ARM64 candidate passed the selected 20-module
campaign (128 tests, no skips), the 62-case HF corpus, nine strict protected
checks, the original public workload and the lifecycle supplement. The public
workload retains 1,000 objects and 1,000 edges, 1,000 reads and 200 committed
updates. These counts describe the retained candidate receipts before the
public source557 compiler refresh; source86 evidence is preserved unchanged.

The [public v0.0.48 audit](dependencies/public-truss-048/verification.json)
verifies the actual published wheel SHA-256
`1aedf614ff3d3ff7a61bd4d91887ede650a7135d1239e8564c1c297c0ddc37c3`,
tag commit8e89, nativec433, original migration manifest7d165 and published
Linux migration80/HF62 receipts. The
[source48 admission receipt](source48-admission/receipt.json) retains the new
America/New_York and UTC captures and raw logs. Both captures, comparison and
additive packaging passed; all 18 existing current pins and all 15 published
v0.0.48 migration artifact bytes remain unchanged. Three new artifacts add
the ACL profile, managed-grants-only edge to native35fd and archived original
v0.0.48 manifest. The resulting migration manifest SHA-256 is
`86bcf78541e316c7e5697fb91e09d4741ef3e3cb5600b9b76ac5c6cc2e836923`.
Earlier candidate source48 captures remain preliminary history. Admission does
not establish final v0.0.49 installed lineage or release qualification.

`supplemental/run_final_local_campaign.py` is the final local campaign producer.
It records the wheel, input files, installed payload, exact independent UMF
oracle, Bun and PostgreSQL identities and verifies them again at completion.
The lifecycle producer is retained unchanged in the same directory. The final
local record below is separate from preliminary evidence. Current macOS and
hosted branch Linux receipts pass. The later exact tag and public-download
gates are complete; see the [retained public v0.0.49 proof](published-0.0.49/receipt.json).

The mandatory finite release campaign is defined by
[the release workflow](../../../../../../.github/workflows/release.yml).
The historical broad all-discovery diagnostic remains incomplete and
unqualified. Actual Lakebase acceptance, TLS/token behavior and consumer
adoption remain separate gates; this packet makes no acceptance claim for them.

The [first Linux v0.0.49 attempt](linux-attempt-1/receipt.json) retains its
original 106-case migration failure: two source48 rollback fault injectors
matched an old SQL statement absent from the new short edge, so no failure was
injected. The corrected injectors execute the real managed-grants ALTER before
failing at the subsequent function statement and explicitly assert injection.
All original rollback, state, ledger and resource-close assertions and deadlines
remain. Sol reviewed eight pure cursor controls across all four routes; only
this producer digest changed, with the other 362 pins and 62 cases preserved.
The final local campaign below passes. The original failed hosted receipt is
preserved unchanged.

## Historical source628/native35fd macOS ARM64 campaign

The [final local qualification](final-local/qualification.json) passes on source
`6287e52a5ef8a0abce90341106e8e9389216cb80`, Python3.11.17, PostgreSQL18.6,
public Weft0.4.51 source557/Mac native3469, and the independent clean UMF5ba
oracle with Bun1.4.3. The [payload audit](final-local/payload-verification.json)
binds wheel
`26cf1fd712930bc9e573682cc6b04b428756201cf619de902d2108769a90e5ff`,
native manifest
`35fd797b5cf48dd888c68e53b9e599df20cffe00f8f3d33e1563820ea808d59f`,
HF62 corpus
`d5b89965ea9962049077fb1b813aed32341c9c8948c70b526a8baf21e5eeabfe`
and HF archive
`c6b1eff58cf81beaf85bf0013f72156aca15654e2a61de49e5e43d440c1666c3`.
All 462 source/wheel/sdist/installed runtime files agree. All 1,198 frozen
inputs, oracle/compiler identities, eight outer logs and 20 managed module logs
verify; cleanup and unchanged-input/payload controls pass. The
[retained-file index](final-local/retained-files.json) binds 56 original outputs
retained losslessly.

The eight steps include 20 boundary controls, 20 managed modules/128 tests,
62 HF cases, nine strict protected tests, all 106 migration/recovery tests over
four actual published source wheels, lifecycle controls and the original public
workload. Test campaigns have zero skips, failures and errors. Lifecycle evidence
preserves the carrier through supported evolution, contained unsupported-record-
retirement refusal and later selected ACL variation. The workload verifies
1,000 objects, 1,000 edges, 1,000 reads, 200 committed updates and values after
connection reopen; it counts 26,121 SQL submissions. Local acceptance is confined
to this exact artifact and macOS scope; it establishes no broader performance,
full-engine, all-discovery or Lakebase claim.

The [second Linux diagnostic](linux-attempt-2/receipt.json) retains corrected
source628's 106 passing migration tests and one HF62 native-deadline failure
(SQLSTATE57014). That unchanged case passes locally and in public48 Linux
receipts. Host speed is a possible explanation, not an established cause. Sol
recommended one unchanged failed-job rerun of run39845177814 at that checkpoint.
The rerun below reproduced it and led to native diagnosis; no assertion or limit
was changed. Current native2888 macOS and branch Linux results below supersede
that candidate's readiness, while final tag/public verification remain open.

The [unchanged Linux rerun](linux-attempt-3/receipt.json) reproduced the same
whole-group audit SQL cancellation. At that checkpoint, release was held for
same-host public48/current49 SQL timing and plan diagnosis.
There is no further incidental rerun; the original workload, assertions and
10-second SQL / 30-second operation limits remain unchanged. The retained final
Mac pass qualifies its recorded source and tuple only.

A new diagnostic native candidate is
`288801f7177338328441b5d3ce9328af31740ebf513f04ea45e30ae316a9f3a4`.
It appends a representation-only audit collector override: native arrays retain
the same values and order before the existing JSON bounds, exact DISTINCT owner
reduction and authorization checks. The original collector source and all prior
migration artifacts remain unchanged. Two additional semantic controls join the
managed campaign (21 modules / 130 discovered tests); the independent corpus
retains its 62 cases and all 363 existing producer digests, adding the new test
producer for 364 bindings. Source628/native35fd local results above remain
evidence for that exact earlier candidate, without qualification of2888.

The [native capture and packaging receipt](audit-accumulation/receipt.json)
records passing actual New York/UTC source-and-target captures, read-only
comparison and additive packaging. The old private v0.0.49 wheel26cf supplies native35fd only as
an intermediate fixture; it does not join the four public source-wheel inputs.
All 21 prior migration artifact bytes remain unchanged. Four additions retain
manifest86bc and add the 2888 profile, exact ACL census and 35fd→2888 SQL-only edge.
The new migration manifest SHA-256 is
`96addcdb95523f478d8f50b0b47198e47a860680c7400dd359711930e837e535`.
All four forward routes resolve to 2888 in 3/3/2/2 edges for public 44/shared46/47/48.
This native profile admission is not a complete installed migration campaign.

The [retained diagnostic](audit-diagnostic-39852375031/receipt.json) ([run39852375031](https://github.com/DocumentDrivenDX/truss/actions/runs/39852375031))
passes original and instrumented invocations of the unchanged audit case on both
public48 and candidate2888 on the same AMD EPYC9V45 host. The instrumented
complete-page query takes 6.940221s versus 0.380100s; original whole-case times are
12.764s versus 5.619s. Default-budget refusals remain SQLSTATE54000, original
10-second SQL/30-second operation limits are unchanged, and all owned worker
inventories and shutdowns verify. Instrumentation affects timing; these figures
are bounded prototype evidence, not broader performance qualification. The
previous 9V74 failures remain separate original evidence.

The next gate is a fresh complete artifact freeze and the 21-module/130-test
managed campaign, HF62, strict protected controls, all four source migration and
recovery routes, lifecycle and the original public workload on the new native
identity. Full macOS ARM64 and branch Linux qualification now pass below.
At this earlier candidate checkpoint, the tag/public verification gates
remained pending. They are now complete for the published assets in the [retained public v0.0.49 proof](published-0.0.49/receipt.json).
No full-engine, all-discovery or Lakebase acceptance is claimed.

The [automatic comparison at source4188](audit-diagnostic-39854667352/receipt.json)
remains red because public48's original and instrumented cases reached the
unchanged deadline on an AMD EPYC7763 host. Candidate2888 passes both invocations:
original whole-case time is 9.833s, versus 19.691s for public48; instrumented
complete-page SQL takes 0.815960s, while public48 cancels at 10.000734s with
SQLSTATE57014. Default-budget refusals remain 54000 and all four workers restore
inventory and stop. The 24 retained outputs and five binary identities preserve
this comparison; it is diagnostic evidence, not full release qualification.

The temporary PR trigger is retired after diagnosis. Manual dispatch retains
the same steps, failure exits, assertions and 10-second SQL/30-second operation
limits. This keeps the known public48 benchmark out of ordinary PR acceptance
without relabeling its failure. The mandatory release workflow and final
qualification requirements are unchanged.

## Full hosted Linux branch qualification

The [retained Linux receipt](linux-2888-branch/receipt.json) records successful
package and complete mandatory native jobs in run39854672450 at source
`4188141faf3e51a7a25711a6fc22751cb37c7ae4`. It binds wheel
`57fd9520a453dcafa52dabe6aa75a143c162593237e80177acaebdbd51202790`,
native2888, migration96add and archive
`ae5726d745e6ce52f1229ad1d1b46ca6a5ff55d8cb0bb0aa73751f2dd8fd0eb6`.
All 467 source/wheel/sdist runtime files agree. All 411 HF archive source payloads
match their manifest and checkout; the corpus keeps 62 cases/364 producer pins.

The run passes 21 managed modules/130 tests, HF62 and 106 migration/recovery tests
with zero skips, failures or errors. The managed receipt confirms baseline
restoration, worker shutdown, unchanged input/payload and the clean pinned
UMF5ba/Bun1.4.3 oracle. HF uses public Weft557's exact Linux native cohort;
migration uses all four actual public source wheels and the prior public48
receipt. The complete mandatory installed regressions pass. The audit case
passes in both HF62 and the broader API regression step. The public workload
verifies 1,000 objects, 1,000 edges, 1,000 reads, 200 committed updates and values
after connection reopen, counting 26,122 SQL submissions.

The packet retains 46 original outputs losslessly, including all 21 managed
module logs, full workflow log and run metadata, with three binary identities
retained privately. The input payload audit's original `nativeQualification:
pending` field remains its pre-gate observation; the completed workflow and
aggregate receipt record the subsequent Linux result. No original evidence is
rewritten. This is a branch Linux pass; publication was skipped. Current2888 full
Mac qualification also passes below. The later final tag campaign and public-
download verification are recorded in the [retained public v0.0.49 proof](published-0.0.49/receipt.json). Lakebase and full-engine acceptance remain separate.

## Current installed macOS ARM64 qualification — native manifest `288801f7…`

The [complete local receipt](./final-local-2888/qualification.json)
passes at source `19d7bbe5793e61e4034769a18b1d9a03b5c7e959` on Python3.11.17,
PostgreSQL18.6, psycopg3.3.6 and public Weft0.4.51 compiler source `55715373…` with the exact Mac
native cohort `34691932…`. It uses the same wheel `57fd9520…`, native manifest `288801f7…` and migration manifest `96addcdb…`
and HF archive `ae5726d7…` as the passing commit `4188141f` Linux campaign above. All 467
source/wheel/installed runtime files agree. All 1,206 input hashes, the pinned
clean UMF commit `5ba77cff` / Bun1.4.3 oracle and compiler/worker identities remain unchanged.

All eight steps exit with status0: module boundaries and 20 allowed/forbidden controls;
21 managed modules/130 tests; lifecycle; HF62; nine strict protected tests;
106 migration/recovery tests over four actual public source wheels; and the
original public workload. Selected test campaigns have zero skips, failures or
errors. Lifecycle checks preserve the original carrier through supported r2
additive evolution, contained SQLSTATE `0A000` unsupported-retirement refusal and later
selected ACL variation. The workload verifies 1,000 objects, 1,000 edges,
1,000 reads, 200 committed updates and values after connection reopen, with
26,122 SQL submissions. The original 10s SQL/30s operation limits are unchanged.

The [retained-file index](./final-local-2888/retained-files.json)
binds 53 original outputs retained losslessly. [Scoped cleanup](./final-local-2888/final-local-audit2888-1-cleanup-owned.json)
confirms no campaign-owned or newly created PostgreSQL process remains;
unrelated pre-existing servers were outside custody and unchanged. The
[retention statement](./final-local-2888/retention.json)
records that the exact branch wheel/sdist/archive containers are private or held
in GitHub artifacts subject to retention limits. These branch artifacts are
distinct from the published wheel, sdist and HF archive, whose full identities
are in the [public proof](published-0.0.49/receipt.json). The published proof
records the post-public Mac verifier, including its driver/worker controls and
HF62 result, plus the exact tag Linux qualification (managed130, HF62 and
migrations106). These selected platform results make no full-engine, broad
discovery, general p95 or actual Lakebase/Arras acceptance claim.
