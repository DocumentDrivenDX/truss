"""Original reified graph source archive; never a compiler/native admission token.

The trusted host supplies original owner compiler bytes. Comparisons preserve
physical/logical source identities and accepted census without interpreting SQL.
Native installer/epoch machinery separately verifies actual source and custody.
"""
from dataclasses import dataclass,field,replace
from hashlib import sha256
from ._owner_evidence_json import decode_owner_evidence_json,same_owner_evidence

@dataclass(frozen=True,slots=True)
class PreparedGraphSecuritySource:
 original_request:bytes
 original_response:bytes
 accepted_catalog_assessment:bytes
 native_dependencies:bytes # original compiler request, including graph binding
 native_guard:tuple[bytes,bytes,int]|None=None
 security_ready:bool=field(default=False,init=False)


def snapshot_graph_security_source(value):
 if type(value) is not PreparedGraphSecuritySource or value.security_ready is not False:
  raise ValueError('Original graph source archive required')
 value=replace(value)
 for raw,limit in ((value.original_request,4000000),(value.original_response,16777216),(value.accepted_catalog_assessment,1048576),(value.native_dependencies,4000000)):
  if type(raw) is not bytes or not 1<=len(raw)<=limit:raise ValueError('Bounded original graph source bytes required')
 physical=decode_owner_evidence_json(value.original_request)
 assessment=decode_owner_evidence_json(value.accepted_catalog_assessment)
 request=decode_owner_evidence_json(value.native_dependencies)
 output=decode_owner_evidence_json(value.original_response)
 binding=decode_owner_evidence_json(request['bindingJson'].encode())
 if (binding.get('version')!='weft.truss.security.graph-source/0.1-candidate'
     or type(assessment['revision']) is not str or not 1<=len(assessment['revision'])<=19
     or not assessment['revision'].isascii() or not assessment['revision'].isdigit() or assessment['revision'][0]=='0'
     or int(assessment['revision'])>9223372036854775807
     or type(binding['nativeSchemaRevision']) is not str or binding['nativeSchemaRevision']!=assessment['revision']
     or not same_owner_evidence(decode_owner_evidence_json(binding['inventoryJson'].encode()),assessment)
     or type(physical['modules']) is not list or len(physical['modules'])!=1
     or not same_owner_evidence(binding['physicalModule'],{**physical['modules'][0],'selectedModuleIds':['m']})
     or output.get('version')!='weft.truss.security.graph-lowering/0.1-candidate'
     or output.get('securityReady') is not False
     or output.get('sourceRequestSha256')!=sha256(value.native_dependencies).hexdigest()
     or output.get('bindingSha256')!=sha256(request['bindingJson'].encode()).hexdigest()
     or output['query'].get('securityReady') is not False
     or output['query'].get('nativeAdmission')!='required'
     or output['query']['contextSha256']!=output['contextSha256']
     or output['query']['graphSourceSha256']!=output['graph']['graphSourceSha256']):
  raise ValueError('Original physical graph and compiler source correspondence required')
 pin=binding['physicalModule']['pin'];document=binding['physicalModule']['documentJson']
 if (type(pin) is not dict or set(pin)!={'documentId','revision','umfVersion','sha256'}
     or any(type(v) is not str or not v for v in pin.values())
     or pin['sha256']!=sha256(document.encode()).hexdigest()
     or decode_owner_evidence_json(document.encode())['id']!=pin['documentId']
     or binding['physicalModule']['selectedModuleIds']!=['m']):
  raise ValueError('Original authored physical graph pin required')
 return value


def graph_source_archives(value,release):
 value=snapshot_graph_security_source(value)
 return [('bundle','graph:original-release-manifest',release),
         ('expected_inventory','graph:original-accepted-assessment',value.accepted_catalog_assessment),
         ('installed_inventory','graph:recaptured-accepted-assessment',value.accepted_catalog_assessment),
         ('input','graph:original-physical-request',value.original_request),
         ('input','graph:original-compiler-request',value.native_dependencies),
         ('input','graph:original-compiler-output',value.original_response)]


def acquire_graph_source_catalog_cut(cursor):
 """Fixed metadata cut for trusted graph archive/factory construction."""
 from psycopg import sql
 from ._security_catalog_assessment import SOURCE_TABLES,verify_held_accepted_catalog_source_cut
 for name in SOURCE_TABLES:
  cursor.execute(sql.SQL('LOCK TABLE ONLY {} IN SHARE MODE NOWAIT').format(sql.Identifier('truss',name)),prepare=False)
 verify_held_accepted_catalog_source_cut(cursor)


def verify_graph_fact_recipe_completeness(cursor,relations):
 """Under already qualified cuts, reject omitted native fact columns."""
 for relation in relations:
  cursor.execute("SELECT count(*)::pg_catalog.text FROM pg_catalog.pg_attribute WHERE attrelid OPERATOR(pg_catalog.=) %s::pg_catalog.oid AND attnum OPERATOR(pg_catalog.>) 0 AND NOT attisdropped",(relation.oid,),prepare=False,binary=False)
  if cursor.description is None or len(cursor.description)!=1 or cursor.description[0].type_code!=25 or cursor.fetchmany(2)!=[(str(len(relation.columns)),)]:
   raise ValueError('Complete original graph fact column census required')
