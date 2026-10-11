"""Read-only retained-evidence audit; never imports repository code or runs tests/native tools."""
import ast
import collections
import datetime
import hashlib
import json
from pathlib import Path
import re
import sys
import zipfile

ROOT = Path('/private/tmp/truss-security-main-integration')
BASE = ROOT / 'docs/helix/04-build/evidence/python-catalog-report-release'
OUTPUT = Path('/private/tmp/astra-catalog-resources-audit.json')
sha = lambda raw: hashlib.sha256(raw).hexdigest()
archive_failures = {
    'test_concurrent_archive_writes_excluded_until_transaction_end',
    'test_later_rollback_and_savepoint_release_preserve_archive_cut',
    'test_preexisting_archive_writer_refuses_without_waiting',
    'test_rollback_across_selection_releases_archive_cut_same_xid',
}
resource_failures = {
    'test_resource_archive_damage_refuses_before_first_catalog_effect',
    'test_same_writer_resource_change_during_effect_refuses_and_rolls_back',
}

def audit(run_id, kind):
    folder = BASE / run_id
    raw_receipt = (folder / 'receipt.json').read_bytes()
    receipt = json.loads(raw_receipt)
    pins = receipt['sourceDigests']
    failures = []
    def require(condition, label):
        if not condition:
            failures.append(label)
    out = {'runId': run_id, 'countercontrolKind': kind,
           'receiptSha256': sha(raw_receipt),
           'zipSha256': sha((folder / 'sources.zip').read_bytes()),
           'receiptStatus': receipt['status'], 'auditFailures': failures}
    require(receipt['runId'] == run_id, 'receipt run identity')
    require(receipt['status'] == ('component-passed' if kind is None else 'countercontrol-reproduced'), 'receipt status')
    require(receipt.get('countercontrol') is (kind is not None), 'countercontrol Boolean')
    require(receipt.get('countercontrolKind') == kind, 'countercontrol kind')
    require(type(receipt['testExitCode']) is int and receipt['testExitCode'] == (0 if kind is None else 1), 'test exit code')
    require(receipt['nativeTests'] == 19, 'receipt native population')
    current_mismatches = [p for p, digest in pins.items() if not Path(p).is_file() or sha(Path(p).read_bytes()) != digest]
    out.update(sourceCount=len(pins), currentSourceMismatches=current_mismatches)
    require(len(pins) == 271 and not current_mismatches, '271 current source/dependency pins')
    with zipfile.ZipFile(folder / 'sources.zip') as archive:
        names = archive.namelist()
        expected_names = {p.lstrip('/') for p in pins}
        duplicates = len(names) - len(set(names))
        extra = sorted(set(names) - expected_names)
        missing = sorted(expected_names - set(names))
        bad = [p for p, digest in pins.items() if p.lstrip('/') in names and sha(archive.read(p.lstrip('/'))) != digest]
        out['zip'] = {'entryCount': len(names), 'duplicates': duplicates, 'extra': extra, 'missing': missing, 'digestMismatches': bad}
        require(not (duplicates or extra or missing or bad) and len(names) == len(pins), 'exact original ZIP closure')
        def original(relative):
            return archive.read(str(ROOT / relative).lstrip('/'))
        def methods(module, selected_class=None):
            tree = ast.parse(original('packages/python/tests/' + module + '.py'))
            return [f'{module}.{cls.name}.{f.name}' for cls in tree.body if isinstance(cls, ast.ClassDef)
                    and (selected_class is None or cls.name == selected_class)
                    for f in cls.body if isinstance(f, ast.FunctionDef) and f.name.startswith('test_')]
        release = methods('test_catalog_report_release_native') + methods('test_catalog_configured_release_stage_native')
        dispatch = methods('test_native_catalog_dispatch', 'NativeCatalogDispatchTests')
        auxiliary = methods('test_catalog_source_candidate') + methods('test_configured_catalog_stage')
        require(len(release) == 19 and len(dispatch) == 14 and len(auxiliary) == 15, 'frozen AST inventories 19/14/15')
        require(receipt['originalCatalogRegressions'] == [n.rsplit('.', 1)[1] for n in dispatch], 'receipt dispatch order equals AST')
        require(receipt['incomingCatalogRegressions'] == (auxiliary if kind is None else []), 'receipt auxiliary inventory equals AST/explicit omission')
        policy = json.loads(original('packages/python/src/truss/_profiles/catalog-report-release.json'))
        resources = []
        for entry in policy['resources']:
            path = str(ROOT / entry['path'])
            body = original(entry['path'])
            resources.append({'path': entry['path'], 'bytes': len(body), 'sha256': sha(body),
                              'policyHashMatches': sha(body) == entry['sha256'],
                              'sourcePinMatches': pins.get(path) == sha(body),
                              'currentMatches': Path(path).read_bytes() == body})
        out['declaredResources'] = {'count': len(resources), 'uniquePaths': len({r['path'] for r in resources}),
                                    'totalBytes': sum(r['bytes'] for r in resources), 'rows': resources}
        require(len(resources) == 21 and len({r['path'] for r in resources}) == 21, '21 unique declared resources')
        require(sum(r['bytes'] for r in resources) == 101453 and all(r['policyHashMatches'] and r['sourcePinMatches'] and r['currentMatches'] for r in resources), 'all declared resource bytes/hash/ZIP/current correspondence')
        package_files = [p for p in (ROOT / 'packages/python/src/truss').rglob('*') if p.is_file() and '__pycache__' not in p.parts]
        uncaptured = [str(p) for p in package_files if str(p) not in pins]
        out['currentPythonPackageFileCount'] = len(package_files)
        out['uncapturedCurrentPythonPackageFiles'] = uncaptured
        require(not uncaptured, 'whole current Python package closure')
        dep_counts = {}
        for package in ('pg8000', 'scramp', 'asn1crypto', 'dateutil', 'six'):
            selected = [p for p in pins if (package in Path(p).parts and p.endswith('.py')) or (package == 'six' and Path(p).name == 'six.py')]
            distribution = 'python_dateutil' if package == 'dateutil' else package
            metadata = [p for p in pins if Path(p).name == 'METADATA' and Path(p).parent.name.startswith(distribution + '-')]
            versions = []
            for p in metadata:
                m = re.search(rb'^Version: (.+)$', archive.read(p.lstrip('/')), re.M)
                versions.append(m.group(1).decode() if m else None)
            dep_counts[package] = {'pythonFiles': len(selected), 'metadataFiles': len(metadata), 'versions': versions}
            require(bool(selected) and len(metadata) == 1, 'captured dependency ' + package)
        out['dependencies'] = dep_counts
        codec = str(ROOT / 'packages/postgresql/native/canonical-tree-bytes.sql')
        require(codec in pins, 'native tree codec pinned')
        release_sql = original('packages/postgresql/native/catalog-report/release-selection.sql')
        resource_sql = original('packages/postgresql/native/catalog-report/resource-selection.sql')
        require(receipt['executedReleaseSqlSha256'] == sha(release_sql if kind != 'archive-lock' else release_sql.replace(b' LOCK TABLE truss.installation_archive IN SHARE MODE NOWAIT;', b' -- Deliberate negative control: archive table lock omitted.')), 'executed release SQL hash')
        if kind is not None:
            if kind == 'archive-lock':
                base = release_sql
                marker = b' LOCK TABLE truss.installation_archive IN SHARE MODE NOWAIT;'
                replacement = b' -- Deliberate negative control: archive table lock omitted.'
                variant_path = folder / 'countercontrol-release-selection.sql'
            else:
                base = resource_sql
                marker = b'  IF NOT EXISTS(SELECT 1 FROM truss.installation_archive a WHERE a.archive_row_id=row.archive_row_id'
                replacement = b'  IF FALSE AND NOT EXISTS(SELECT 1 FROM truss.installation_archive a WHERE a.archive_row_id=row.archive_row_id'
                variant_path = folder / 'countercontrol-resource-selection.sql'
            variant = variant_path.read_bytes()
            out['counterVariant'] = {'path': str(variant_path), 'originalSha256': sha(base), 'variantSha256': sha(variant),
                                     'markerCount': base.count(marker), 'exactSingleReplacement': variant == base.replace(marker, replacement)}
            require(base.count(marker) == 1 and variant == base.replace(marker, replacement), 'exact single omission variant')
    def group(prefix, expected, expected_failures):
        stderr = (folder / (prefix + '.stderr.log')).read_text()
        records = re.findall(r'^test_\S+ \(([^)]+)\) \.\.\. (ok|FAIL|ERROR|skipped[^\n]*)$', stderr, re.M)
        names = [name for name, result in records]
        observed_failures = {name.rsplit('.', 1)[1] for name, result in records if result == 'FAIL'}
        result = {'expectedCount': len(expected), 'observedCount': len(records), 'expectedMethods': expected,
                  'results': dict(records), 'missing': sorted(set(expected) - set(names)), 'extra': sorted(set(names) - set(expected)),
                  'duplicateCount': len(names) - len(set(names)), 'notRaisedCount': stderr.count('DatabaseError not raised'),
                  'failureMethods': sorted(observed_failures), 'summary': re.findall(r'^(?:Ran \d+ tests.*|OK|FAILED \(.*\))$', stderr, re.M)}
        require(len(names) == len(expected) and set(names) == set(expected), prefix + ' exact AST/log method inventory')
        require(observed_failures == expected_failures, prefix + ' exact intended failure methods')
        require(all(status == ('FAIL' if name.rsplit('.', 1)[1] in expected_failures else 'ok') for name, status in records), prefix + ' exact statuses/no errors/skips')
        require(stderr.count('DatabaseError not raised') == len(expected_failures), prefix + ' exact omission assertion count')
        require(re.search(r'^Ran ' + str(len(expected)) + r' tests in ', stderr, re.M) is not None, prefix + ' anchored population summary')
        require((f'FAILED (failures={len(expected_failures)})' if expected_failures else 'OK') in stderr.splitlines(), prefix + ' terminal summary')
        return result
    out['methodGroups'] = {'release': group('tests', release, set() if kind is None else archive_failures if kind == 'archive-lock' else resource_failures),
                           'dispatch': group('regression', dispatch, set())}
    if kind is None:
        out['methodGroups']['auxiliary'] = group('auxiliary', auxiliary, set())
    else:
        auxiliary_present = [p.name for p in folder.glob('auxiliary.*.log')]
        out['auxiliaryLogFiles'] = auxiliary_present
        require(not auxiliary_present, 'countercontrol has no auxiliary execution/logs')
    out['logs'] = {p.name: sha(p.read_bytes()) for p in folder.glob('*.log')}
    out['boundaries'] = (folder / 'boundaries.stdout.log').read_text().strip()
    out['nativeBinaryCount'] = len(receipt['nativeBinaryDigests'])
    binary_bad = [p for p, digest in receipt['nativeBinaryDigests'].items() if not Path(p).is_file() or sha(Path(p).read_bytes()) != digest]
    out['currentNativeBinaryMismatches'] = binary_bad
    require(len(receipt['nativeBinaryDigests']) == 1614 and not binary_bad, '1614 current native binary pins')
    cleanup = receipt['cleanup']
    execution = Path(receipt['testCommand'][5]).parents[3]
    server = (folder / 'server.log').read_text()
    socket_match = re.search(r'listening on Unix socket "([^"]+)"', server)
    socket = Path(socket_match.group(1)) if socket_match else None
    out['cleanup'] = {'receipt': cleanup, 'executionDirectory': str(execution), 'executionDirectoryAbsent': not execution.exists(),
                      'socketPath': str(socket) if socket else None, 'socketAbsent': socket is not None and not socket.exists(),
                      'socketParentAbsent': socket is not None and not socket.parent.exists(),
                      'serverShutdownLogged': re.search(r'LOG:  database system is shut down\s*$', server) is not None}
    require(cleanup == {'attempted': True, 'stopExitCode': 0, 'statusExitCode': 3, 'socketAbsent': True}, 'receipt owned cleanup')
    require(not execution.exists() and socket is not None and not socket.exists() and not socket.parent.exists(), 'owned fixture paths absent')
    require(out['cleanup']['serverShutdownLogged'], 'terminal server shutdown log')
    require((folder / 'receipt.json').read_bytes() == raw_receipt, 'receipt unchanged through audit')
    out['status'] = 'scoped-evidence-matches' if not failures else 'findings'
    return out

if __name__ == '__main__':
    if len(sys.argv) != 4:
        raise SystemExit('Usage: audit.py POSITIVE RESOURCE_COUNTER ARCHIVE_COUNTER')
    reports = {label: audit(run_id, kind) for label, run_id, kind in
               zip(('positive', 'resourceCountercontrol', 'archiveCountercontrol'), sys.argv[1:], (None, 'resource-digest', 'archive-lock'))}
    findings = [{'packet': name, 'finding': item} for name, report in reports.items() for item in report['auditFailures']]
    prior = Path('/private/tmp/astra-configured-catalog-d42-audit.json')
    result = {'auditKind': 'independent read-only declared-resource native retained evidence audit',
              'auditedAtUtc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'integrationRoot': str(ROOT),
              'status': 'scoped-evidence-matches' if not findings else 'findings',
              'executionsPerformed': 'Only local file/hash/ZIP/AST/log inspection; no tests, native execution, producers or source edits.',
              'priorAuditPreserved': {'path': str(prior), 'sha256': sha(prior.read_bytes()), 'stage': 'pre-declared-resource increment'},
              **reports, 'findings': findings,
              'qualification': 'Private administrative configured-staging candidate, exact retained source/dependency/native inputs and selected controls only. No authenticated issuer, registered required authority producers, complete accepted report, installed-source authority cut or backend acceptance qualification.'}
    OUTPUT.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'path': str(OUTPUT), 'sha256': sha(OUTPUT.read_bytes()), 'status': result['status'], 'findings': findings,
                      'packets': {name: {k: report[k] for k in ('runId', 'sourceCount', 'nativeBinaryCount', 'receiptSha256', 'zipSha256', 'status')} for name, report in reports.items()}}, indent=2))
