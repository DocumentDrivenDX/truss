"""Independent ordered receipt composition, preserving full native AST meaning."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
BASE = ROOT / 'docs/helix/04-build/evidence/design-audit'
def load(pin):
    b = (ROOT / pin['path']).read_bytes()
    if hashlib.sha256(b).hexdigest() != pin['sha256']:
        raise ValueError('source pin mismatch: ' + pin['path'])
    return json.loads(b)
def decode(node):
    if node['kind'] == 'object':
        return {k: decode(v) for k, v in node['members'].items()}
    if node['kind'] == 'array':
        return [decode(v) for v in node['items']]
    return json.loads(node['value']) if node['kind'] == 'number' else node.get('value')
def strip(node):
    if isinstance(node, dict):
        return {k: strip(v) for k, v in node.items() if k not in ('location','stmt_location','stmt_len')}
    if isinstance(node, list):
        return [strip(v) for v in node]
    return node
receipt = json.loads((BASE / 'request-receipt-layout-profile-composition.json').read_bytes())
expected = []
for pin in receipt['inputs']:
    model = load(pin)
    expected.extend(decode(model['modules'][0]['elements'][0]['extensions']['umf.postgresql']['root'])['stmts'])
for node in expected:
    if node['stmt'].get('CommentStmt', {}).get('objtype') == 'OBJECT_SCHEMA':
        node['stmt']['CommentStmt']['comment'] = 'truss-layout weft-review-0.11 REVIEW ONLY - unqualified'
for field in ('model','sql','ast'):
    load_pin = {'path':receipt[field+'Path'], 'sha256':receipt[field+'Sha256']}
    b = (ROOT / load_pin['path']).read_bytes()
    if hashlib.sha256(b).hexdigest() != load_pin['sha256']:
        raise ValueError('output pin mismatch')
actual = json.loads((ROOT / receipt['astPath']).read_bytes())
if strip(actual) != strip(expected):
    raise ValueError('ordered full-AST composition mismatch')
tables = [n['stmt']['CreateStmt'] for n in actual if 'CreateStmt' in n['stmt']]
columns_by_table = {t['relation']['relname']: [c['ColumnDef']['colname'] for c in t['tableElts'] if 'ColumnDef' in c] for t in tables}
for node in actual:
    alter = node['stmt'].get('AlterTableStmt')
    if alter is not None:
        for command in alter.get('cmds', []):
            command = command['AlterTableCmd']
            if command['subtype'] == 'AT_AddColumn':
                columns_by_table[alter['relation']['relname']].append(command['def']['ColumnDef']['colname'])
if any(len(cols) != len(set(cols)) for cols in columns_by_table.values()):
    raise ValueError('duplicate declared column')
columns = sum(map(len, columns_by_table.values()))
names = [t['relation']['relname'] for t in tables]
if len(names) != len(set(names)):
    raise ValueError('duplicate relation')
result = {'scope':'ordered complete source AST plus output custody; no native installation or replay qualification',
          'statements':len(actual),'tables':len(tables),'columns':columns,
          'addedTables':names[-3:],'indexes':sum('IndexStmt' in n['stmt'] for n in actual),
          'sequences':sum('CreateSeqStmt' in n['stmt'] for n in actual),
          'columnCountScope':'CREATE TABLE plus ALTER TABLE ADD COLUMN, not ALTER TYPE replacement nodes',
          'nativeQualified':False,'installationReady':False}
(BASE / 'request-receipt-layout-profile-independent.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result))
