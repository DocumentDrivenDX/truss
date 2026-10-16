"""Fixture-only old/new preflight oracle; no public admission qualification claim."""
import json,hashlib,unittest
from pathlib import Path
import psycopg
from psycopg.types.json import Jsonb
from test_owned_group_batch_native import OwnedGroupBatchTests

class Equivalence(OwnedGroupBatchTests):
    test_batch_updates_preserve_keys_and_committed_values=None
    test_unique_updates_keep_trailing_noop_and_duplicate_order=None
    def tearDown(self):
        self.admin.execute('DROP FUNCTION IF EXISTS public.buffer_compare(jsonb,jsonb)')
        self.admin.execute('DROP FUNCTION IF EXISTS public.buffer_baseline_prepare(jsonb,jsonb)')
        super().tearDown()
    def test_original_update_inventories(self):
        OwnedGroupBatchTests.test_unique_updates_keep_trailing_noop_and_duplicate_order(self)
        source=Path('/private/tmp/truss-owned-prepare-before-buffer-20261016.sql').read_text()
        function=source.split('CREATE FUNCTION truss.runtime_owned_prepare(',1)[1].split('REVOKE ALL ON FUNCTION truss.runtime_owned_prepare',1)[0]
        self.admin.execute('CREATE FUNCTION public.buffer_baseline_prepare('+function)
        self.addCleanup(self.admin.execute,'DROP FUNCTION IF EXISTS public.buffer_baseline_prepare(jsonb,jsonb)')
        owner=psycopg.sql.Identifier(self.installation.owner_role)
        self.admin.execute(psycopg.sql.SQL('ALTER FUNCTION public.buffer_baseline_prepare(jsonb,jsonb) OWNER TO {}').format(owner))
        self.admin.execute('REVOKE ALL ON FUNCTION public.buffer_baseline_prepare(jsonb,jsonb) FROM PUBLIC')
        self.admin.execute('''CREATE FUNCTION public.buffer_compare(input jsonb,scope jsonb) RETURNS jsonb
          LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,pg_temp AS $$
          DECLARE old_plan jsonb;new_plan jsonb;
          BEGIN old_plan:=public.buffer_baseline_prepare(input,scope);
           new_plan:=truss.runtime_owned_prepare(input,scope);
           RETURN jsonb_build_object('equal',old_plan=new_plan,'old',old_plan,'new',new_plan);
          END $$''')
        self.addCleanup(self.admin.execute,'DROP FUNCTION IF EXISTS public.buffer_compare(jsonb,jsonb)')
        self.admin.execute(psycopg.sql.SQL('ALTER FUNCTION public.buffer_compare(jsonb,jsonb) OWNER TO {}').format(owner))
        self.admin.execute('REVOKE ALL ON FUNCTION public.buffer_compare(jsonb,jsonb) FROM PUBLIC')
        self.admin.execute('GRANT EXECUTE ON FUNCTION public.buffer_compare(jsonb,jsonb) TO consumer')
        rows=self.admin.execute('''SELECT convert_from(a.input_bytes,'UTF8')::jsonb,p.plan->'initialScope'
          FROM truss.runtime_object_attempt a JOIN truss.runtime_owned_operation p ON p.attempt_id=a.id
          WHERE p.operation_index=0 ORDER BY a.id''').fetchall()
        connection,host,assembly,tx=self.consumer()
        reports=[]
        for original,scope in rows:
            if not all(o['operation']=='update_object' for o in original['operations']):continue
            result=connection.execute('SELECT public.buffer_compare(%s,%s)',(Jsonb(original),Jsonb(scope))).fetchone()[0]
            self.assertTrue(result['equal'],json.dumps(result))
            reports.append({'operations':len(original['operations']),'equal':True,
              'inputSha256':hashlib.sha256(json.dumps(original,sort_keys=True).encode()).hexdigest(),
              'inventorySha256':hashlib.sha256(json.dumps(result['new'],sort_keys=True).encode()).hexdigest()})
        self.assertEqual(len(reports),2)
        host.detach();connection.rollback()
        # Advance the real catalog through public acceptance, leaving stored
        # images at their genuine prior accepted revision.
        from truss import CatalogDocument, Ok
        from test_catalog_relational_support import relational_document
        import os
        self.admin.execute(psycopg.sql.SQL('GRANT {} TO consumer WITH SET FALSE').format(
            psycopg.sql.Identifier(self.installation.registrar_role)))
        connection,host,assembly,tx=self.consumer()
        document=relational_document();document['id']='extra'
        prepared=assembly.prepare_catalog((CatalogDocument('extra','r1',json.dumps(document).encode()),),
            source_version=document['umf'],bun_executable=os.environ['TRUSS_BUN_EXECUTABLE'])
        accepted=assembly.accept_in_transaction(tx,prepared,request_key='extra-catalog')
        self.assertIsInstance(accepted,Ok,repr(accepted))
        host.detach();connection.commit()
        self.admin.execute(psycopg.sql.SQL('REVOKE {} FROM consumer').format(
            psycopg.sql.Identifier(self.installation.registrar_role)))
        revision=self.admin.execute('SELECT rev FROM truss.schema_head WHERE id=1').fetchone()[0]
        self.assertGreater(revision,1)
        connection,host,assembly,tx=self.consumer()
        for original,scope in rows:
            if not all(o['operation']=='update_object' for o in original['operations']):continue
            scope=dict(scope,catalogRevision=revision)
            self.assertTrue(all(n['rev']<revision for n in scope['nodes'].values()))
            result=connection.execute('SELECT public.buffer_compare(%s,%s)',(Jsonb(original),Jsonb(scope))).fetchone()[0]
            self.assertTrue(result['equal'],json.dumps(result))
            reports.append({'operations':len(original['operations']),'equal':True,
              'case':'captured original scope with current catalog head and genuinely older stored images',
              'catalogRevision':revision,
              'inventorySha256':hashlib.sha256(json.dumps(result['new'],sort_keys=True).encode()).hexdigest()})
        host.detach();connection.rollback()
        Path('/private/tmp/truss-buffer-inventory-equivalence-20261016.json').write_text(json.dumps({
            'scope':'Fixture-only SECURITY DEFINER comparator under installed owner, called by consumer; original committed input and captured initial scope; no production wrapper or admission claim',
            'baselineSourceSha256':hashlib.sha256(source.encode()).hexdigest(),'cases':reports},indent=2)+'\n')

if __name__=='__main__':unittest.main(verbosity=2)
