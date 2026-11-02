# Truss 0.0.53 published baseline proof

`umf-truss==0.0.53` is published on [PyPI](https://pypi.org/project/umf-truss/0.0.53/)
and in the [immutable GitHub release](https://github.com/DocumentDrivenDX/truss/releases/tag/v0.0.53).
The source is `d6efcb4fded2cb94393f4056d960f51008919383`, merged through
[PR44](https://github.com/DocumentDrivenDX/truss/pull/44). The complete identities,
asset digests, public installation URLs and disposition are in [receipt.json](receipt.json).

## Required actions and support boundary

The owner explicitly selected a fresh-install baseline on 2026-11-02:
“Drop all the old junk. We need a baseline as of now.” Initialize a fresh
database and use a clean Python environment:

```sh
python -m pip install 'umf-truss[native,query]==0.0.53'
```

Historical installation upgrades and historical migration-receipt recovery are
retired. Existing databases are never reset, relabelled or automatically
upgraded. Moving their data needs a separately qualified export/rebuild
procedure; this release supplies no such conversion. Unknown sources and
native drift continue to refuse. The active index has no predecessor wheels
or migration edges. Native SQL, embedded owners and the selected compiler retain
their original identities. Original published assets and failed historical
lineage evidence remain preserved with their original scope.

Qualification covers the exact PostgreSQL 18.6 / UMF 0.10 / Weft 0.4.51 current
target on Linux x86-64 and the selected installed-runtime subset. It does not
establish complete protected-profile adoption, actual Lakebase or Ashlar
production acceptance, or general cross-platform support.

## Qualification and public bytes

- [Complete candidate run](https://github.com/DocumentDrivenDX/truss/actions/runs/41492233903)
  passed before the release-note-only finalization and merge.
- [Exact-tag Linux run](https://github.com/DocumentDrivenDX/truss/actions/runs/41495685215)
  passed packaging, all six baseline controls, all 62 independent HF cases,
  all 174 managed-grant tests, every installed-runtime workflow and publication.
  Optional stress campaigns were not selected.
- [PyPI run](https://github.com/DocumentDrivenDX/truss/actions/runs/41499832807)
  passed exact source/assets validation, actual OIDC upload, verification of
  PyPI-served wheel/sdist bytes, and a fresh public-index Linux query consumer.
  Original [publication](pypi-publication-receipt.json),
  [source](pypi-source-receipt.json) and [consumer](pypi-consumer-receipt.json)
  receipts are retained byte-for-byte.
- Every entry in the 16-file `SHA256SUMS` closure and the checksum manifest's
  own API digest matched the 17 public GitHub assets. The release pins explicitly
  advertise `fresh-baseline-only`, no historical upgrade support and no admitted
  predecessor sources.
- Original [Linux baseline qualification](baseline-qualification.json) and
  [shutdown evidence](baseline-cleanup.json) are retained. `pg_ctl status`
  returned 3 and `postmaster.pid` was absent before fixture data removal. The
  immutable [native evidence archive](https://github.com/DocumentDrivenDX/truss/releases/download/v0.0.53/migration-qualification-evidence.tar.gz)
  contains these same cleanup bytes. Its historical filename does not advertise
  historical migration support; the receipt scope is the fresh baseline.
- An independent fresh PyPI-only native/query installation on macOS arm64
  matched the GitHub Truss wheel and the qualified public Weft wheel/module.
  The original [pip installation report](fresh-public-pip-report.json.gz)
  retains every public download URL and archive hash. Its gzip stream preserves
  the original JSON bytes, including the original absence of a trailing newline.
  With the separately checksummed existing host PostgreSQL wheel,
  [all six baseline controls passed](fresh-public-native-qualification.json)
  and [shutdown was confirmed](fresh-public-native-cleanup.json). This is a
  host-native subset check, not macOS CI or the complete hosted suite.

The complete [HF receipt](https://github.com/DocumentDrivenDX/truss/releases/download/v0.0.53/hf-conformance-qualification.json)
and [managed-grant receipt](https://github.com/DocumentDrivenDX/truss/releases/download/v0.0.53/managed-grants-qualification.json)
remain immutable release assets, with their hashes recorded here.

The immutable 0.0.52 tag still resolves to
`1d23bedfdfdc0901e16e1a0663882c765fe1068f`. All three old asset digests match the
original readback. No old asset, initializer, native inventory or failed receipt
was rewritten to establish this baseline.

## Branch and worktree disposition

[branch-disposition.json](branch-disposition.json) records all 23 primary local
heads and all seven registered worktrees. Three history reconciliations bring
the already-incorporated lean-CI,0.0.43 evidence and equivalent Linux-only CI
branches into ancestry. The resulting tree equals the published tag exactly;
no runtime changes are introduced by those merges. 21 local heads are then
incorporated. The remaining heads are preserved and explicitly retired from
current baseline delivery scope:

- `codex/consolidation-20261025-private-tmp-truss-pws03-20261023`,
  `8bc82edd270a0043cd48ef8073fb2ef755eb017b`.
- `codex/embedder-e0-e1-release`,
  `a2b9c8a1fc98a34528a32492b7ca5ad4a1bad955`.

The [final head disposition](historical-head-disposition.json) records the
concrete evidence and owner-decision boundary. The temporal snapshot is an
unverified, separately versioned feature experiment whose own plan excludes
publication. The E0/E1 head is historical 0.0.43 delivery work: its required
behavior and safeguards are already adopted or superseded in the current
qualified baseline. Its residual history does not merge without native/code
conflicts, so no forced ancestry merge is made. Neither head is required work
for 0.0.53. No owner decision remains for baseline closeout; an explicit future
feature decision or demonstrated current defect would be a new work item.

This classification leaves every commit, file and private index intact. It
restores no retired migration semantics and requires no new package version.

[PR43](https://github.com/DocumentDrivenDX/truss/pull/43) is closed as superseded.
Its original dev8 ABI refusal, source and evidence remain on the preserved
branch at `21e3d303a07fb88c247efefa3a87183f210a466b`. The 0.0.53 baseline retains
its existing optional dev5 pin and makes no dev8 adoption claim. Any future
optional cohort needs separate version-coherent qualification.

The primary checkout is unchanged. Six stale registrations, their original
private indices, and all five residual directories containing files are
retained. Missing `.git` markers are not treated as proof that working files
are clean or disposable. No unique commit or uncommitted work was deleted.
