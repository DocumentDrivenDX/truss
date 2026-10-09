"""Scoped stored-generated declaration correspondence; not a complete installer."""
import hashlib
import importlib.metadata
import importlib.resources
import json
from pathlib import Path
import subprocess
import tempfile
import pgserver

root = Path(__file__).resolve().parents[1]
manifest_path = 'docs/helix/04-build/evidence/design-audit/pgserver-native-object-declarations.json'
manifest = json.loads((root / manifest_path).read_text())
for source in manifest['sources']:
    assert hashlib.sha256((root / source['path']).read_bytes()).hexdigest() == source['sha256']

def expression(raw, native_type):
    assert native_type == 'bytea'
    call = raw['FuncCall']
    assert [n['String']['sval'] for n in call['funcname']] in (['pg_catalog', 'sha256'], ['sha256'])
    assert len(call['args']) == 1
    fields = call['args'][0]['ColumnRef']['fields']
    assert len(fields) == 1
    name = fields[0]['String']['sval']
    assert name.replace('_', '').isalnum()
    return 'sha256(' + name + ')'

expected = []
for obj in manifest['objects']:
    d = obj['definition']
    if obj['kind'] == 'CreateStmt':
        columns = [e['ColumnDef'] for e in d.get('tableElts', []) if 'ColumnDef' in e]
    elif obj['kind'] == 'AlterTableStmt':
        columns = [c['AlterTableCmd']['def']['ColumnDef'] for c in d['cmds'] if c['AlterTableCmd'].get('subtype') == 'AT_AddColumn']
    else:
        continue
    for column in columns:
        for item in column.get('constraints', []):
            constraint = item['Constraint']
            if constraint['contype'] == 'CONSTR_GENERATED':
                typename = column['typeName']['names'][-1]['String']['sval']
                assert constraint.get('generated_when') == 'a'
                expected.append([d['relation']['relname'], column['colname'], 's', expression(constraint['raw_expr'], typename)])
expected.sort()
assert len(expected) == 29 and len({tuple(row[:2]) for row in expected}) == 29
paths = ['docs/helix/04-build/evidence/source-epoch-layout-0.16.owner-export.sql', 'docs/helix/04-build/evidence/operation-configuration-storage.owner-export.sql', 'docs/helix/04-build/evidence/layout-migration-storage.owner-export.sql']
originals = [(root / p).read_bytes() for p in paths]
assert importlib.metadata.version('pgserver') == '0.1.4'
psql = Path(str(importlib.resources.files('pgserver'))) / 'pginstall/bin/psql'
with tempfile.TemporaryDirectory(prefix='truss-default-declarations-') as directory:
    server = pgserver.get_server(Path(directory) / 'data', cleanup_mode='stop')
    def query(sql):
        return subprocess.check_output([str(psql), server.get_uri(), '-X', '-q', '-A', '-t', '-v', 'ON_ERROR_STOP=1'], input=sql, text=True, timeout=60).strip()
    try:
        version = query('SHOW server_version;'); assert version == '16.2'
        sql = "SELECT coalesce(json_agg(json_build_array(c.relname,a.attname,a.attgenerated,pg_get_expr(d.adbin,d.adrelid)) ORDER BY c.relname,a.attname),'[]') FROM pg_attrdef d JOIN pg_class c ON c.oid=d.adrelid JOIN pg_namespace n ON n.oid=c.relnamespace JOIN pg_attribute a ON a.attrelid=c.oid AND a.attnum=d.adnum WHERE n.nspname='truss' AND a.attgenerated<>'';"
        observed = json.loads(query('BEGIN;\n' + b';\n'.join(originals).decode() + ';\n' + sql + '\nROLLBACK;'))
        if observed != expected:
            raise ValueError(json.dumps({'expected': expected, 'observed': observed}))
        assert query("SELECT to_regnamespace('truss') IS NULL;") == 't'
    finally:
        server.cleanup()
receipt = dict(scope='Original generated expression declaration/storage-mode/native deparse correspondence only; no full installer qualification', serverVersion=version, generatedColumns=len(expected), expected=expected, observed=observed, rollbackRemovedNamespace=True, sources={p:hashlib.sha256(b).hexdigest() for p,b in zip(paths,originals)}, declarationCaptureSha256=hashlib.sha256((root / manifest_path).read_bytes()).hexdigest(), producerSha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), limitations=['Populated generated-value evaluation, function permissions/dependencies and write-path enforcement not qualified', 'No full routine/grant/initializer or ready marker', 'Scoped AST inventory comparison, not another UMF DDL generator'])
(root / 'docs/helix/04-build/evidence/design-audit/pgserver-generated-declaration-component.json').write_text(json.dumps(receipt, indent=2)+'\n')
print(json.dumps(dict(serverVersion=version, generatedColumns=len(expected), rollbackRemovedNamespace=True)))
