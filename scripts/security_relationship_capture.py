"""Original buffered operand captures under held cuts; not a release permit.

Trusted original producer/codec checker and genuinely derived native Subject
locator remain caller obligations. This helper does not authenticate them.
"""
import json,uuid
from psycopg import sql
from security_relational_capture import _relational_parameters,_run_relational_text
from truss._owner_evidence_json import decode_owner_evidence_json
from truss._security_relationship_source import capture_relationship_source_comparison
from truss._security_catalog_assessment import verify_held_accepted_catalog_source_cut
from security_ontology_read_cut import verify_held_ontology_fact_cut


def capture_relationship_operands(cursor,request,output,subject_id,check_codecs):
 capture_relationship_source_comparison(request,output)
 packet=decode_owner_evidence_json(output)
 # Pure original value verification must precede every native anchor/capture.
 check_codecs(request,output)
 if type(subject_id) is not int or not 1<=subject_id<=9223372036854775807:raise ValueError('Original native Subject locator required')
 types,values=_relational_parameters(packet,subject_id)
 def held():
  verify_held_accepted_catalog_source_cut(cursor)
  verify_held_ontology_fact_cut(cursor,include_subject=True)
 checks=packet['checks']
 if type(checks) is not list or any(type(c) is not dict or c.get('stage') not in ('beforeOperandCapture','afterOperandValidation') for c in checks):raise ValueError('Original relational check stages required')
 held()
 for check in checks:
  if check['stage']=='beforeOperandCapture' and _run_relational_text(cursor,types,values,check['sql'])!=[('0',)]:raise ValueError('Original relational integrity check refused')
 scans=[];names=set()
 for read in packet['operandReads']:
  if read['scan'] in names or read['nativeAdmission']!='required' or read['scope']!='complete_primary_permitted_population_under_held_native_cuts':raise ValueError('Original complete operand capture scope required')
  names.add(read['scan']);name='operands_'+uuid.uuid4().hex
  declarations=sql.SQL(',').join(sql.SQL('pg_catalog.'+t) for t in types)
  cursor.execute(sql.SQL('PREPARE {}({}) AS ').format(sql.Identifier(name),declarations)+sql.SQL(read['sql']),prepare=False)
  try:
   cursor.execute(sql.SQL('EXECUTE {}({})').format(sql.Identifier(name),sql.SQL(',').join(sql.Literal(v) for v in values)),prepare=False,binary=False)
   if cursor.description is None or len(cursor.description)!=1 or cursor.description[0].type_code!=25:raise ValueError('Original operand TEXT transport required')
   rows=cursor.fetchmany(4097)
   if len(rows)>4096 or any(type(row) is not tuple or len(row)!=1 or type(row[0]) is not str or len(row[0].encode())>65536 for row in rows):raise ValueError('Bounded complete operand capture required')
   scans.append({'scan':read['scan'],'rows':[decode_owner_evidence_json(row[0].encode()) for row in rows]})
  finally:cursor.execute(sql.SQL('DEALLOCATE {}').format(sql.Identifier(name)),prepare=False)
 raw=json.dumps({'version':'weft.security.operand-values/0.1-candidate','contextSha256':packet['queryContextSha256'],'scans':scans},separators=(',',':')).encode()
 if len(raw)>4000000:raise ValueError('Bounded complete operand batch required')
 check_codecs(request,output,raw);held()
 return raw


def execute_relationship_program(cursor,request,output,subject_id,check_codecs,inspect):
 operands=capture_relationship_operands(cursor,request,output,subject_id,check_codecs)
 packet=decode_owner_evidence_json(output);types,values=_relational_parameters(packet,subject_id)
 for check in packet['checks']:
  if check['stage']=='afterOperandValidation' and _run_relational_text(cursor,types,values,check['sql'])!=[('0',)]:raise ValueError('Original relational integrity check refused')
 rows=[decode_owner_evidence_json(row[0].encode()) for row in _run_relational_text(cursor,types,values,packet['executionSql'])]
 batch=json.dumps({'version':packet['resultContract']['encoding'],'resultContractSha256':packet['resultContractSha256'],'rows':rows},separators=(',',':')).encode()
 if len(batch)>4000000:raise ValueError('Bounded complete relational batch required')
 checked=inspect(request,output,operands,batch)
 verify_held_accepted_catalog_source_cut(cursor);verify_held_ontology_fact_cut(cursor,include_subject=True)
 return {'operandBatch':operands,'batch':batch,'inspection':checked}

