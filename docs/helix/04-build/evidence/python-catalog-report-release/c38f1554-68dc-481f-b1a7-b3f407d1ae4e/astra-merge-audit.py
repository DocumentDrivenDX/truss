"""Inspect replacement retained packets and compare them with the pre-merge resource checkpoint."""
import datetime
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

spec = importlib.util.spec_from_file_location('resource_evidence_audit', '/private/tmp/astra-catalog-resources-audit.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
if len(sys.argv) != 4:
    raise SystemExit('Usage: merge-audit.py POSITIVE RESOURCE_COUNTER ARCHIVE_COUNTER')
sha = lambda raw: hashlib.sha256(raw).hexdigest()
labels = ('positive', 'resourceCountercontrol', 'archiveCountercontrol')
kinds = (None, 'resource-digest', 'archive-lock')
old_ids = ('1197e66c-c413-4514-a4e8-37e545aae2e8', '8c70ddc3-dc79-4f27-9127-8ba0f2c04551', '93cc755e-5732-40e9-b0a1-794028ee6644')
reports = {label: module.audit(run_id, kind) for label, run_id, kind in zip(labels, sys.argv[1:], kinds)}
findings = [{'packet': label, 'finding': item} for label, report in reports.items() for item in report['auditFailures']]
comparisons = {}
new_receipts = []
critical = ('packages/postgresql/native/catalog-report/resource-selection.sql',
            'packages/postgresql/native/catalog-report/configured-stage.sql',
            'packages/postgresql/native/catalog-report/release-selection.sql',
            'packages/python/src/truss/_native_catalog_report_sources.py',
            'packages/python/src/truss/_native_catalog_metadata.py',
            'packages/python/src/truss/_native_catalog_capture.py',
            'packages/python/tests/test_catalog_configured_release_stage_native.py',
            'scripts/check-python-catalog-report-release-native.py',
            'packages/python/src/truss/_profiles/catalog-report-release.json')
for label, old_id, new_id in zip(labels, old_ids, sys.argv[1:]):
    old_raw = (module.BASE / old_id / 'receipt.json').read_bytes()
    new_raw = (module.BASE / new_id / 'receipt.json').read_bytes()
    old, new = json.loads(old_raw), json.loads(new_raw)
    new_receipts.append(new)
    a, b = old['sourceDigests'], new['sourceDigests']
    changed = [{'path': p, 'oldSha256': a[p], 'newSha256': b[p]} for p in sorted(a.keys() & b.keys()) if a[p] != b[p]]
    critical_changed = [p for p in critical if a.get(str(module.ROOT / p)) != b.get(str(module.ROOT / p))]
    comparisons[label] = {'oldRunId': old_id, 'oldReceiptSha256': sha(old_raw), 'newRunId': new_id,
                           'newReceiptSha256': sha(new_raw), 'addedPaths': sorted(b.keys() - a.keys()),
                           'removedPaths': sorted(a.keys() - b.keys()), 'changedPaths': changed,
                           'criticalPathsCompared': list(critical), 'criticalPathsChanged': critical_changed,
                           'nativeBinaryPinsUnchanged': old['nativeBinaryDigests'] == new['nativeBinaryDigests']}
    if critical_changed or comparisons[label]['addedPaths'] or comparisons[label]['removedPaths']:
        findings.append({'packet': label, 'finding': 'unexpected critical path or capture-set change'})
same_sources = all(r['sourceDigests'] == new_receipts[0]['sourceDigests'] for r in new_receipts)
same_binaries = all(r['nativeBinaryDigests'] == new_receipts[0]['nativeBinaryDigests'] for r in new_receipts)
if not same_sources or not same_binaries:
    findings.append({'finding': 'final packets do not share original source/native pin maps'})
prior = Path('/private/tmp/astra-catalog-resources-audit.json')
result = {'auditKind': 'independent read-only merged configured resource retained evidence audit',
          'auditedAtUtc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
          'integrationRoot': str(module.ROOT), 'incomingMain': '9c54bd66',
          'status': 'scoped-evidence-matches' if not findings else 'findings',
          'executionsPerformed': 'Only local file/hash/ZIP/AST/log inspection; no tests, native execution, producers or repository edits.',
          'priorAuditPreserved': {'path': str(prior), 'sha256': sha(prior.read_bytes()), 'stage': 'pre-9c54bd66 resource checkpoint'},
          'sameFinalSourcePinMaps': same_sources, 'sameFinalNativePinMaps': same_binaries,
          'comparisonsToPreviousResourceCheckpoint': comparisons,
          **reports, 'findings': findings,
          'qualification': 'Merged private administrative configured-staging candidate and 48 selected positive tests with isolated omission controls only. No authenticated issuer, registered required authority producers, complete accepted report, installed-source authority cut or backend acceptance qualification.'}
output = Path('/private/tmp/astra-catalog-resources-merge-audit.json')
output.write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({'path': str(output), 'sha256': sha(output.read_bytes()), 'status': result['status'], 'findings': findings,
                  'changedPaths': {label: [p['path'] for p in diff['changedPaths']] for label, diff in comparisons.items()},
                  'packets': {label: {k: report[k] for k in ('runId', 'sourceCount', 'nativeBinaryCount', 'receiptSha256', 'zipSha256', 'status')} for label, report in reports.items()}}, indent=2))
