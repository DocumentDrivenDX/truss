"""One original shared store registration; no authentication or native permit.

Trusted quiescent direct installer, PG18.6 and complete original metadata basis.
Pending issuance is not committed context. Fresh observation preserves original
receipts even when incarnation/source mismatch fences use. Absence never proves
rollback. The guard epoch is excluded from replay namespace identity.
"""
from dataclasses import dataclass
from hashlib import sha256
from importlib.resources import files
import json
from psycopg import sql
from .execution import Error,ExecutionFailure
from .psycopg_host import PsycopgHost
from .catalog_runtime import _release,_pin_cursor
from ._preparation_source_epoch import _context,_restore,_runtime_inventory
from ._action_identity_codec import encode_action_store_identity,encode_action_tenant_identity,encode_action_namespace_epoch
from ._security_catalog_subject_installation import _text_rows

_STORAGE_SHA='3b699c0d800da79207f48230a7fef8f1b3252efd0d531ecd7a0a05be5bf199d8'
_ISSUER_SHA='7181f92898912785300bb4984f41a275287e982c67ca3fde1da90fd5735d520b'
_PROFILE='truss.action-store/native-pg18/0.1'
_COLUMNS=(('singleton',16),('control_id',20),('logical_store_id',2950),('store_identity',17),('tenant_identity',17),('executor_oids',1028),('guard_epoch',2950),('epoch_identity',17),('registration_key',17),('installation_id',2950),('source_installation_id',25),('database_oid',26),('schema_oid',26),('postmaster_started_at',1184),('source_epoch',25),('source_incarnation',25),('source_profile_bytes',17),('source_evidence_bytes',17),('runtime_release_id',25),('runtime_release_sha256',17),('issuer_xid',5069),('issuer_actor_oid',26),('issued_at',1184),('initial_receipt_bytes',17),('profile_id',25))
_CHECKS=('((cardinality(executor_oids) >= 0) AND (cardinality(executor_oids) <= 4))', '((octet_length(initial_receipt_bytes) >= 1) AND (octet_length(initial_receipt_bytes) <= 4194304))', '((octet_length(registration_key) >= 1) AND (octet_length(registration_key) <= 256))', '((octet_length(runtime_release_id) >= 1) AND (octet_length(runtime_release_id) <= 1024))', '((octet_length(source_epoch) >= 1) AND (octet_length(source_epoch) <= 256))', '((octet_length(source_evidence_bytes) >= 1) AND (octet_length(source_evidence_bytes) <= 1048576))', '((octet_length(source_incarnation) >= 1) AND (octet_length(source_incarnation) <= 1024))', '((octet_length(source_profile_bytes) >= 1) AND (octet_length(source_profile_bytes) <= 65536))', '((octet_length(tenant_identity) >= 1) AND (octet_length(tenant_identity) <= 4096))', '(control_id > 0)', "(database_oid <> '0'::oid)", '(epoch_identity = convert_to(((\'"\'::text || (guard_epoch)::text) || \'"\'::text), \'UTF8\'::name))', '(guard_epoch <> logical_store_id)', "(issuer_actor_oid <> '0'::oid)", "(issuer_xid > '0'::xid8)", '(octet_length(runtime_release_sha256) = 32)', "(profile_id = 'truss.action-store/native-pg18/0.1'::text)", "(schema_oid <> '0'::oid)", '(store_identity = convert_to(((\'"\'::text || (logical_store_id)::text) || \'"\'::text), \'UTF8\'::name))', 'isfinite(issued_at)', 'isfinite(postmaster_started_at)', 'singleton')
_FUNCTIONS=(('action_store_original_receipt','truss.action_store_registration','sql','s','false',False),('register_action_store_original','bytea,bytea,oid[],text,bytea','plpgsql','v','false',True),('observe_action_store_original','bytea','plpgsql','v','true',False),('acquire_action_store_source_cut','','plpgsql','v','true',False))

@dataclass(frozen=True,slots=True)
class PendingActionStoreRegistration:
    registration_key:bytes
    tenant_identity:bytes
    receipt_bytes:bytes
    status:str='pending_commit'
    security_ready:bool=False

@dataclass(frozen=True,slots=True)
class ActionStoreObservation:
    registration_key:bytes
    receipt_bytes:bytes
    store_identity:bytes
    tenant_identity:bytes
    epoch_identity:bytes
    installation_id:str
    binding_correspondence:str
    authority:bool=False

    @property
    def binding_matches(self):return self.binding_correspondence=='matches'

@dataclass(frozen=True,slots=True)
class ActionStoreRegistrationNotObserved:
    registration_key:bytes
    disposition:str='not_observed_not_rollback'


def _sources():
    root=files('truss').joinpath('_security_bootstrap')
    raw=root.joinpath('action-store-storage.sql').read_bytes();issuer=root.joinpath('action-store-issuer.sql').read_bytes()
    if sha256(raw).hexdigest()!=_STORAGE_SHA or sha256(issuer).hexdigest()!=_ISSUER_SHA:raise ValueError('Original shared store source bytes required')
    return raw,issuer


def _receipt(raw):
    if type(raw) is not bytes or not 1<=len(raw)<=4194304:raise ValueError('Original bounded namespace receipt required')
    data=json.loads(raw)
    if type(data) is not dict or data.get('interfaceVersion')!='truss.action-store-issuance/0.1' or data.get('profileId')!=_PROFILE:raise ValueError('Original namespace receipt profile required')
    for field in ('storeIdentityHex','tenantIdentityHex','epochIdentityHex','registrationKeyHex','sourceProfileHex','sourceEvidenceHex','runtimeReleaseSha256'):
        value=data.get(field)
        if type(value) is not str or bytes.fromhex(value).hex()!=value:raise ValueError('Original namespace hexadecimal bytes required')
    if (bytes.fromhex(data['storeIdentityHex'])!=encode_action_store_identity(data['logicalStoreId'])
            or bytes.fromhex(data['epochIdentityHex'])!=encode_action_namespace_epoch(data['guardEpoch'])
            or bytes.fromhex(data['tenantIdentityHex'])!=encode_action_tenant_identity(json.loads(bytes.fromhex(data['tenantIdentityHex'])))):
        raise ValueError('Original store/tenant/epoch codec correspondence required')
    return data


def _capture_action_store_context(context):
    """Bounded exact immutable comparison copy; never issuance or authority."""
    if type(context) is not ActionStoreObservation:
        raise ValueError('Original immutable store comparison required')
    # Read each caller-owned slot once, then validate and retain only this copy.
    context=ActionStoreObservation(context.registration_key,context.receipt_bytes,context.store_identity,
        context.tenant_identity,context.epoch_identity,context.installation_id,context.binding_correspondence,context.authority)
    if type(context.authority) is not bool or context.authority is not False:
        raise ValueError('Original immutable store comparison required')
    for name,maximum in (('registration_key',256),('receipt_bytes',4194304),
                         ('store_identity',4096),('tenant_identity',4096),('epoch_identity',4096)):
        value=getattr(context,name)
        if type(value) is not bytes or not 1<=len(value)<=maximum:
            raise ValueError('Exact bounded immutable store bytes required')
    if (type(context.installation_id) is not str or not 1<=len(context.installation_id)<=256
            or type(context.binding_correspondence) is not str or context.binding_correspondence not in ('matches','fenced')):
        raise ValueError('Exact bounded immutable store labels required')
    try:
        receipt=_receipt(context.receipt_bytes)
        if (bytes.fromhex(receipt['registrationKeyHex'])!=context.registration_key
                or bytes.fromhex(receipt['storeIdentityHex'])!=context.store_identity
                or bytes.fromhex(receipt['tenantIdentityHex'])!=context.tenant_identity
                or bytes.fromhex(receipt['epochIdentityHex'])!=context.epoch_identity
                or receipt['installationId']!=context.installation_id):
            raise ValueError('Original store receipt comparison required')
    except (KeyError,TypeError,UnicodeError,RecursionError):
        raise ValueError('Original bounded store receipt required') from None
    return ActionStoreObservation(context.registration_key,context.receipt_bytes,context.store_identity,
        context.tenant_identity,context.epoch_identity,context.installation_id,context.binding_correspondence)


def _verify(cursor,owner,executors=None):
    _,issuer=_sources();source=issuer.decode('utf8')
    cursor.execute('SELECT rolcanlogin,rolsuper,rolcreaterole,rolcreatedb,rolreplication,rolbypassrls FROM pg_catalog.pg_roles WHERE oid=%s::oid',(owner,),prepare=False)
    if cursor.fetchmany(2)!=[(False,False,False,False,False,False)]:raise ValueError('Original unprivileged NOLOGIN store owner required')
    for name,args,language,volatility,secdef,admin in _FUNCTIONS:
        signature='truss.'+name+'('+args+')'
        cursor.execute('SELECT pg_catalog.to_regprocedure(%s)::pg_catalog.oid', (signature,),prepare=False)
        ids=cursor.fetchmany(2)
        if len(ids)!=1 or ids[0][0] is None:raise ValueError('Original shared store routine signature required')
        oid=ids[0][0]
        body=source.split('CREATE FUNCTION truss.'+name+'(',1)[1].split('AS $$',1)[1].split('$$;',1)[0]
        config='["search_path=pg_catalog, pg_temp"]' if name=='acquire_action_store_source_cut' else '["search_path=pg_catalog, pg_temp", "TimeZone=UTC"]'
        if name=='action_store_original_receipt':config='["search_path=pg_catalog, pg_temp", "TimeZone=UTC", "DateStyle=ISO, YMD"]'
        rows=_text_rows(cursor,"SELECT p.proowner::text,l.lanname::text,p.prokind::text,p.prorettype::text,p.proretset::text,p.prosecdef::text,p.provolatile::text,p.proparallel::text,p.proisstrict::text,p.proleakproof::text,p.prosupport::oid::text,pg_catalog.to_jsonb(p.proconfig)::text,p.prosrc,r.rolsuper::text FROM pg_catalog.pg_proc p JOIN pg_catalog.pg_language l ON l.oid=p.prolang JOIN pg_catalog.pg_roles r ON r.oid=p.proowner WHERE p.oid=%s::oid",(oid,),1)
        if (len(rows)!=1 or rows[0][1:-1]!=(language,'f','2278' if name=='acquire_action_store_source_cut' else '17','false',secdef,volatility,'u','false','false','0',config,body)
                or (rows[0][-1]!='true' if admin else rows[0][0]!=str(owner))):raise ValueError('Original store routine body/attributes required')
        names={'action_store_original_receipt':['r'],'register_action_store_original':['original_tenant','original_key','original_executors','expected_release','expected_release_sha256'],'observe_action_store_original':['original_key'],'acquire_action_store_source_cut':None}[name]
        abi=_text_rows(cursor,"SELECT coalesce(pg_catalog.to_jsonb(proargnames),'null'::pg_catalog.jsonb)::text,pronargdefaults::text,(proargdefaults IS NULL)::text FROM pg_catalog.pg_proc WHERE oid=%s::oid",(oid,),1)
        if abi!=[('null' if names is None else json.dumps(names),'0','true')]:raise ValueError('Original store argument names/default ABI required')
        acl=_text_rows(cursor,"SELECT a.grantee::text,a.grantor::text,a.privilege_type::text,a.is_grantable::text FROM pg_catalog.pg_proc p CROSS JOIN LATERAL pg_catalog.aclexplode(coalesce(p.proacl,pg_catalog.acldefault('f',p.proowner))) a WHERE p.oid=%s::oid",(oid,),8)
        if not acl or any(r[0]=='0' or r[1:]!=(rows[0][0],'EXECUTE','false') for r in acl) or ((admin or name=='action_store_original_receipt') and acl!=[(rows[0][0],rows[0][0],'EXECUTE','false')]):raise ValueError('Private original store routine ACL required')
        if executors is not None and name in ('observe_action_store_original','acquire_action_store_source_cut') and {r[0] for r in acl}!={str(owner),*(str(x) for x in executors)}:raise ValueError('Exact original store executor ACL required')
    cursor.execute("SELECT c.oid,c.reltype,c.relowner,c.relkind,c.relpersistence,c.relrowsecurity,c.relforcerowsecurity,n.nspowner,EXISTS(SELECT 1 FROM pg_catalog.pg_inherits i WHERE i.inhrelid=c.oid OR i.inhparent=c.oid) FROM pg_catalog.pg_class c JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='truss' AND c.relname='action_store_registration'",prepare=False)
    rows=cursor.fetchmany(2)
    if len(rows)!=1 or rows[0][2:]!=(owner,'r','p',False,False,owner,False):raise ValueError('Original private singleton store home required')
    table,composite=rows[0][:2]
    cursor.execute('SELECT attname,atttypid,attnotnull,attgenerated,attidentity,attisdropped,attacl FROM pg_catalog.pg_attribute WHERE attrelid=%s::oid AND attnum>0 ORDER BY attnum',(table,),prepare=False)
    if cursor.fetchmany(26)!=[(name,typ,name!='source_installation_id','s' if name=='source_installation_id' else '','',False,None) for name,typ in _COLUMNS]:raise ValueError('Original store column profile required')
    cursor.execute('SELECT typowner,typrelid,typtype FROM pg_catalog.pg_type WHERE oid=%s::oid',(composite,),prepare=False)
    if cursor.fetchmany(2)!=[(owner,table,'c')]:raise ValueError('Original store composite ownership required')
    cursor.execute("SELECT c.contype,c.convalidated,c.condeferrable,c.condeferred,c.conkey FROM pg_catalog.pg_constraint c WHERE c.conrelid=%s::oid AND c.contype<>'n' ORDER BY c.contype,c.oid",(table,),prepare=False)
    constraints=cursor.fetchmany(31)
    if (len(constraints)!=30 or sum(r[0]=='c' for r in constraints)!=22
            or any(r[1:4]!=(True,False,False) for r in constraints)
            or {(r[0],tuple(r[4])) for r in constraints if r[0]!='c'}!={('p',(1,)),('u',(2,)),('u',(3,)),('u',(4,)),('u',(7,)),('u',(9,)),('f',(10,)),('f',(11,15))}):raise ValueError('Original shared store immediate constraints required')
    cursor.execute("SELECT pg_catalog.pg_get_expr(conbin,conrelid) FROM pg_catalog.pg_constraint WHERE conrelid=%s::oid AND contype='c' ORDER BY 1",(table,),prepare=False)
    if cursor.fetchmany(23)!=[(x,) for x in _CHECKS]:raise ValueError('Exact original store CHECK expressions required')
    cursor.execute('SELECT a.attname,pg_catalog.pg_get_expr(d.adbin,d.adrelid) FROM pg_catalog.pg_attrdef d JOIN pg_catalog.pg_attribute a ON a.attrelid=d.adrelid AND a.attnum=d.adnum WHERE d.adrelid=%s::oid ORDER BY a.attnum',(table,),prepare=False)
    if cursor.fetchmany(4)!=[('singleton','true'),('control_id',"nextval('truss.action_store_control_seq'::regclass)"),('source_installation_id','(installation_id)::text')]:raise ValueError('Original store defaults/generated expression required')
    cursor.execute("SELECT pg_catalog.pg_get_constraintdef(oid),confupdtype,confdeltype,confmatchtype FROM pg_catalog.pg_constraint WHERE conrelid=%s::oid AND contype='f' ORDER BY 1",(table,),prepare=False)
    if cursor.fetchmany(3)!=[('FOREIGN KEY (installation_id) REFERENCES truss.catalog_runtime_installation(installation_id)','a','a','s'),('FOREIGN KEY (source_installation_id, source_epoch) REFERENCES truss.source_epoch_registry(installation_id, source_epoch)','a','a','s')]:raise ValueError('Exact original store FK targets/actions required')
    cursor.execute("SELECT s.seqtypid,s.seqstart,s.seqincrement,s.seqmax,s.seqmin,s.seqcache,s.seqcycle,c.relowner,c.relpersistence FROM pg_catalog.pg_sequence s JOIN pg_catalog.pg_class c ON c.oid=s.seqrelid WHERE s.seqrelid='truss.action_store_control_seq'::regclass",prepare=False)
    if cursor.fetchmany(2)!=[(20,1,1,9223372036854775807,1,1,False,owner,'p')]:raise ValueError('Original independent store control allocator required')
    cursor.execute("SELECT d.refobjid::pg_catalog.regclass::pg_catalog.text FROM pg_catalog.pg_depend d JOIN pg_catalog.pg_attrdef a ON d.classid='pg_catalog.pg_attrdef'::regclass AND d.objid=a.oid WHERE a.adrelid=%s::oid AND a.adnum=2 AND d.refclassid='pg_catalog.pg_class'::regclass AND d.deptype='n'",(table,),prepare=False)
    if cursor.fetchmany(2)!=[('truss.action_store_control_seq',)]:raise ValueError('Original control allocator dependency required')
    cursor.execute("SELECT a.grantee,a.grantor,a.privilege_type,a.is_grantable FROM pg_catalog.pg_type t CROSS JOIN LATERAL pg_catalog.aclexplode(coalesce(t.typacl,pg_catalog.acldefault('T',t.typowner))) a WHERE t.oid=%s::oid",(composite,),prepare=False)
    if cursor.fetchmany(2)!=[(owner,owner,'USAGE',False)]:raise ValueError('Original private store composite ACL required')
    cursor.execute("SELECT i.indisunique,i.indisvalid,i.indisready,i.indimmediate,i.indnkeyatts,i.indnatts,i.indkey::text,i.indoption::text,i.indpred IS NULL,i.indexprs IS NULL,am.amname,n.nspname FROM pg_catalog.pg_constraint k JOIN pg_catalog.pg_index i ON i.indexrelid=k.conindid JOIN pg_catalog.pg_class c ON c.oid=i.indexrelid JOIN pg_catalog.pg_am am ON am.oid=c.relam JOIN pg_catalog.pg_opclass o ON o.oid=i.indclass[0] JOIN pg_catalog.pg_namespace n ON n.oid=o.opcnamespace WHERE k.conrelid=%s::oid AND k.contype IN ('p','u') ORDER BY i.indkey::text",(table,),prepare=False)
    if cursor.fetchmany(7)!=[(True,True,True,True,1,1,str(x),'0',True,True,'btree','pg_catalog') for x in (1,2,3,4,7,9)]:raise ValueError('Original valid immediate store identity indexes required')
    cursor.execute("SELECT tgname,tgfoid::pg_catalog.regprocedure::pg_catalog.text,tgenabled,tgtype,tgnargs,tgargs,tgqual IS NULL FROM pg_catalog.pg_trigger WHERE tgrelid=%s::oid AND NOT tgisinternal",(table,),prepare=False)
    if cursor.fetchmany(2)!=[('action_store_registration_immutable','truss.catalog_immutable()','A',58,0,b'',True)]:raise ValueError('Original immutable store home required')
    cursor.execute("SELECT a.grantee,a.grantor,a.is_grantable FROM pg_catalog.pg_class c CROSS JOIN LATERAL pg_catalog.aclexplode(coalesce(c.relacl,pg_catalog.acldefault(CASE WHEN c.relkind='S' THEN 's'::\"char\" ELSE 'r'::\"char\" END,c.relowner))) a WHERE c.oid IN (%s::oid,'truss.action_store_control_seq'::regclass)",(table,),prepare=False)
    acl=cursor.fetchmany(32)
    if not acl or any(r!=(owner,owner,False) for r in acl):raise ValueError('Original owner-only store/allocator ACL required')
    return table


def register_action_store_in_transaction(host,transaction,*,tenant,registration_key,executor_roles=()):
    """Atomic initial adjunct install/issuance; returns pending, never usable context."""
    try:
        if type(host) is not PsycopgHost or type(registration_key) is not bytes or not 1<=len(registration_key)<=256 or type(executor_roles) is not tuple or len(executor_roles)>4 or len(set(executor_roles))!=len(executor_roles) or any(type(r) is not str or not r or '\0' in r or len(r.encode())>63 for r in executor_roles):raise ValueError()
        tenant_bytes=encode_action_tenant_identity(tenant);storage,issuer=_sources();manifest,digest,sources=_release()
    except (ValueError,TypeError,UnicodeError):return Error(ExecutionFailure('execution_obligation','Original bounded shared store registration required'))
    def register(cursor,observed):
        path,identity,owner,actor=_context(cursor);_runtime_inventory(cursor,sources,owner)
        selected_executors=[]
        for role in executor_roles:
            roles=_text_rows(cursor,"SELECT oid::text,rolcanlogin::text,rolsuper::text,rolcreaterole::text,rolcreatedb::text,rolreplication::text,rolbypassrls::text,pg_catalog.pg_has_role(oid,%s::oid,'MEMBER')::text FROM pg_catalog.pg_roles WHERE rolname=%s",(owner,role),1)
            if len(roles)!=1 or roles[0][1:]!=('true','false','false','false','false','false','false'):raise ValueError('Original ordinary native store executor required')
            selected_executors.append(int(roles[0][0]))
        selected_executors=sorted(selected_executors)
        cursor.execute("SELECT pg_catalog.to_regclass('truss.action_store_registration')::oid",prepare=False)
        existing=cursor.fetchmany(2)
        if existing==[(None,)]:
            cursor.execute(storage.decode(),prepare=False);cursor.execute(issuer.decode(),prepare=False)
            cursor.execute('SELECT rolname FROM pg_catalog.pg_roles WHERE oid=%s::oid',(owner,),prepare=False)
            owner_name=cursor.fetchone()[0]
            for statement in ('ALTER TABLE truss.action_store_registration OWNER TO {}','ALTER SEQUENCE truss.action_store_control_seq OWNER TO {}'):
                cursor.execute(sql.SQL(statement).format(sql.Identifier(owner_name)),prepare=False)
            for name,args,language,volatility,secdef,admin in _FUNCTIONS:
                if not admin:cursor.execute(sql.SQL('ALTER FUNCTION truss.'+name+'('+args+') OWNER TO {}').format(sql.Identifier(owner_name)),prepare=False)
            for role in executor_roles:
                roles=_text_rows(cursor,"SELECT oid::text,rolcanlogin::text,rolsuper::text,rolcreaterole::text,rolcreatedb::text,rolreplication::text,rolbypassrls::text,pg_catalog.pg_has_role(oid,%s::oid,'MEMBER')::text FROM pg_catalog.pg_roles WHERE rolname=%s",(owner,role),1)
                if len(roles)!=1 or roles[0][1:]!=('true','false','false','false','false','false','false'):raise ValueError('Original ordinary native store executor required')
                cursor.execute(sql.SQL('GRANT EXECUTE ON FUNCTION truss.observe_action_store_original(bytea),truss.acquire_action_store_source_cut() TO {}').format(sql.Identifier(role)),prepare=False)
                cursor.execute(sql.SQL('GRANT USAGE ON SCHEMA truss TO {}').format(sql.Identifier(role)),prepare=False)
        else:
            cursor.execute('LOCK TABLE ONLY truss.action_store_registration IN SHARE MODE NOWAIT',prepare=False)
            cursor.execute('SELECT count(*) FROM ONLY truss.action_store_registration',prepare=False)
            if cursor.fetchmany(2)!=[(1,)]:raise ValueError('Incomplete existing store requires explicit migration')
        _verify(cursor,owner,selected_executors)
        cursor.execute('SELECT truss.register_action_store_original(%s,%s,%s::pg_catalog.oid[],%s,%s)',(tenant_bytes,registration_key,'{'+','.join(str(x) for x in selected_executors)+'}',manifest['releaseId'],bytes.fromhex(digest)),prepare=False)
        rows=cursor.fetchmany(2)
        if len(rows)!=1:raise ValueError('Original native store issuance required')
        raw=rows[0][0];receipt=_receipt(raw)
        if bytes.fromhex(receipt['tenantIdentityHex'])!=tenant_bytes or bytes.fromhex(receipt['registrationKeyHex'])!=registration_key or receipt['installationId']!=identity or receipt['executorOids']!=[str(x) for x in selected_executors]:raise ValueError('Original namespace issuance correspondence required')
        _restore(cursor,path)
        return PendingActionStoreRegistration(registration_key,tenant_bytes,raw)
    return host._run_operation(transaction,register)


def observe_action_store_in_transaction(host,transaction,*,registration_key):
    """Fresh original receipt observation; current comparison is not authority."""
    if type(host) is not PsycopgHost or type(registration_key) is not bytes or not 1<=len(registration_key)<=256:return Error(ExecutionFailure('execution_obligation','Original registration key required'))
    def observe(cursor,observed):
        _pin_cursor(cursor)
        cursor.execute("SELECT pg_catalog.current_setting('search_path')",prepare=False);path=cursor.fetchone()[0]
        cursor.execute("SELECT pg_catalog.set_config('search_path','pg_catalog,pg_temp',true)",prepare=False);cursor.fetchone()
        # Ordinary executors cannot lock the private table directly. The native
        # observation's row/source closure must be admitted by its trusted caller.
        cursor.execute("SELECT nspowner FROM pg_catalog.pg_namespace WHERE nspname='truss'",prepare=False)
        rows=cursor.fetchmany(2)
        if len(rows)!=1:raise ValueError('Original store installation required')
        rows_owner=rows[0][0]
        _verify(cursor,rows_owner)
        cursor.execute('SELECT truss.observe_action_store_original(%s)',(registration_key,),prepare=False)
        rows=cursor.fetchmany(2)
        if len(rows)!=1:raise ValueError('Original store observation required')
        if rows[0][0] is None:
            _restore(cursor,path);return ActionStoreRegistrationNotObserved(registration_key)
        raw=rows[0][0]
        if type(raw) is not bytes or len(raw)>8388608:raise ValueError('Bounded original store observation required')
        value=json.loads(raw)
        if value.get('interfaceVersion')!='truss.action-store-observation/0.1' or value.get('authority') is not False or value.get('bindingCorrespondence') not in ('matches','fenced'):raise ValueError('Original store observation profile required')
        receipt_bytes=bytes.fromhex(value['receiptHex']);receipt=_receipt(receipt_bytes)
        if bytes.fromhex(receipt['registrationKeyHex'])!=registration_key:raise ValueError('Original receipt registration identity required')
        _verify(cursor,rows_owner,[int(x) for x in receipt['executorOids']])
        _restore(cursor,path)
        return ActionStoreObservation(registration_key,receipt_bytes,bytes.fromhex(receipt['storeIdentityHex']),bytes.fromhex(receipt['tenantIdentityHex']),bytes.fromhex(receipt['epochIdentityHex']),receipt['installationId'],value['bindingCorrespondence'])
    return host._run_operation(transaction,observe)


def verify_action_store_enrollment_context_with_cursor(cursor,store_context,installation_id):
    """Initial trusted quiescent administrative comparison, not a source cut.

    Holding the operational epoch SHARE cut would correctly prohibit later
    routine DDL. This immutable issued-row check therefore does not establish
    current-source closure or authorization. Native runtime release comparison
    uses the current overlay, never immutable genesis release labels. Under
    native immutable issuance/RC visibility, a distinct visible issuer is
    committed; long-lived receipts do not depend on retained CLOG history.
    """
    store_context=_capture_action_store_context(store_context)
    if _text_rows(cursor,"SELECT pg_catalog.current_setting('server_version_num'),pg_catalog.current_setting('transaction_isolation'),pg_catalog.current_setting('transaction_read_only'),pg_catalog.current_setting('role')",limit=1)!=[('180006','read committed','off','none')]:
        raise ValueError('Original native administrative enrollment context required')
    if not store_context.binding_matches:raise ValueError('Original unfenced store comparison required')
    cursor.execute('LOCK TABLE ONLY truss.action_store_registration IN SHARE MODE NOWAIT', prepare=False)
    issued = _text_rows(cursor, """SELECT pg_catalog.encode(r.initial_receipt_bytes,'hex'),
        pg_catalog.encode(r.store_identity,'hex'),pg_catalog.encode(r.tenant_identity,'hex'),
        pg_catalog.encode(r.epoch_identity,'hex'),r.installation_id::text
        FROM ONLY truss.action_store_registration r
        JOIN truss.runtime_current_installation() i ON i.installation_id=r.installation_id AND i.singleton
        WHERE r.singleton AND r.registration_key=%s
        AND r.database_oid=(SELECT oid FROM pg_catalog.pg_database WHERE datname=pg_catalog.current_database())
        AND r.schema_oid=(SELECT oid FROM pg_catalog.pg_namespace WHERE nspname='truss')
        AND r.postmaster_started_at=pg_catalog.pg_postmaster_start_time()
        AND r.runtime_release_id=i.release_id AND r.runtime_release_sha256=pg_catalog.decode(i.release_sha256,'hex')
        AND r.initial_receipt_bytes=truss.action_store_original_receipt(r)
        AND r.issuer_xid IS DISTINCT FROM pg_catalog.pg_current_xact_id_if_assigned()
        FOR SHARE OF r NOWAIT""", (store_context.registration_key,), 1)
    if issued != [(store_context.receipt_bytes.hex(),store_context.store_identity.hex(),store_context.tenant_identity.hex(),
                   store_context.epoch_identity.hex(),store_context.installation_id)]:
        raise ValueError('Original committed issued store enrollment required')
    if store_context.installation_id != installation_id:
        raise ValueError('Original issued store installation required')


def verify_action_store_context_with_cursor(cursor,context):
    """Exact native issued-row comparison under source custody, never authorization."""
    context=_capture_action_store_context(context)
    if not context.binding_matches:raise ValueError('Original current issued store comparison required')
    cursor.execute('SELECT truss.observe_action_store_original(%s)',(context.registration_key,),prepare=False)
    rows=cursor.fetchmany(2)
    if len(rows)!=1 or type(rows[0][0]) is not bytes:raise ValueError('Original committed store observation required')
    value=json.loads(rows[0][0]);raw=bytes.fromhex(value['receiptHex']);receipt=_receipt(raw)
    expected=ActionStoreObservation(context.registration_key,raw,bytes.fromhex(receipt['storeIdentityHex']),bytes.fromhex(receipt['tenantIdentityHex']),bytes.fromhex(receipt['epochIdentityHex']),receipt['installationId'],value['bindingCorrespondence'])
    if expected!=context or not expected.binding_matches:raise ValueError('Complete original issued store correspondence required')
    return None
