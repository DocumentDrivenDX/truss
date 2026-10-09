#!/usr/bin/env python3
"""Rollback-only composition probe of original base, adjunct DDL and immutable guards on pgserver."""
import hashlib
import importlib.metadata
import importlib.resources
import json
from pathlib import Path
import re
from collections import Counter
import subprocess
import tempfile

import pgserver

root = Path(__file__).resolve().parents[1]
paths = [
 'docs/helix/04-build/evidence/source-epoch-layout-0.16.owner-export.sql',
 'docs/helix/04-build/evidence/operation-configuration-storage.owner-export.sql',
 'docs/helix/04-build/evidence/layout-migration-storage.owner-export.sql',
 'packages/postgresql/native/operation-configuration-immutability.sql',
 'packages/postgresql/native/layout-migration-receipt-immutability.sql',
]
originals = [(root / path).read_bytes() for path in paths]
original = b';\n'.join(originals)
structural_path = root / 'docs/helix/02-design/models/truss-layout-core-structural-0.6.proposal.umf.json'
structural_bytes = structural_path.read_bytes()
model = json.loads(structural_bytes)
module = model['modules'][0]
elements = {e['id']: e for e in module['elements']}
records = [e for e in module['elements'] if e['kind'] == 'record']
expected = [r['name'] for r in records]
expected_columns = {}
for record in records:
    columns = []
    for ref in record['members']:
        assert ref['module'] == module['id']
        field = elements[ref['element']]
        native = field['extensions']['truss.layout.native']['nativeType']
        typname = native['names'][-1]['String']['sval']
        if native.get('arrayBounds'):
            typname = '_' + typname
        typmod = -1
        if native.get('typmods'):
            assert typname == 'bpchar' and len(native['typmods']) == 1, 'Unadmitted type modifier profile'
            length = native['typmods'][0]['A_Const']['ival']['ival']
            assert isinstance(length, int) and not isinstance(length, bool) and 1 <= length <= 10485760
            # PostgreSQL16 anychar_typmodin includes the four-byte varlena header.
            typmod = length + 4
        declaration = field['extensions']['truss.layout.native'].get('collation')
        collation = ['pg_catalog', 'default'] if typname in ('text', 'bpchar') else None
        if declaration:
            collation = [v['String']['sval'] for v in declaration['collname']]
            if len(collation) == 1:
                assert collation == ['C'], 'Unadmitted unqualified collation'
                # This fresh-cluster probe admits only implicit pg_catalog.C.
                collation = ['pg_catalog', 'C']
            assert len(collation) == 2, 'Original qualified collation required'
        columns.append([field['name'], typname, field['nullability'] == 'required', len(native.get('arrayBounds', [])), typmod, collation])
    expected_columns[record['name']] = columns
expected_fks = []
# Scoped native AST inventory comparison, not a UMF or SQL validator.
# PostgreSQL16 transformConstraintAttrs attaches these separate ColumnDef
# attribute nodes to the preceding FK. Retain original descriptors unchanged.
def fk_definition(relation):
    definition = relation.get('nativeCorrespondence', {}).get('definition', relation.get('definition'))
    normalized = dict(definition)
    pointer = relation.get('nativeCorrespondence', {}).get('sourcePointer', relation.get('sourcePointer', ''))
    if not pointer.endswith('/ColumnDef'):
        return normalized
    refs = relation['fieldCorrespondence']
    assert len(refs) == 1, 'Unadmitted compound column FK'
    field = elements[refs[0]['source']['element']]
    native = field['extensions']['truss.layout.native']
    assert native['sourcePointer'] == pointer
    constraints = [entry['Constraint'] for entry in native['constraints']]
    indices = [i for i, entry in enumerate(constraints) if entry == definition]
    assert len(indices) == 1, 'Original column FK node correspondence required'
    attrs = []
    for entry in constraints[indices[0]+1:]:
        if not entry['contype'].startswith('CONSTR_ATTR_'):
            break
        attrs.append(entry['contype'])
    assert len(attrs) == len(set(attrs))
    assert not {'CONSTR_ATTR_DEFERRABLE', 'CONSTR_ATTR_NOT_DEFERRABLE'} <= set(attrs)
    assert not {'CONSTR_ATTR_DEFERRED', 'CONSTR_ATTR_IMMEDIATE'} <= set(attrs)
    for kind in attrs:
        assert kind in {'CONSTR_ATTR_DEFERRABLE', 'CONSTR_ATTR_NOT_DEFERRABLE', 'CONSTR_ATTR_DEFERRED', 'CONSTR_ATTR_IMMEDIATE'}
    if 'CONSTR_ATTR_DEFERRABLE' in attrs:
        normalized['deferrable'] = True
    if 'CONSTR_ATTR_NOT_DEFERRABLE' in attrs:
        normalized['deferrable'] = False
    if 'CONSTR_ATTR_DEFERRED' in attrs:
        normalized['initdeferred'] = True
        assert 'CONSTR_ATTR_NOT_DEFERRABLE' not in attrs
        normalized['deferrable'] = True
    if 'CONSTR_ATTR_IMMEDIATE' in attrs:
        normalized['initdeferred'] = False
    return normalized

def retain_fk(source, target, correspondence, definition):
    expected_fks.append([source, target,
        [elements[c['source']['element']]['name'] for c in correspondence],
        [elements[c['target']['element']]['name'] for c in correspondence],
        definition['fk_matchtype'], definition['fk_upd_action'], definition['fk_del_action'],
        definition.get('deferrable', False), definition.get('initdeferred', False), definition['initially_valid']])
for relation in module['relationships']:
    retain_fk(relation['source'][0]['element'], relation['target'][0]['element'], relation['fieldCorrespondence'], fk_definition(relation))
for record in records:
    for relation in record.get('extensions', {}).get('truss.layout.native', {}).get('physicalForeignKeys', []):
        target = relation.get('target', [{}])[0].get('element')
        if target is None:
            target = relation['definition']['pktable']['relname']
        retain_fk(record['name'], target, relation['fieldCorrespondence'], fk_definition(relation))
declarations_path = root / 'docs/helix/04-build/evidence/design-audit/pgserver-native-object-declarations.json'
declarations_bytes = declarations_path.read_bytes()
declarations = json.loads(declarations_bytes)
for source in declarations['sources']:
    assert hashlib.sha256((root / source['path']).read_bytes()).hexdigest() == source['sha256'], 'Stale original declaration capture'
expected_sequences = {}
for obj in declarations['objects']:
    if obj['kind'] != 'CreateSeqStmt':
        continue
    definition = obj['definition']
    relation = definition['sequence']
    assert relation['schemaname'] == 'truss' and relation['relpersistence'] == 'p'
    # Scoped ascending int8 declarations. PostgreSQL16 documented defaults:
    # https://www.postgresql.org/docs/16/sql-createsequence.html
    values = {'as': 'int8', 'increment': '1', 'minvalue': '1',
              'maxvalue': '9223372036854775807', 'start': '1', 'cache': '1', 'cycle': False}
    seen = set()
    for entry in definition.get('options', []):
        option = entry['DefElem']; name = option['defname']; arg = option['arg']
        assert name in values and name not in seen, 'Unadmitted sequence option'
        seen.add(name)
        if name == 'as':
            names = [v['String']['sval'] for v in arg['TypeName']['names']]
            assert names == ['pg_catalog', 'int8']
        elif name == 'cycle':
            values[name] = arg['Boolean']['boolval']
            assert isinstance(values[name], bool)
        elif 'Integer' in arg:
            value = arg['Integer']['ival']
            assert isinstance(value, int) and not isinstance(value, bool)
            values[name] = str(value)
        else:
            value = arg['Float']['fval']
            assert re.fullmatch(r'-?[0-9]+', value), 'Exact integer token required'
            values[name] = str(int(value))
    assert values['increment'] == '1' and values['as'] == 'int8', 'Unadmitted sequence default profile'
    assert relation['relname'] not in expected_sequences
    expected_sequences[relation['relname']] = values
if importlib.metadata.version('pgserver') != '0.1.4':
    raise SystemExit('Expected pinned pgserver0.1.4')
psql = Path(str(importlib.resources.files('pgserver'))) / 'pginstall/bin/psql'
with tempfile.TemporaryDirectory(prefix='truss-pgserver-layout-') as directory:
    server = pgserver.get_server(Path(directory) / 'data', cleanup_mode='stop')
    def query(sql):
        return subprocess.check_output(
            [str(psql), server.get_uri(), '-X', '-q', '-A', '-t', '-v', 'ON_ERROR_STOP=1'],
            input=sql, text=True, timeout=60).strip()
    try:
        # No schema replacement, substituted SQL or installed publication.
        probe = '''
DO $$
DECLARE mode text; relation text;
BEGIN
 FOREACH mode IN ARRAY ARRAY['origin','replica'] LOOP
  PERFORM set_config('session_replication_role',mode,true);
  FOREACH relation IN ARRAY ARRAY['operation_configuration','layout_migration_receipt'] LOOP
   BEGIN
    EXECUTE format('TRUNCATE truss.%I',relation);
    RAISE EXCEPTION 'immutable truncate did not refuse' USING ERRCODE='P0001';
   EXCEPTION WHEN SQLSTATE '55000' THEN NULL;
   END;
  END LOOP;
 END LOOP;
 PERFORM set_config('session_replication_role','origin',true);
END $$;
SELECT json_build_object(
 'sequences',(SELECT json_object_agg(c.relname,json_build_object(
  'as',t.typname,'increment',q.seqincrement::text,'minvalue',q.seqmin::text,
  'maxvalue',q.seqmax::text,'start',q.seqstart::text,'cache',q.seqcache::text,'cycle',q.seqcycle))
 FROM pg_sequence q JOIN pg_class c ON c.oid=q.seqrelid
 JOIN pg_namespace n ON n.oid=c.relnamespace JOIN pg_type t ON t.oid=q.seqtypid
 WHERE n.nspname='truss'),
 'tables',(SELECT json_agg(c.relname ORDER BY c.relname) FROM pg_class c
 JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='truss' AND c.relkind IN ('r','p')),
 'serverVersion',current_setting('server_version'),
 'sha256',to_regprocedure('pg_catalog.sha256(bytea)') IS NOT NULL,
 'xactStatus',to_regprocedure('pg_catalog.pg_xact_status(xid8)') IS NOT NULL,
 'currentXid',to_regprocedure('pg_catalog.pg_current_xact_id_if_assigned()') IS NOT NULL,
 'uuidIssuer',to_regprocedure('pg_catalog.gen_random_uuid()') IS NOT NULL,
 'typeNamespaces',(SELECT json_agg(DISTINCT tn.nspname) FROM pg_attribute a
 JOIN pg_class c ON c.oid=a.attrelid JOIN pg_namespace n ON n.oid=c.relnamespace
 JOIN pg_type ty ON ty.oid=a.atttypid JOIN pg_namespace tn ON tn.oid=ty.typnamespace
 WHERE n.nspname='truss' AND c.relkind IN ('r','p') AND a.attnum>0 AND NOT a.attisdropped),
 'fkTargetNamespaces',(SELECT json_agg(DISTINCT pn.nspname) FROM pg_constraint k
 JOIN pg_class c ON c.oid=k.conrelid JOIN pg_namespace n ON n.oid=c.relnamespace
 JOIN pg_class p ON p.oid=k.confrelid JOIN pg_namespace pn ON pn.oid=p.relnamespace
 WHERE n.nspname='truss' AND k.contype='f' AND k.conparentid=0),
 'columns',(SELECT json_object_agg(t.relname,t.columns) FROM
 (SELECT c.relname,json_agg(json_build_array(a.attname,ty.typname,a.attnotnull,a.attndims,a.atttypmod,
 CASE WHEN a.attcollation=0 THEN NULL ELSE json_build_array(cn.nspname,co.collname) END) ORDER BY a.attnum) AS columns
 FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
 JOIN pg_attribute a ON a.attrelid=c.oid JOIN pg_type ty ON ty.oid=a.atttypid
 LEFT JOIN pg_collation co ON co.oid=a.attcollation LEFT JOIN pg_namespace cn ON cn.oid=co.collnamespace
 WHERE n.nspname='truss' AND c.relkind IN ('r','p') AND a.attnum>0 AND NOT a.attisdropped
 GROUP BY c.relname) t),
 'foreignKeys',(SELECT json_agg(json_build_array(c.relname,p.relname,
  (SELECT json_agg(a.attname ORDER BY u.ord) FROM unnest(k.conkey) WITH ORDINALITY u(num,ord)
   JOIN pg_attribute a ON a.attrelid=k.conrelid AND a.attnum=u.num),
  (SELECT json_agg(a.attname ORDER BY u.ord) FROM unnest(k.confkey) WITH ORDINALITY u(num,ord)
   JOIN pg_attribute a ON a.attrelid=k.confrelid AND a.attnum=u.num),
  k.confmatchtype,k.confupdtype,k.confdeltype,k.condeferrable,k.condeferred,k.convalidated))
 FROM pg_constraint k JOIN pg_class c ON c.oid=k.conrelid JOIN pg_class p ON p.oid=k.confrelid
 JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='truss' AND k.contype='f' AND k.conparentid=0),
 'adjuncts',(SELECT json_object_agg(c.relname,json_build_object(
  'columns',(SELECT count(*) FROM pg_attribute a WHERE a.attrelid=c.oid AND a.attnum>0 AND NOT a.attisdropped),
  'foreignKeys',(SELECT count(*) FROM pg_constraint k WHERE k.conrelid=c.oid AND k.contype='f'),
  'generatedHashes',(SELECT count(*) FROM pg_attribute a WHERE a.attrelid=c.oid AND a.attgenerated='s'),
  'alwaysGuards',(SELECT count(*) FROM pg_trigger t WHERE t.tgrelid=c.oid AND NOT t.tgisinternal AND t.tgenabled='A'),
  'publicInsert',has_table_privilege('public',c.oid,'INSERT')))
  FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='truss'
  AND c.relname IN ('operation_configuration','layout_migration_receipt')),
 'transactionTimeout',current_setting('transaction_timeout',true));
ROLLBACK;
'''
        observed = json.loads(query('BEGIN;\n' + original.decode('utf-8') + ';\n' + probe))
        assert observed['sequences'] == expected_sequences, 'Original sequence configuration discrepancy'
        assert observed['tables'] == sorted(expected), (observed['tables'], expected)
        assert all(observed[k] for k in ['sha256', 'xactStatus', 'currentXid', 'uuidIssuer'])
        assert observed['typeNamespaces'] == ['pg_catalog']
        assert observed['fkTargetNamespaces'] == ['truss']
        assert observed['columns'] == expected_columns, 'UMF column/type/requiredness discrepancy'
        frozen = lambda values: Counter(json.dumps(v, separators=(',', ':')) for v in values)
        if frozen(observed['foreignKeys']) != frozen(expected_fks):
            print(json.dumps({'missingExpected': list((frozen(expected_fks)-frozen(observed['foreignKeys'])).elements()), 'unexpectedNative': list((frozen(observed['foreignKeys'])-frozen(expected_fks)).elements())}))
            raise AssertionError('UMF ordered FK correspondence discrepancy')
        assert observed['adjuncts'] == {
            'operation_configuration': {'columns': 16, 'foreignKeys': 2, 'generatedHashes': 3, 'alwaysGuards': 2, 'publicInsert': False},
            'layout_migration_receipt': {'columns': 11, 'foreignKeys': 1, 'generatedHashes': 3, 'alwaysGuards': 2, 'publicInsert': False},
        }, observed['adjuncts']
        assert query("SELECT to_regnamespace('truss') IS NULL;") == 't'
    finally:
        server.cleanup()
receipt = {'scope': 'Original generated base/adjunct DDL and immutable guard composition, UMF core column/type/requiredness and ordered physical FK and sequence configuration correspondence plus independent adjunct catalog expectations under rollback only; no complete installer, routine/grant inventory, accepted catalog or migration qualification',
           'pgserverVersion': '0.1.4', 'declarationCaptureSha256': hashlib.sha256(declarations_bytes).hexdigest(), 'structuralModel': str(structural_path.relative_to(root)), 'structuralSha256': hashlib.sha256(structural_bytes).hexdigest(), 'sources': [{'path': path, 'sha256': hashlib.sha256(value).hexdigest()} for path, value in zip(paths, originals)], 'observation': observed,
           'rollbackRemovedNamespace': True, 'truncateRefusals': 4, 'truncateModes': ['origin', 'replica'],
           'unverifiedStructure': ['collation implementation/version semantics', 'default and check expression meaning', 'complete indexes/routines/grants'],
           'limitation': 'PostgreSQL16.2 lacks transaction_timeout; any selected profile requiring that setting must refuse or use a separately admitted bounded alternative',
           'producerSha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
(root / 'docs/helix/04-build/evidence/design-audit/pgserver-umf-structural-correspondence.json').write_text(json.dumps(receipt, indent=2) + '\n')
print(json.dumps({'serverVersion': observed['serverVersion'], 'tables': len(expected), 'columns': sum(map(len, expected_columns.values())), 'foreignKeys': len(expected_fks), 'sequences': len(expected_sequences),
                  'rollbackRemovedNamespace': True, 'truncateRefusals': 4, 'truncateModes': ['origin', 'replica'], 'transactionTimeout': observed['transactionTimeout']}))
