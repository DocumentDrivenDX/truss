# Original source52 native cleanup — archived evidence

This additive archive preserves the authenticated original evidence from
[run 41379481836, attempt 1](https://github.com/DocumentDrivenDX/truss/actions/runs/41379481836),
[job 125066903220](https://github.com/DocumentDrivenDX/truss/actions/runs/41379481836/job/125066903220),
at source `1d23bedfdfdc0901e16e1a0663882c765fe1068f` (Truss v0.0.52).
It records historical scope; it is not a new runtime observation or qualification.

## Relative-path index

| File | Original material |
| --- | --- |
| [review.json](review.json) | Unchanged authenticated cleanup appendix, including observations and proof limits. |
| [job125066903220.log](job125066903220.log) | Original complete job log. |
| [artifact13112413929.zip](artifact13112413929.zip) | Original `released-runtime-evidence` Actions artifact; all 13 members retained without repacking. |
| [run.json](run.json) | Original run metadata. |
| [jobs.json](jobs.json) | Original job metadata. |
| [artifacts.json](artifacts.json) | Original artifact metadata and GitHub digest. |
| [source-correspondence.json](source-correspondence.json) | Original producer/source hash comparison. |

The copied appendix SHA-256 is
`6bd4250ad09ee4f2c5aaea1afa8a04cb24895b89f62b75c77f752de9c773cf9a`.
The original ZIP is 9,089 bytes, SHA-256
`3bc0846c33a204926eac0e538a49e875d2ff140873e40c38475491e7866c6b02`,
matching the recorded GitHub artifact digest. Its original member paths are
under `ci-release-41379481836-1/`; open the ZIP for the JSON receipts and logs.
No duplicate extracted payload is needed for custody.

The original appendix retains absolute `/private/tmp/` recovery paths so its
bytes and hash remain unchanged. For these seven archived files, resolve each
basename through the table above. References under `artifact-contents/` resolve
to the same relative member inside the unchanged ZIP. Original source paths
refer to the immutable source commit, not current candidate code.

## Observed scope and unavailable proof

Original numeric worker postmaster PIDs **2997 and 3025** were captured. The
retained controls record worker/database/role cleanup, shutdown and PID-marker
or directory/socket checks in their stated scopes. CLI PIDs 3116/3152 identify
CLI processes, not PostgreSQL postmasters. Source correspondence matched eleven
producer/test entries against the original receipt; `local_runtime.py` has a
separately retained hash but no corresponding original-receipt hash assertion.

**No numeric OS-PID absence observation and no actually recorded `pg_ctl status`
exit 3 are present for those original worker PIDs.** A conditional fallback in
source does not show that it executed. Do not infer either check from a passing
job, removed directory/socket/PID marker, or ephemeral runner disposal.

This archive neither reruns nor strengthens the historical observations. It
establishes no current native0.76/130-case, full-engine, or managed-service pass.
The [earlier source52 reference](../../../05-deploy/evidence/truss-0.0.53-candidate-linux/release-hold.json)
and [published baseline evidence](../../../05-deploy/evidence/truss-0.0.53-publication/README.md)
retain their original, separate scopes. No historical receipt, initializer,
release asset or frozen inventory is rewritten.
