# Truss 0.0.51 published release proof

`umf-truss==0.0.51` is published on [PyPI](https://pypi.org/project/umf-truss/0.0.51/)
and in the [immutable GitHub release](https://github.com/DocumentDrivenDX/truss/releases/tag/v0.0.51).
The import remains `truss`. Use a fresh environment when moving from the old
distribution name because both packages provide that import tree.

```sh
python -m pip install 'umf-truss[query]==0.0.51'
```

## Exact source and publication identities

- Normal merge: [PR #39](https://github.com/DocumentDrivenDX/truss/pull/39),
  `26c1b9171718ad0f6291b82f65c8cef0406886fb`; tree
  `12e9fbb8ad72dc960c5b59adccc87011a306cbd2` equals reviewed head
  `90e5e4e77ce12172aa323a74a6c55e907a529202`.
- Tag `v0.0.51` was created once at that merge. GitHub release `425804959`,
  published `2026-10-27T17:56:46Z`, is actually immutable. All 17 asset IDs,
  sizes and API digests are retained in `verification-record.json` and
  `release-api.json`; every downloaded asset matched its digest and size, and
  the complete `SHA256SUMS` closure matched.
- Exact-tag Linux producer [40549597103](https://github.com/DocumentDrivenDX/truss/actions/runs/40549597103)
  passed package `122349437603`, native `122350361032` and publication
  `122369060691`. Native execution took 33m22s. Optional stress, capacity
  statistics, installer comparison and named real-schema extension steps were
  outside this selected run; the selected small public workload ran and passed.
- Automatic publisher [40555332184](https://github.com/DocumentDrivenDX/truss/actions/runs/40555332184)
  ran by `workflow_run` with driver/source
  `26c1b9171718ad0f6291b82f65c8cef0406886fb`. Verify-release `122369759482`,
  publish `122370316424` and installed-consumer `122371253335` all passed.
  The original publication receipt records `oidc_upload`, actual trusted
  publisher use and verified registry bytes. No local registry upload occurred.

## Qualification and public bytes

Original final-tag receipts record 108 populated migration/existing-current
cases, 62 independent HF cases and 174 managed-grant tests with zero skips,
plus the remaining required installed workflows and selected small public
workload. `linux-artifact-verification.json` records the five original Actions
artifact IDs, ZIP sizes and independently verified API digests. The public
migration/HF/managed receipt bytes equal those original producer receipts.
Original raw receipts, the workload report and terminal producer job roster are
retained here; `retained-file-hashes.json` binds the retained files.

| Public archive | SHA-256 |
|---|---|
| `umf_truss-0.0.51-py3-none-any.whl` | `eb59141c48e94bb93ab7053e9e8725012eee1749e4432e9c71804d23abbdff57` |
| `umf_truss-0.0.51.tar.gz` | `0f091b8c87428a003cf2a5cc68c3905fca66a3cd35e23d353b015346afd4718c` |

Both independently downloaded public PyPI archives match the immutable GitHub
assets byte for byte. The fresh Linux Python 3.11 consumer installed
`umf-truss[query]==0.0.51` using only `https://pypi.org/simple`, checked all
resolved downloads came from `files.pythonhosted.org`, and imported `truss`
and the exact declared `weft-sql==0.4.51`. The source, publication and consumer
receipts remain separate. Future qualified tag releases use this same automatic
Actions OIDC route and main-only `pypi` environment without a stored token.

`archive-verification.json` compares the final public wheel with the actual
public 0.0.50 wheel. All 468 shared execution payload files are identical; only
the migration index changed and its exact original 0.0.50 index was added as an
archive. No payload file was deleted. Native manifest remains
`288801f7177338328441b5d3ce9328af31740ebf513f04ea45e30ae316a9f3a4`.
The existing Weft consumer archives, source revision
`557153731e9f5d0583193a1189a07c6ed485d3d3`, embedded UMF JavaScript/V8 owners,
native SQL and immutable recipes retain their identities. Weft 0.4.55 adoption
requires a separate preserving consumer-archive migration.

## Source distinctions and limits

The [candidate receipt](../truss-0.0.51-candidate-linux/README.md) binds the earlier
`f3fc953814f71fe4c8e4abaa86b762a51b53add0` source to run `40509075159`.
The later documentation/raw-evidence head and final normal merge retain their
own identities; the final tag was independently qualified above. Earlier failed
candidate runs and all historical release assets remain unchanged.

Core's sequencing prerequisite was independently confirmed before the Truss
merge: immutable Core release `425637342`/`python-v0.10.3` at
`7d334dec45948953718bfacd3ed6dd199cadba79`, Actions PyPI `40533286158` and full
Linux public proof `40547321010`. Its original accepted handoff and review are
retained under `core-prerequisite/`. This is sequencing evidence; Truss does
not acquire a Core Python dependency or repin its embedded JavaScript bundles.

The actual Truss native profile is Linux x86_64, Python 3.11, PostgreSQL 18.6
and the exact recorded dependencies. CI is Linux-only. The universal Truss
wheel and existing public macOS ARM64 Weft 0.4.51 wheel remain available;
historical macOS qualification keeps its original versions and scope. No new
Truss 0.0.51 macOS native execution, populated migration, managed Lakebase or
broader performance/platform qualification is claimed.

Only the latest Truss application runtime is supported. Every admitted database
lineage retains its unexpired explicit forward path; 0.0.49/0.0.50 use
existing-current verification without a fabricated physical migration. Startup
does not migrate or reset a database. Pre-0.10 UMF compatibility and downgrades
remain unsupported.
