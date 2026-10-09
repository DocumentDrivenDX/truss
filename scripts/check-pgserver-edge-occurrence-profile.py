#!/usr/bin/env python3
"""Native edge tuple uniqueness boundary, not a protected graph installation."""
import hashlib
import importlib.metadata
import importlib.resources
import json
from pathlib import Path
import subprocess
import tempfile
import pgserver

root = Path(__file__).resolve().parents[1]
source_path = 'docs/helix/04-build/evidence/source-epoch-layout-0.16.owner-export.sql'
source = (root / source_path).read_bytes()
assert importlib.metadata.version('pgserver') == '0.1.4'
psql = Path(str(importlib.resources.files('pgserver'))) / 'pginstall/bin/psql'
fixture = r'''
INSERT INTO truss.schema_doc VALUES
 (0,1,'administrative-edge-occurrence-fixture','0','unadmitted',repeat('0',64),'{}','{}');
INSERT INTO truss.type_def(document_id,type_id,module,element,kind,since_rev,doc_ord,
 lineage_profile,lineage_bytes,definition_source_kind,binding_source_rev,
 binding_source_pointer,binding_source_bytes) VALUES
 ('administrative-edge-occurrence-fixture',1,'fixture','Source','Record',0,1,'fixture',decode('01','hex'),
  'accepted_binding',0,'/fixture/source',decode('01','hex')),
 ('administrative-edge-occurrence-fixture',2,'fixture','Target','Record',0,1,'fixture',decode('02','hex'),
  'accepted_binding',0,'/fixture/target',decode('02','hex'));
INSERT INTO truss.rel_def(document_id,rel_type_id,module,rel_id,name,source_min,
 source_max,target_min,target_max,lifecycle,directed,since_rev,doc_ord,
 definition_source_kind,binding_source_rev,binding_source_pointer,binding_source_bytes) VALUES
 ('administrative-edge-occurrence-fixture',1,'fixture','R1','R1',0,NULL,0,NULL,'independent',true,0,1,
  'accepted_binding',0,'/fixture/r1',decode('03','hex')),
 ('administrative-edge-occurrence-fixture',2,'fixture','R2','R2',0,NULL,0,NULL,'independent',true,0,1,
  'accepted_binding',0,'/fixture/r2',decode('04','hex'));
INSERT INTO truss.rel_endpoint VALUES (1,1,2),(2,1,2);
INSERT INTO truss.object(id,type_id,rev) VALUES (10,1,0),(20,2,0),(30,2,0);
INSERT INTO truss.edge(id,rel_type_id,source_id,source_type,target_id,target_type,props,rev)
 VALUES (100,1,10,1,20,2,'{"occurrence":"first"}',0);
DO $$
DECLARE rejected_constraint text;
BEGIN
 BEGIN
  INSERT INTO truss.edge(id,rel_type_id,source_id,source_type,target_id,target_type,props,rev)
   VALUES (101,1,10,1,20,2,'{"occurrence":"different"}',0);
  RAISE EXCEPTION 'parallel occurrence unexpectedly admitted';
 EXCEPTION WHEN unique_violation THEN
  GET STACKED DIAGNOSTICS rejected_constraint = CONSTRAINT_NAME;
  IF rejected_constraint <> 'edge_out' THEN
   RAISE EXCEPTION 'wrong uniqueness refusal: %', rejected_constraint;
  END IF;
 END;
END $$;
INSERT INTO truss.edge(id,rel_type_id,source_id,source_type,target_id,target_type,props,rev)
 VALUES (102,2,10,1,20,2,'{"occurrence":"other-relationship"}',0),
        (103,1,10,1,30,2,'{"occurrence":"other-target"}',0);
SELECT json_build_object('edges',
 (SELECT json_agg(json_build_object('id',id::text,'relationship',rel_type_id::text,
   'source',source_id::text,'target',target_id::text,'occurrence',props->>'occurrence') ORDER BY id)
  FROM truss.edge),
 'indexDefinition',pg_get_indexdef('truss.edge_out'::regclass));
'''
expected = [
 {'id':'100','relationship':'1','source':'10','target':'20','occurrence':'first'},
 {'id':'102','relationship':'2','source':'10','target':'20','occurrence':'other-relationship'},
 {'id':'103','relationship':'1','source':'10','target':'30','occurrence':'other-target'},
]
with tempfile.TemporaryDirectory(prefix='truss-edge-occurrence-') as directory:
 server = pgserver.get_server(Path(directory) / 'data', cleanup_mode='stop')
 def query(sql):
  return subprocess.check_output([str(psql),server.get_uri(),'-X','-q','-A','-t',
   '-v','ON_ERROR_STOP=1'],input=sql,text=True,timeout=60).strip()
 try:
  version = query('SHOW server_version;')
  assert version == '16.2'
  observed = json.loads(query('BEGIN;\n' + source.decode('utf-8') + ';\n' + fixture + '\nROLLBACK;'))
  assert observed['edges'] == expected
  assert observed['indexDefinition'] == (
   'CREATE UNIQUE INDEX edge_out ON truss.edge USING btree (source_id, rel_type_id, target_id) INCLUDE (target_type)')
  assert query("SELECT to_regnamespace('truss') IS NULL;") == 't'
 finally:
  server.cleanup()
receipt = {
 'scope':'Original source-epoch0.16 edge tuple uniqueness on local PostgreSQL16.2; synthetic administrative fixtures, no protected writer, catalog or security adoption',
 'pgserver':'0.1.4','serverVersion':version,
 'parallelTupleRefusal':{'sqlState':'23505','nativeIndex':'edge_out'},
 'expectedEdges':expected,'observed':observed,
 'sameTupleParallelOccurrencesSupported':False,
 'differentRelationshipAndDifferentTargetStored':True,
 'protectedInstallationQualified':False,'participationQueryQualified':False,
 'rollbackRemovedNamespace':True,
 'source':{'path':source_path,'sha256':hashlib.sha256(source).hexdigest()},
 'fixtureSha256':hashlib.sha256(fixture.encode()).hexdigest(),
 'producerSha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
}
(root / 'docs/helix/04-build/evidence/design-audit/pgserver-edge-occurrence-profile.json').write_text(
 json.dumps(receipt,indent=2)+'\n')
print(json.dumps({'serverVersion':version,'parallelTupleRefused':True,
 'observedEdges':len(expected),'protectedInstallationQualified':False}))
