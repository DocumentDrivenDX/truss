"""Scoped source-node evidence; never native/exporter completeness qualification."""
import argparse
import hashlib
import json
from pathlib import Path

class AuditRefusal(ValueError):
    pass

def require(condition, message):
    if not condition:
        raise AuditRefusal(message)

root = Path('docs/helix')
parser = argparse.ArgumentParser()
parser.add_argument('--manifest', default=str(root / '02-design/models/truss-relationship-lineage-candidate.physical-ids.draft.json'))
parser.add_argument('--check-only', action='store_true')
args = parser.parse_args()
manifest = json.loads(Path(args.manifest).read_text())
def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()
require(sha(manifest['source']) == manifest['sourceSha256'], 'stale source')
require(sha(manifest['model']) == manifest['modelSha256'], 'stale model')
model = json.loads(Path(manifest['model']).read_text())
def resolve(pointer):
    value = model
    for part in pointer.split('/')[1:]:
        part = part.replace('~1', '/').replace('~0', '~')
        value = value[int(part)] if isinstance(value, list) else value[part]
    return value

def untag(value):
    # Inspect this pinned captured AST only; not a UMF conversion implementation.
    if value['kind'] == 'object':
        return {key: untag(item) for key, item in value['members'].items()}
    if value['kind'] == 'array':
        return [untag(item) for item in value['items']]
    return value.get('value')

prefix = 'truss.relationship-lineage.'
expected = {'table', 'primary-key', 'relationship-home-fk', 'category', 'profile-nonempty',
            'identity-nonempty', 'route-index', 'primary-key-index'}
columns = {'rel_type_id': 'int4', 'lineage_category': 'text', 'identity_profile': 'text',
           'original_identity_bytes': 'bytea', 'identity_sha256': 'bytea'}
expected.update('column.' + key for key in columns)
expected.update('not-null.' + key for key in list(columns)[1:4])
expected.add('generation.identity_sha256')
entries = manifest['entries']
require(len(entries) == len(expected) == 17, 'binding requirement at source line 42')
require({entry['id'] for entry in entries} == {prefix + key for key in expected}, 'binding requirement at source line 43')
by_id = {entry['id']: entry for entry in entries}
for entry in entries:
    locator = entry['capturedModelLocator']
    require(locator['model'] == manifest['model'] and locator['modelSha256'] == manifest['modelSha256'], 'binding requirement at source line 47')
    require(locator['generatedStatementOrdinal'] is None, 'binding requirement at source line 48')
    if entry.get('parent'):
        require(entry['parent'] in by_id, 'binding requirement at source line 50')
        parent_locator = by_id[entry['parent']]['capturedModelLocator']['jsonPointer']
        if entry['id'] != prefix + 'route-index':
            require(locator['jsonPointer'].startswith(parent_locator + '/members/'), 'source node outside declared parent')
    node = untag(resolve(locator['jsonPointer']))
    suffix = entry['id'][len(prefix):]
    if entry['kind'] != 'table':
        expected_parent = (prefix + 'column.' + suffix.split('.', 1)[1]
                           if suffix.startswith(('not-null.', 'generation.')) else prefix + 'table')
        require(entry['parent'] == expected_parent, 'unexpected physical owner')
    if entry['kind'] == 'table':
        require(node['relation']['schemaname'] == 'truss' and node['relation']['relname'] == entry['nativeName'], 'binding requirement at source line 61')
    elif entry['kind'] == 'column':
        require(node['colname'] == entry['nativeName'], 'binding requirement at source line 63')
        require(node['typeName']['names'][-1]['String']['sval'] == columns[entry['nativeName']], 'binding requirement at source line 64')
    elif suffix == 'route-index':
        require(node['idxname'] == entry['nativeName'] and node['relation']['relname'] == 'relationship_lineage', 'binding requirement at source line 66')
        require(not node.get('unique', False), 'binding requirement at source line 67')
        require([item['IndexElem']['name'] for item in node['indexParams']] == ['identity_sha256', 'rel_type_id'], 'binding requirement at source line 68')
    else:
        contype = ('CONSTR_PRIMARY' if suffix in ('primary-key', 'primary-key-index') else
                   'CONSTR_FOREIGN' if suffix == 'relationship-home-fk' else
                   'CONSTR_NOTNULL' if suffix.startswith('not-null.') else
                   'CONSTR_GENERATED' if suffix.startswith('generation.') else 'CONSTR_CHECK')
        require(node['contype'] == contype, 'binding requirement at source line 74')
        if entry.get('nativeName'):
            require(node['conname'] == entry['nativeName'], 'binding requirement at source line 76')
        if suffix == 'relationship-home-fk':
            require(node['pktable']['schemaname'] == 'truss' and node['pktable']['relname'] == 'rel_def', 'binding requirement at source line 78')
        if suffix.startswith('generation.'):
            call = node['raw_expr']['FuncCall']
            require([item['String']['sval'] for item in call['funcname']] == ['pg_catalog', 'sha256'], 'binding requirement at source line 81')
        if suffix == 'primary-key-index':
            require(locator['bindingKind'] == 'implicit-owned-source-basis', 'binding requirement at source line 83')
            require(locator['jsonPointer'] == by_id[prefix + 'primary-key']['capturedModelLocator']['jsonPointer'], 'binding requirement at source line 84')
require(manifest['complete'] is False, 'binding requirement at source line 85')
receipt = {'scope': manifest['scope'], 'entries': 17, 'sourceHashExact': True,
           'modelHashExact': True, 'sourceNodesResolved': 17, 'nativeNameTypeCorrespondenceChecked': True,
           'completePhysicalInventory': False, 'completeExporterCorrespondence': False, 'nativeQualified': False,
           'reproduce': 'python3 docs/helix/04-build/evidence/design-audit/check-relationship-lineage-bindings.py'}
if not args.check_only:
    (root / '04-build/evidence/design-audit/relationship-lineage-source-bindings.json').write_text(json.dumps(receipt, indent=2) + '\n')
print(json.dumps(receipt))
