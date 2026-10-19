# SPDX-License-Identifier: MIT OR Apache-2.0
"""Private source-bound preparation under a native profile guard; no SQL permit.

The host supplies original compiler code and source inputs. Neither this Python
object nor a matching guard row authenticates their issuer or installed mapping.
Prepared output cannot be passed to the ordinary compiled-query executor.
"""
from dataclasses import dataclass, field
from hashlib import sha256
import inspect
from .weft import _decode, CompileRefusal
from .execution import Error, ExecutionFailure
from .psycopg_host import PsycopgHost
from .catalog_runtime import _pin_cursor
from ._installation_privileges import installation_administrator_with_cursor

_FIELDS=('modules','policyJson','ontologyJson','queryProfileJson','bindingJson',
         'backendId','backendVersion','targetProfile','readProfile')
_KEYS={'interfaceVersion','sql','parameters',*_FIELDS}

def _signature(value):
    # This is transport identity, not interpretation of UMF/policy/SQL meaning.
    # Numeric carriers are not needed in model pins or read-profile metadata.
    if value is None:return ('null',)
    if type(value) is str:return ('string',value)
    if type(value) is list:return ('array',tuple(_signature(v) for v in value))
    if type(value) is dict:return ('object',tuple(sorted((k,_signature(v)) for k,v in value.items())))
    raise CompileRefusal('mapping_source','Exact string source/pin metadata required')

def _request(original):
    text,value=_decode(original,4_000_000,'mapping_input')
    if (type(value) is not dict or set(value)-_KEYS
            or value.get('interfaceVersion')!='weft-security-mapping/0.1.0'
            or not {'sql','parameters',*(_FIELDS[:-1])}<=set(value)
            or value.get('backendId')!='truss.postgresql'):
        raise CompileRefusal('mapping_input','Original closed Truss mapping request required')
    modules=value.get('modules')
    if (type(modules) is not list or not 1<=len(modules)<=256
            or any(type(m) is not dict or set(m)!={'documentJson','pin','selectedModuleIds'}
                   or type(m.get('pin')) is not dict or set(m['pin'])!={'documentId','revision','umfVersion','sha256'}
                   or any(type(v) is not str or not v for v in m['pin'].values())
                   or type(m.get('documentJson')) is not str
                   or type(m.get('selectedModuleIds')) is not list
                   or any(type(v) is not str or not v for v in m['selectedModuleIds']) for m in modules)):
        raise CompileRefusal('mapping_input','Original model source/pin transport required')
    return text,value

@dataclass(frozen=True,slots=True)
class PreparedSecurityMapping:
    original_request:bytes
    original_response:bytes
    security_ready:bool=field(default=False,init=False)
    accepted_catalog_assessment:bytes|None=None
    native_dependencies:bytes|None=None
    native_guard:tuple[bytes,bytes,int]|None=None

class SecurityMappingBoundary:
    """Capture original sources once; changing SQL/parameters cannot rebind them.

    This private boundary is not compiler-code authentication, policy issuance,
    physical mapping validation or an executable artifact constructor.
    """
    def __init__(self,prepare_function,original_reference:bytes):
        if (not callable(prepare_function) or any(check(candidate)
                for candidate in (prepare_function,getattr(prepare_function,'__call__',None))
                for check in (inspect.iscoroutinefunction,inspect.isgeneratorfunction,inspect.isasyncgenfunction))):
            raise CompileRefusal('mapping_compiler','Original synchronous compiler required')
        _,reference=_request(original_reference)
        self._source=tuple(_signature(reference.get(k)) for k in _FIELDS)
        for key in _FIELDS[1:-1]:
            if type(reference[key]) is not str or not reference[key]:raise CompileRefusal('mapping_source','Original source strings required')
        self._profile=reference['queryProfileJson'].encode('utf8')
        self._expected={key:sha256(reference[source].encode('utf8')).hexdigest() for key,source in
                        [('policySha256','policyJson'),('ontologySha256','ontologyJson')]}
        self._binding=(reference['backendId'],reference['backendVersion'],reference['targetProfile'],sha256(reference['bindingJson'].encode('utf8')).hexdigest())
        self._pins=_signature([entry['pin'] for entry in reference['modules']])
        self._prepare=prepare_function
    @property
    def original_profile(self):return self._profile
    def prepare(self,original_request:bytes)->PreparedSecurityMapping:
        text,request=_request(original_request)
        if tuple(_signature(request.get(k)) for k in _FIELDS)!=self._source:
            raise CompileRefusal('mapping_source','Original deployment sources changed before compiler invocation')
        raw=self._prepare(text)
        if inspect.isgenerator(raw) or inspect.iscoroutine(raw):
            raw.close()
            raise CompileRefusal('mapping_response','Deferred compiler response refused')
        if type(raw) is not str:raise CompileRefusal('mapping_response','Original completed compiler response required')
        original_response=raw.encode('utf8',errors='strict');_,response=_decode(original_response,16_000_000,'mapping_response')
        if (type(response) is not dict or response.get('interfaceVersion')!='weft-security-mapping/0.1.0'
                or response.get('status')!='prepared' or response.get('securityReady') is not False
                or set(response)!={'interfaceVersion','status','securityReady','handoff'}):
            raise CompileRefusal('mapping_response','Non-ready original prepared mapping required')
        h=response['handoff']
        if (type(h) is not dict
                or set(h)!={'version','profile','modelPins','policySha256','ontologySha256','binding','sqlSha256','applicationPlan','securityLogicalPlan','uses','scans'}
                or type(h.get('applicationPlan')) is not dict or type(h.get('securityLogicalPlan')) is not dict
                or type(h.get('uses')) is not list or type(h.get('scans')) is not list
                or h.get('version')!='weft.security.mapping-handoff/0.2.0'
                or any(h.get(k)!=v for k,v in self._expected.items())
                or _signature(h.get('modelPins'))!=self._pins
                or type(h.get('profile')) is not dict or h['profile'].get('sha256')!=sha256(self._profile).hexdigest()
                or type(h.get('binding')) is not dict
                or tuple(h['binding'].get(k) for k in ('backendId','backendVersion','targetProfile','sha256'))!=self._binding
                or type(request['sql']) is not str or h.get('sqlSha256')!=sha256(request['sql'].encode('utf8')).hexdigest()):
            raise CompileRefusal('mapping_response','Original handoff source correspondence required')
        return PreparedSecurityMapping(original_request,original_response)


def prepare_security_mapping_in_transaction(host,transaction,*,boundary,installation_identity,expected_generation,original_request,require_accepted_catalog=False):
    """Selected administrative guard coupling only; caller owns outer settlement."""
    if (type(require_accepted_catalog) is not bool or type(host) is not PsycopgHost or type(boundary) is not SecurityMappingBoundary
            or type(installation_identity) is not bytes or not 1<=len(installation_identity)<=32768
            or type(expected_generation) is not int or not 1<=expected_generation<=9223372036854775807
            or not 1<=len(boundary.original_profile)<=32768):
        return Error(ExecutionFailure('execution_obligation','Original bounded mapping preparation required'))
    def prepare(cursor,observed):
        _pin_cursor(cursor)
        cursor.execute("SELECT pg_catalog.current_setting('search_path')",prepare=False)
        paths=cursor.fetchmany(2)
        if len(paths)!=1 or type(paths[0][0]) is not str:raise ValueError('Original mapping caller path required')
        original_path=paths[0][0]
        cursor.execute("SELECT pg_catalog.set_config('search_path','pg_catalog, pg_temp',true)",prepare=False)
        cursor.execute('SELECT installation_id::text,owner_oid FROM truss.catalog_runtime_installation FOR SHARE',prepare=False)
        installation=cursor.fetchmany(2)
        if len(installation)!=1 or installation[0][0].encode('utf8')!=installation_identity:raise ValueError('Original mapping installation required')
        installation_administrator_with_cursor(cursor,installation[0][1])
        cursor.execute("SELECT pg_catalog.current_setting('server_version_num'),pg_catalog.current_setting('transaction_isolation'),pg_catalog.current_setting('transaction_read_only')",prepare=False)
        if cursor.fetchmany(2)!=[('180006','read committed','off')]:raise ValueError('Original read-write read-committed mapping cut required')
        cursor.execute('SELECT rev FROM truss.schema_head WHERE id=1 FOR SHARE',prepare=False)
        if len(cursor.fetchmany(2))!=1:raise ValueError('Original mapping head required')
        expected=(installation_identity,boundary.original_profile,expected_generation)
        def home():
            cursor.execute('''SELECT c.oid,c.relkind::pg_catalog.text,c.relpersistence::pg_catalog.text,
                c.relowner,n.nspowner,c.relrowsecurity,c.relforcerowsecurity,
                NOT EXISTS(SELECT 1 FROM pg_catalog.aclexplode(COALESCE(c.relacl,pg_catalog.acldefault('r',c.relowner))) a
                  WHERE a.grantee<>c.relowner OR a.grantor<>c.relowner)
                AND NOT EXISTS(SELECT 1 FROM pg_catalog.pg_attribute column_acl
                  CROSS JOIN LATERAL pg_catalog.aclexplode(column_acl.attacl) a
                  WHERE column_acl.attrelid=c.oid AND column_acl.attnum>0 AND NOT column_acl.attisdropped
                    AND (a.grantee<>c.relowner OR a.grantor<>c.relowner))
                FROM pg_catalog.pg_class c JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace
                WHERE n.nspname='truss' AND c.relname='policy_generation_guard' ''',prepare=False)
            rows=cursor.fetchmany(2)
            if len(rows)!=1 or rows[0][1:]!=('r','p',installation[0][1],installation[0][1],False,False,True):
                raise ValueError('Original private persistent mapping guard home required')
            return rows[0][0]
        original_home=home()
        def guard(lock=''):
            cursor.execute('SELECT installation_identity_bytes,policy_profile_bytes,generation FROM truss.policy_generation_guard WHERE singleton=1'+lock,prepare=False)
            if (cursor.description is None or tuple(c.type_code for c in cursor.description)!=(17,17,20)
                    or tuple(c.name for c in cursor.description)!=('installation_identity_bytes','policy_profile_bytes','generation')):
                raise ValueError('Original mapping profile/generation guard required')
            rows=cursor.fetchmany(2)
            if (len(rows)!=1 or tuple(type(v) for v in rows[0])!=(bytes,bytes,int) or rows!=[expected]):
                raise ValueError('Original mapping profile/generation guard required')
        guard(' FOR SHARE')
        assessment=None
        if require_accepted_catalog:
            from ._security_catalog_assessment import capture_accepted_catalog
            assessment=capture_accepted_catalog(cursor,original_request)
        result=boundary.prepare(original_request)
        # A genuine owner compiler is pure. Reassert the native inspection
        # environment before the synthetic late-mutation endpoint controls.
        _pin_cursor(cursor)
        cursor.execute("SELECT pg_catalog.set_config('search_path','pg_catalog, pg_temp',true)",prepare=False)
        guard()
        if require_accepted_catalog:
            if capture_accepted_catalog(cursor,original_request)!=assessment:raise ValueError('Accepted catalog changed during compiler preparation')
            from ._security_catalog_mapping import map_catalog_dependencies
            dependencies=map_catalog_dependencies(assessment,result.original_response,original_request)
            result=PreparedSecurityMapping(result.original_request,result.original_response,assessment,dependencies,expected)
        if home()!=original_home:raise ValueError('Original mapping guard home changed')
        cursor.execute("SELECT pg_catalog.set_config('search_path',%s,true)",(original_path,),prepare=False)
        if cursor.fetchmany(2)!=[(original_path,)]:raise ValueError('Original mapping caller path restoration required')
        return result
    return host._run_operation(transaction,prepare)
