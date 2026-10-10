#!/usr/bin/env python3
"""Rollback-only populated immutable-guard component checks; no installer publication."""
import argparse
import hashlib
import importlib.metadata
import importlib.resources
import json
from pathlib import Path
import subprocess
import tempfile
import pgserver

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--corrected-pgserver', action='store_true')
args = parser.parse_args()
selected_package = '0.1.4+truss.pg16.15' if args.corrected_pgserver else '0.1.4'
selected_server = '16.15' if args.corrected_pgserver else '16.2'
receipt_name = ('pgserver-corrected-populated-guard-component.json' if args.corrected_pgserver
                else 'pgserver-populated-guard-component.json')
root = Path(__file__).resolve().parents[1]
paths = [
 'docs/helix/04-build/evidence/source-epoch-layout-0.16.owner-export.sql',
 'docs/helix/04-build/evidence/operation-configuration-storage.owner-export.sql',
 'docs/helix/04-build/evidence/layout-migration-storage.owner-export.sql',
 'packages/postgresql/native/operation-configuration-immutability.sql',
 'packages/postgresql/native/layout-migration-receipt-immutability.sql',
 'docs/helix/04-build/evidence/design-audit/pgserver-populated-guard-fixture.sql',
]
originals = [(root / p).read_bytes() for p in paths]
assert importlib.metadata.version('pgserver') == selected_package
psql = Path(str(importlib.resources.files('pgserver'))) / 'pginstall/bin/psql'
probe = '''
DO $$
DECLARE mode text; relation text; command text; before_row jsonb; after_row jsonb;
BEGIN
 FOREACH mode IN ARRAY ARRAY['origin','replica'] LOOP
  PERFORM set_config('session_replication_role',mode,true);
  FOREACH relation IN ARRAY ARRAY['operation_configuration','layout_migration_receipt'] LOOP
   EXECUTE format('SELECT to_jsonb(t) FROM truss.%I t',relation) INTO STRICT before_row;
   FOREACH command IN ARRAY ARRAY['UPDATE','DELETE','TRUNCATE'] LOOP
    BEGIN
     IF command='UPDATE' THEN
      IF relation='operation_configuration' THEN
       UPDATE truss.operation_configuration SET configuration_bytes=convert_to('changed','UTF8');
      ELSE
       UPDATE truss.layout_migration_receipt SET original_receipt_bytes=convert_to('changed','UTF8');
      END IF;
     ELSE
      EXECUTE CASE WHEN command='DELETE' THEN format('DELETE FROM truss.%I',relation)
       ELSE format('TRUNCATE truss.%I',relation) END;
     END IF;
     RAISE EXCEPTION 'immutable operation did not refuse' USING ERRCODE='P0001';
    EXCEPTION WHEN SQLSTATE '55000' THEN NULL;
    END;
    EXECUTE format('SELECT to_jsonb(t) FROM truss.%I t',relation) INTO STRICT after_row;
    IF before_row IS DISTINCT FROM after_row THEN
     RAISE EXCEPTION 'immutable row changed after refusal';
    END IF;
   END LOOP;
  END LOOP;
 END LOOP;
 PERFORM set_config('session_replication_role','origin',true);
END $$;
SELECT json_build_object('serverVersion',current_setting('server_version'),
 'configuration',(SELECT json_build_array(operation_ordinal::text,configuration_generation::text,
 key_reuse,journal_mode,convert_from(configuration_bytes,'UTF8'),convert_from(selected_binding_bytes,'UTF8'),
 convert_from(installed_inventory_bytes,'UTF8'),encode(configuration_sha256,'hex'),
 encode(selected_binding_sha256,'hex'),encode(installed_inventory_sha256,'hex')) FROM truss.operation_configuration),
 'receipt',(SELECT json_build_array(storage_row_id::text,convert_from(original_attempt_identity_bytes,'UTF8'),
 convert_from(original_request_bytes,'UTF8'),convert_from(original_receipt_bytes,'UTF8'),
 encode(original_attempt_sha256,'hex'),encode(original_request_sha256,'hex'),encode(original_receipt_sha256,'hex'))
 FROM truss.layout_migration_receipt));
ROLLBACK;
'''
hash_text = lambda value: hashlib.sha256(value.encode()).hexdigest()
with tempfile.TemporaryDirectory(prefix='truss-populated-guards-') as directory:
    server = pgserver.get_server(Path(directory) / 'data', cleanup_mode='stop')
    def query(sql):
        return subprocess.check_output([str(psql),server.get_uri(),'-X','-q','-A','-t','-v','ON_ERROR_STOP=1'],
                                       input=sql,text=True,timeout=60).strip()
    try:
        assert query('SHOW server_version;') == selected_server, 'Wrong selected native version'
        observed = json.loads(query('BEGIN;\n' + b';\n'.join(originals).decode() + ';\n' + probe))
        assert observed['configuration'] == ['0','0','forbid','engine','fixture-configuration','fixture-binding','fixture-inventory',
            hash_text('fixture-configuration'),hash_text('fixture-binding'),hash_text('fixture-inventory')]
        assert observed['receipt'] == ['1','fixture-attempt','fixture-request','fixture-receipt',
            hash_text('fixture-attempt'),hash_text('fixture-request'),hash_text('fixture-receipt')]
        assert query("SELECT to_regnamespace('truss') IS NULL") == 't'
    finally:
        server.cleanup()
receipt = {'scope':'Populated immutable guard component under rollback; administrative fixtures with actual FKs, not protected original producers or a ready installation',
 'pgserver':selected_package,'nativeBinarySha256':{name:hashlib.sha256((psql.parent/name).read_bytes()).hexdigest() for name in ('postgres','psql')},'observation':observed,'refusals':12,'sqlstate':'55000','modes':['origin','replica'],
 'operations':['UPDATE','DELETE','TRUNCATE'],'unchangedCompleteRowsAfterEachRefusal':True,
 'independentOriginalBytesAndHashesMatch':True,'rollbackRemovedNamespace':True,
 'sources':[{'path':p,'sha256':hashlib.sha256(b).hexdigest()} for p,b in zip(paths,originals)],
 'producerSha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
 'limitations':['No installer/ready-marker publication','No original capsule/receipt semantic producer admission',
 'No ordinary-role authorization qualification','No complete retention/cleanup lifecycle or migration execution']}
(root/'docs/helix/04-build/evidence/design-audit'/receipt_name).write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({'serverVersion':observed['serverVersion'],'refusals':12,'unchangedRows':True,'rollbackRemovedNamespace':True}))
