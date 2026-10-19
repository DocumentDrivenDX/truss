# SPDX-License-Identifier: MIT OR Apache-2.0
"""Distinct ordinary caller/private executor traversal publication candidate.

Trusted source/binary/host/server/installer custody remains required. This
fixed fixture query is not public activation or complete channel admission.
"""
from pathlib import Path
from hashlib import sha256
from uuid import uuid4
import json,subprocess,os
from truss.psycopg_host import PsycopgHost,_HostPairReservation
from truss.execution import Ok
from truss.catalog_runtime import _pin_cursor
from truss._owner_evidence_json import decode_owner_evidence_json
from truss._security_relationship_source import capture_relationship_source_comparison
from truss._security_relationship_epoch_read import snapshot_relationship_epoch_read_context,acquire_relationship_epoch_read,verify_held_relationship_epoch_read
from truss._security_graph_subject_installation import snapshot_graph_subjects,derive_graph_subject_profile,read_own_graph_subject_with_cursor,verify_registered_graph_subjects_with_cursor
from security_ontology_native_subject_read import _caller,_registered_subject,_verify_native_peer,_text_rows
from security_ontology_read_cut import acquire_issued_ontology_read_cut
from security_relationship_facts import capture_relationship_facts
from security_relationship_request import prepare_relationship_request,FIXTURE
from security_relationship_capture import execute_relationship_program
from security_relationship_codecs import prepare_owned_relationship_codec_checker
from security_relationship_inspection import prepare_owned_relationship_inspector
from security_relationship_publication import inspected_relationship_publication

ROOT=Path(__file__).resolve().parent.parent
QUERY="SELECT r.resourceId FROM Resource r WHERE HAS_RELATED(r.relatedResources, KEY('RB'))"

def publish_native_relationship_read(caller,caller_transaction,executor,executor_transaction,context,subjects,publisher,*,compiler_binary):
 if type(caller) is not PsycopgHost or type(executor) is not PsycopgHost or caller is executor or not callable(publisher):raise ValueError('Distinct original relationship hosts/publisher required')
 context=snapshot_relationship_epoch_read_context(context);subjects=snapshot_graph_subjects(subjects)
 if subjects.profile_bytes!=derive_graph_subject_profile(context.source):raise ValueError('Original relationship Subject source required')
 if context.subject_source!=Path(__file__).read_bytes():raise ValueError('Original relationship host source pin required')
 original=decode_owner_evidence_json(context.source.native_dependencies)
 if original['sql']!=QUERY:raise ValueError('Original fixed authored relationship query required')
 policy=original['policyJson'].encode()
 choices=[name for name in ('policy','policy-observation-denied') if (FIXTURE/(name+'.json')).read_bytes()==policy]
 if len(choices)!=1:raise ValueError('Original selected relationship policy preimage required')
 variant=choices[0];denied=variant=='policy-observation-denied'
 binary=Path(compiler_binary).resolve()
 checker=prepare_owned_relationship_codec_checker(binary.with_name('security_relationship_codecs'))
 inspector=prepare_owned_relationship_inspector(binary.with_name('security_relationship_result'))
 paths=[Path(__file__),ROOT/'scripts/security_ontology_native_subject_read.py',ROOT/'scripts/security_relationship_facts.py',ROOT/'scripts/security_ontology_edge_projection.py',ROOT/'scripts/evaluate-security-public-relationship-fixture.ts',ROOT/'scripts/security_relationship_request.py',binary]+list(FIXTURE.glob('*.json'))
 pins={p:sha256(p.read_bytes()).digest() for p in paths}
 def operation(cursor,observed):
  identity=_caller(cursor,observed);previous=_text_rows(cursor,"SELECT pg_catalog.current_setting('application_name')::pg_catalog.text",limit=1)
  if len(previous)!=1:raise ValueError('Original relationship caller application context required')
  challenge='truss_relationship_'+uuid4().hex
  if _text_rows(cursor,"SELECT pg_catalog.set_config('application_name',%s,true)::pg_catalog.text",(challenge,),1)!=[(challenge,)]:raise ValueError('Original relationship live caller challenge required')
  def evaluate(private,private_observed):
   if private_observed[0][2:]!=('read_committed','read_write'):raise ValueError('Original fresh relationship executor required')
   _pin_cursor(private)
   acquire_issued_ontology_read_cut(private,context.issuer.owner_oid,context.issuer.caller_oid)
   acquire_relationship_epoch_read(private,context)
   _verify_native_peer(private,identity,observed[0][0],challenge)
   own=read_own_graph_subject_with_cursor(cursor,subjects,identity)
   issuer=verify_registered_graph_subjects_with_cursor(private,subjects,caller_pid=int(observed[0][0]),source=context.source)
   subject=_registered_subject(private,identity,subjects.bindings,context.issuer.caller_oid,issuer)
   if own!=subject:raise ValueError('Original relationship issuer/map disagreement')
   before=capture_relationship_facts(private,context.source.original_request)
   request=prepare_relationship_request(context.source.original_request,before[0],observation_denied=denied)
   output=subprocess.run([str(binary)],input=request,capture_output=True,check=True,timeout=15).stdout
   if capture_relationship_source_comparison(request,output)!=capture_relationship_source_comparison(context.source.native_dependencies,context.source.original_response):raise ValueError('Original relationship query/source correspondence required')
   assessment=decode_owner_evidence_json(before[0]);inventory=assessment['inventory']
   staff=[t for t in inventory['types'] if t['element']=='Staff' and t['retired_rev'] is None]
   if len(staff)!=1:raise ValueError('Original relationship Staff home required')
   props=[p for p in inventory['properties'] if p['type_id']==staff[0]['type_id'] and p['element']=='staffId' and p['retired_rev'] is None]
   if len(props)!=1:raise ValueError('Original relationship Staff key home required')
   locators=[int(oid) for oid,tid,raw,root in before[1] if tid==str(staff[0]['type_id']) and root=='false' and decode_owner_evidence_json(raw.encode()).get(str(props[0]['prop_id']))=={'kind':'string','text':subject}]
   if len(locators)!=1:raise ValueError('Original unique authenticated relationship Staff locator required')
   oracle=subprocess.run([os.environ.get('TRUSS_BUN_EXECUTABLE','bun'),str(ROOT/'scripts/evaluate-security-public-relationship-fixture.ts'),'--evaluate'],cwd=ROOT,input=json.dumps(before[3]).encode(),capture_output=True,check=True,timeout=15)
   oracle_result=decode_owner_evidence_json(oracle.stdout)
   choices=[r['observed'] for r in oracle_result['results'] if r['variant']==variant and r['subject']==subject]
   if len(choices)!=1:raise ValueError('Original complete selected relationship oracle required')
   executed=execute_relationship_program(private,request,output,locators[0],checker,inspector)
   expected=[[{'outcomeId':'original','disposition':'original','value':{'string':key}}] for key in choices[0]]
   if decode_owner_evidence_json(executed['batch'])['rows']!=expected:raise ValueError('Original native relationship result differs from semantic oracle')
   receipt={'request':request.decode(),'output':output.decode(),'operandBatch':executed['operandBatch'].decode(),'batch':executed['batch'].decode(),'resultCheck':executed['inspection'].decode()}
   published=inspected_relationship_publication(receipt)
   if capture_relationship_facts(private,context.source.original_request)!=before:raise ValueError('Original relationship facts changed before publication')
   verify_held_relationship_epoch_read(private,context)
   if verify_registered_graph_subjects_with_cursor(private,subjects,caller_pid=int(observed[0][0]),source=context.source)!=issuer or read_own_graph_subject_with_cursor(cursor,subjects,identity)!=subject:raise ValueError('Original relationship Subject changed before publication')
   if _registered_subject(private,identity,subjects.bindings,context.issuer.caller_oid,issuer)!=subject:raise ValueError('Original relationship mapping changed')
   _verify_native_peer(private,identity,observed[0][0],challenge)
   return published
  result=executor._run_operation(executor_transaction,evaluate)
  if _text_rows(cursor,"SELECT pg_catalog.set_config('application_name',%s,true)::pg_catalog.text",(previous[0][0],),1)!=previous:raise ValueError('Original relationship caller application restoration required')
  if not isinstance(result,Ok):raise ValueError('Original private relationship execution refused')
  if _caller(cursor,caller._observe(cursor))!=identity or any(sha256(p.read_bytes()).digest()!=digest for p,digest in pins.items()):raise ValueError('Original relationship caller/source changed')
  return result.value
 with _HostPairReservation(caller,executor):return caller._run_published_operation(caller_transaction,operation,publisher)
