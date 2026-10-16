"""Stock-cursor native source observation; data, never an authority witness.

Original host ownership, source/routine/authority fencing and final release remain
separate obligations. Selected relation SHARE cuts last until caller settlement.
"""
from dataclasses import dataclass
from hashlib import sha256
from importlib.resources import files
import json
from .catalog_runtime import _release
from ._owner_evidence_json import decode_owner_evidence_json
from ._security_catalog_assessment import capture_accepted_catalog,SOURCE_TABLES,verify_held_accepted_catalog_source_cut
from ._security_catalog_subject_installation import _text_rows

VERSION='truss.native-source.inventory/0.2-candidate'
ASSESSMENT='truss.accepted-catalog-assessment/0.2-candidate'
HOMES=('edge','object','object_key_bucket')
MAX_BYTES=4_000_000
CATALOGS=(('types','type_def','type_id'),('properties','prop_def','prop_id'),('keys','key_def','type_id,key_num'),('relationships','rel_def','rel_type_id'),('endpoints','rel_endpoint','rel_type_id,source_type,target_type'))


def _uint(token,bits=32,zero=False):
    if type(token) is not str or not 1<=len(token)<=20 or not token.isascii() or not token.isdecimal() or token!=str(int(token)) or not (0 if zero else 1)<=int(token)<2**bits:
        raise ValueError('Canonical native source identity required')
    return token


def _boolean(token):
    if token not in ('true','false'):raise ValueError('Exact native source boolean required')
    return token=='true'


def _signed(token):
    if type(token) is not str or not 1<=len(token)<=11:
        raise ValueError('Exact native signed32 metadata required')
    value=int(token)
    if str(value)!=token or not -(2**31)<=value<2**31:raise ValueError('Exact native signed32 metadata required')
    return value


def _wire(value):return json.dumps(value,separators=(',',':'),ensure_ascii=True).encode()


def _bounded(raw):
    if not 1<=len(raw)<=MAX_BYTES:raise ValueError('Native source observation capacity exceeded')
    decode_owner_evidence_json(raw)
    return raw


def _exact_assessment(cursor,request,installation,revision):
    """Reuse original verifier, preserve fresh native JSON fragments after scanning.

    No native JSON number passes through Python float. PostgreSQL JSONB's own
    canonical output is observed; original authored documents remain separate.
    """
    legacy=capture_accepted_catalog(cursor,request,existing_source_cut=True)
    source=decode_owner_evidence_json(request);parts=[];retained=0
    for name,table,order in CATALOGS:
        rows=_text_rows(cursor,'SELECT to_jsonb(t)::text FROM ONLY truss.'+table+' t ORDER BY '+order,limit=4096)
        fragments=[]
        for row in rows:
            if len(row)!=1:raise ValueError('Exact native source row required')
            raw=row[0].encode();retained+=len(raw)
            if retained>MAX_BYTES:raise ValueError('Native source observation capacity exceeded')
            if type(decode_owner_evidence_json(raw)) is not dict:raise ValueError('Original native source object required')
            fragments.append(raw)
        parts.append(_wire(name)+b':['+b','.join(fragments)+b']')
    metadata={'version':ASSESSMENT,'scope':'accepted_source_and_native_definition_correspondence_only','installationId':installation[0],
              'releaseId':installation[1],'releaseSha256':installation[2],'revision':revision,'modelPins':[m['pin'] for m in source['modules']],'securityReady':False}
    exact=_bounded(_wire(metadata)[:-1]+b',"inventory":{'+b','.join(parts)+b'}}')
    return exact,legacy


@dataclass(frozen=True,slots=True)
class NativeSourceObservation:
    accepted_request:bytes
    accepted_assessment:bytes
    runtime_release:bytes
    native_inventory:bytes
    legacy_assessment:bytes
    report:bytes


def capture_native_source_observation_with_cursor(cursor,accepted_request):
    if type(accepted_request) is not bytes or not 1<=len(accepted_request)<=MAX_BYTES:
        raise ValueError('Bounded immutable accepted source required')
    request=decode_owner_evidence_json(accepted_request)
    if type(request) is not dict or type(request.get('modules')) is not list or not 1<=len(request['modules'])<=256:
        raise ValueError('Complete bounded accepted source modules required')
    for module in request['modules']:
        if type(module) is not dict or type(module.get('documentJson')) is not str or type(decode_owner_evidence_json(module['documentJson'].encode())) is not dict:
            raise ValueError('Strict original model objects required')
    cursor._deadline.check()
    if _text_rows(cursor,"SELECT current_setting('server_version_num')::text,current_setting('transaction_isolation')::text,current_setting('transaction_read_only')::text",limit=1)!=[('180006','read committed','off')]:
        raise ValueError('Selected PostgreSQL18.6 read-committed observation required')
    prior=_text_rows(cursor,"SELECT current_setting('search_path')::text",limit=1)
    if len(prior)!=1:raise ValueError('Original observation search path required')
    cursor.execute("SELECT pg_catalog.set_config('search_path','pg_catalog, pg_temp',true)",prepare=False)
    # Fixed original owner tables only; no request-selected SQL or population.
    for name in sorted(set(SOURCE_TABLES)|set(HOMES)):
        cursor.execute('LOCK TABLE ONLY truss.'+name+' IN SHARE MODE NOWAIT',prepare=False)
    verify_held_accepted_catalog_source_cut(cursor)
    release=_bounded(files('truss').joinpath('_catalog_runtime/manifest.json').read_bytes())
    manifest,digest,_=_release()
    if sha256(release).hexdigest()!=digest:raise ValueError('Original complete runtime release bytes required')
    installed=_text_rows(cursor,'SELECT installation_id::text,release_id::text,release_sha256::text,owner_oid::text FROM truss.runtime_current_installation()',limit=1)
    if len(installed)!=1 or installed[0][1:3]!=(manifest['releaseId'],digest):raise ValueError('Exact installed runtime release required')
    installation=installed[0];_uint(installation[3])
    heads=_text_rows(cursor,'SELECT rev::text FROM ONLY truss.schema_head WHERE id=1',limit=1)
    if len(heads)!=1:raise ValueError('Exact accepted source head required')
    revision=_uint(heads[0][0],64)
    database=_text_rows(cursor,"SELECT s.system_identifier::text,d.oid::text,d.datname::text FROM pg_catalog.pg_control_system() s CROSS JOIN pg_catalog.pg_database d WHERE d.datname=current_database()",limit=1)
    schema=_text_rows(cursor,"SELECT oid::text,nspname::text,nspowner::text FROM pg_catalog.pg_namespace WHERE nspname='truss'",limit=1)
    if len(database)!=1 or len(schema)!=1:raise ValueError('Actual database and schema required')
    db=database[0];ns=schema[0];_uint(db[0],64);_uint(db[1]);_uint(ns[0]);_uint(ns[2])
    exact,legacy=_exact_assessment(cursor,accepted_request,installation,revision)
    relations=[]
    for name in HOMES:
        cursor._deadline.check()
        rows=_text_rows(cursor,"SELECT c.oid::text,c.relnamespace::text,c.relowner::text,c.relkind::text,c.relpersistence::text,c.relrowsecurity::text,c.relforcerowsecurity::text,EXISTS(SELECT 1 FROM pg_catalog.pg_inherits i WHERE i.inhrelid=c.oid OR i.inhparent=c.oid)::text FROM pg_catalog.pg_class c JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='truss' AND c.relname=%s",(name,),1)
        if len(rows)!=1 or rows[0][1:]!=(ns[0],installation[3],'r','p','false','false','false'):
            raise ValueError('Complete original unfiltered native source home required')
        oid=_uint(rows[0][0]);columns=[];constraints=[]
        column_sql="SELECT a.attnum::text,a.attname::text,a.atttypid::text,a.atttypmod::text,a.attcollation::text,a.attnotnull::text,a.attisdropped::text,a.attgenerated::text,a.attidentity::text,(d.oid IS NOT NULL)::text,coalesce(pg_catalog.pg_get_expr(d.adbin,d.adrelid),'')::text FROM pg_catalog.pg_attribute a LEFT JOIN pg_catalog.pg_attrdef d ON d.adrelid=a.attrelid AND d.adnum=a.attnum WHERE a.attrelid=%s::oid AND a.attnum>0 ORDER BY a.attnum"
        # Budget expression text before stock-driver row materialization.
        budget=_text_rows(cursor,"SELECT count(*)::text,coalesce(sum(octet_length(coalesce(pg_catalog.pg_get_expr(d.adbin,d.adrelid),''))),0)::text FROM pg_catalog.pg_attribute a LEFT JOIN pg_catalog.pg_attrdef d ON d.adrelid=a.attrelid AND d.adnum=a.attnum WHERE a.attrelid=%s::oid AND a.attnum>0",(oid,),1)
        if len(budget)!=1 or not 1<=int(_uint(budget[0][0]))<=1600 or int(_uint(budget[0][1],64,True))>MAX_BYTES:
            raise ValueError('Bounded complete native source columns required')
        raw_columns=_text_rows(cursor,column_sql,(oid,),1600)
        if len(raw_columns)!=int(budget[0][0]):raise ValueError('Complete native source column census required')
        for number,label,type_oid,typmod,collation,not_null,dropped,generated,identity,has_default,expression in raw_columns:
            attnum=int(_uint(number,16));_uint(type_oid);_uint(collation,32,True)
            if not 1<=attnum<=1600 or _boolean(dropped) or generated not in ('','s','v') or identity not in ('','a','d'):
                raise ValueError('Supported complete native source columns required')
            if generated and not _boolean(has_default) or not _boolean(has_default) and expression:
                raise ValueError('Consistent original native expression metadata required')
            columns.append({'attnum':attnum,'name':label,'typeOid':type_oid,'typmod':_signed(typmod),'collationOid':collation,'notNull':_boolean(not_null),'dropped':False,'generated':generated,'identity':identity,'expression':{'kind':('generated' if generated else 'default') if _boolean(has_default) else 'none','source':expression if _boolean(has_default) else None}})
        budget=_text_rows(cursor,"SELECT count(*)::text,coalesce(sum(octet_length(pg_catalog.pg_get_constraintdef(oid,false))),0)::text FROM pg_catalog.pg_constraint WHERE conrelid=%s::oid",(oid,),1)
        if len(budget)!=1 or int(_uint(budget[0][0],32,True))>4096 or int(_uint(budget[0][1],64,True))>MAX_BYTES:
            raise ValueError('Bounded complete native source constraints required')
        raw_constraints=_text_rows(cursor,"SELECT oid::text,conname::text,contype::text,convalidated::text,condeferrable::text,condeferred::text,confrelid::text,pg_catalog.pg_get_constraintdef(oid,false)::text FROM pg_catalog.pg_constraint WHERE conrelid=%s::oid ORDER BY oid",(oid,),4096)
        if len(raw_constraints)!=int(budget[0][0]):raise ValueError('Complete native constraint census required')
        for coid,label,kind,valid,defer,initial,target,definition in raw_constraints:
            constraints.append({'oid':_uint(coid),'name':label,'kind':kind,'validated':_boolean(valid),'deferrable':_boolean(defer),'initiallyDeferred':_boolean(initial),'referencedRelationOid':_uint(target,32,True),'definition':definition})
        relations.append({'oid':oid,'name':name,'namespaceOid':ns[0],'ownerOid':installation[3],'kind':'r','persistence':'p','rowSecurity':False,'forceRowSecurity':False,'inherits':False,'columns':columns,'constraints':constraints})
    inventory=_bounded(_wire({'version':VERSION,'installationId':installation[0],'database':{'systemIdentifier':db[0],'oid':db[1],'name':db[2]},'schema':{'oid':ns[0],'name':ns[1],'ownerOid':ns[2]},'release':{'id':manifest['releaseId'],'sha256':digest},'coverage':{'relations':list(HOMES),'completeSelectedHomes':True},'relations':relations}))
    report=_wire({'version':'truss.native-source.observation/0.2-candidate','scope':'selected-native-source-observation','complete':False,'authority':False,'securityReady':False,'nativeAdmission':'required','sources':[{'role':role,'sha256':sha256(raw).hexdigest(),'bytes':len(raw)} for role,raw in [('accepted-request',accepted_request),('accepted-assessment',exact),('runtime-release',release),('native-inventory',inventory)]],'unresolved':['native Field/Key/edge/codec mapping','source continuity and authenticated held authority','closing guards and guarded release']})
    cursor.execute("SELECT pg_catalog.set_config('search_path',%s,true)",(prior[0][0],),prepare=False)
    if cursor.fetchmany(2)!=prior:raise ValueError('Original observation search path restoration required')
    cursor._deadline.check()
    return NativeSourceObservation(accepted_request,exact,release,inventory,legacy,report)
