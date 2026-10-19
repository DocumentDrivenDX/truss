# SPDX-License-Identifier: MIT OR Apache-2.0
"""Private installation of original UMF-exported preparation seal storage.

Trusted direct superuser, initial administrative quiescence and original runtime
are premises. No ordinary grants, seal writer, authority or admission provider.
The metadata epoch does not implicitly admit this new home. Caller owns commit.
"""
from dataclasses import dataclass
from hashlib import sha256
from importlib.resources import files
from psycopg import sql
from .execution import Error, ExecutionFailure
from .psycopg_host import PsycopgHost
from .catalog_runtime import _release, _pin_cursor
from ._preparation_source_epoch import _context, _restore, _runtime_inventory

_SOURCE_SHA256 = '235f2ce982eeda53eaee09f7608a388f96a815cde5354f4ce6db9bb3091422fe'
_TABLE = 'runtime_preparation_seal'
_SEQUENCE = 'runtime_preparation_seal_seq'
_COLUMNS = (
    ('seal_id',20,True,'',"nextval('truss.runtime_preparation_seal_seq'::regclass)"),
    ('attempt_id',2950,True,'',None), ('installation_id',2950,True,'',None),
    ('store_epoch',25,True,'',None), ('initiator_oid',26,True,'',None),
    ('writer_xid',5069,True,'',None), ('data_backend_pid',23,True,'',None),
    ('data_context_bytes',17,True,'',None), ('authority_context_bytes',17,True,'',None),
    ('source_context_bytes',17,True,'',None), ('action_bytes',17,True,'',None),
    ('selection_bytes',17,True,'',None), ('manifest_bytes',17,True,'',None),
    ('cut_bytes',17,True,'',None), ('profile_bytes',17,True,'',None),
    ('manifest_sha256',17,False,'s','sha256(manifest_bytes)'),
    ('sealed_at',1184,True,'','clock_timestamp()'),
)
_CHECKS = ["(seal_id > 0)", "(initiator_oid <> '0'::oid)", "(writer_xid > '0'::xid8)",
           '(data_backend_pid > 0)', 'isfinite(sealed_at)']
for _field,_maximum in (('store_epoch',1024),('data_context_bytes',65536),
        ('authority_context_bytes',16777216),('source_context_bytes',16777216),
        ('action_bytes',1048576),('selection_bytes',16777216),('manifest_bytes',16777216),
        ('cut_bytes',65536),('profile_bytes',65536)):
    _CHECKS.append('((octet_length('+_field+') >= 1) AND (octet_length('+_field+') <= '+str(_maximum)+'))')


@dataclass(frozen=True, slots=True)
class PendingPreparationSealStorage:
    installation_id: str
    owner_oid: int
    table_oid: int
    sequence_oid: int
    source_sha256: str
    status: str = 'pending_commit'
    security_ready: bool = False


def _private_acl(cursor, kind, oid, owner, privileges):
    # Fixed catalog names only; all actual ACL entries must be original owner.
    relation = kind != 'type'
    catalog, acl, owner_column = ('pg_class','relacl','relowner') if relation else ('pg_type','typacl','typowner')
    default = 's' if kind == 'sequence' else 'r' if relation else 'T'
    cursor.execute('SELECT a.grantee,a.grantor,a.privilege_type,a.is_grantable FROM pg_catalog.'+catalog+
        ' c CROSS JOIN LATERAL pg_catalog.aclexplode(coalesce(c.'+acl+',pg_catalog.acldefault(%s::pg_catalog."char",c.'+owner_column+')) ) a WHERE c.oid=%s::pg_catalog.oid ORDER BY a.privilege_type', (default,oid), prepare=False)
    if cursor.fetchmany(len(privileges)+1) != [(owner,owner,p,False) for p in sorted(privileges)]:
        raise ValueError('Exact owner-only preparation seal '+kind+' ACL required')


def verify_preparation_seal_storage_with_cursor(cursor, *, owner_oid):
    """Installed storage comparison only, under original admin/DDL custody."""
    _pin_cursor(cursor)
    cursor.execute("SELECT c.oid,c.relname,c.relkind,c.relpersistence,c.relowner,c.relrowsecurity,c.relforcerowsecurity,c.reltype,EXISTS(SELECT 1 FROM pg_catalog.pg_inherits i WHERE i.inhrelid=c.oid OR i.inhparent=c.oid) FROM pg_catalog.pg_class c JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='truss' AND c.relname=ANY(%s::pg_catalog.text[]) ORDER BY c.relname", ([_TABLE,_SEQUENCE],), prepare=False)
    rows = cursor.fetchmany(3)
    if len(rows)!=2 or rows[0][1:7]!=(_TABLE,'r','p',owner_oid,False,False) or rows[0][8] is not False or rows[1][1:7]!=(_SEQUENCE,'S','p',owner_oid,False,False) or rows[1][8] is not False:
        raise ValueError('Original private seal table and sequence required')
    table_oid, type_oid, sequence_oid = rows[0][0],rows[0][7],rows[1][0]
    cursor.execute("SELECT typowner,typtype,typrelid FROM pg_catalog.pg_type WHERE oid=%s::pg_catalog.oid", (type_oid,), prepare=False)
    if cursor.fetchmany(2)!=[(owner_oid,'c',table_oid)]: raise ValueError('Original seal composite type ownership required')
    cursor.execute('SELECT a.attnum,a.attname,a.atttypid,a.atttypmod,a.attnotnull,a.attgenerated,a.attidentity,a.attacl,a.attisdropped,pg_catalog.pg_get_expr(d.adbin,d.adrelid),coalesce(n.nspname,\'\'),coalesce(c.collname,\'\') FROM pg_catalog.pg_attribute a LEFT JOIN pg_catalog.pg_attrdef d ON d.adrelid=a.attrelid AND d.adnum=a.attnum LEFT JOIN pg_catalog.pg_collation c ON c.oid=a.attcollation LEFT JOIN pg_catalog.pg_namespace n ON n.oid=c.collnamespace WHERE a.attrelid=%s::pg_catalog.oid AND a.attnum>0 ORDER BY a.attnum', (table_oid,), prepare=False)
    columns = cursor.fetchmany(18)
    expected = [(i,name,typ,-1,required,generated,'',None,False,default,'pg_catalog' if name=='store_epoch' else '', 'C' if name=='store_epoch' else '') for i,(name,typ,required,generated,default) in enumerate(_COLUMNS,1)]
    if columns!=expected: raise ValueError('Exact original seal column/default/generated profile required')
    cursor.execute('SELECT seqtypid,seqstart,seqincrement,seqmax,seqmin,seqcache,seqcycle FROM pg_catalog.pg_sequence WHERE seqrelid=%s::pg_catalog.oid', (sequence_oid,), prepare=False)
    if cursor.fetchmany(2)!=[(20,1,1,9223372036854775807,1,1,False)]: raise ValueError('Original metadata-only seal sequence required')
    cursor.execute("SELECT d.refobjid FROM pg_catalog.pg_depend d JOIN pg_catalog.pg_attrdef a ON d.classid='pg_catalog.pg_attrdef'::pg_catalog.regclass AND d.objid=a.oid WHERE a.adrelid=%s::pg_catalog.oid AND a.adnum=1 AND d.refclassid='pg_catalog.pg_class'::pg_catalog.regclass AND d.deptype='n'", (table_oid,), prepare=False)
    if cursor.fetchmany(2)!=[(sequence_oid,)]: raise ValueError('Original new seal sequence default dependency required')
    cursor.execute("SELECT c.contype,c.convalidated,c.condeferrable,c.condeferred,c.conkey,c.confrelid,c.confkey,c.confupdtype,c.confdeltype,c.confmatchtype,pg_catalog.pg_get_expr(c.conbin,c.conrelid),c.conindid FROM pg_catalog.pg_constraint c WHERE c.conrelid=%s::pg_catalog.oid AND c.contype<>'n' ORDER BY c.contype,c.oid", (table_oid,), prepare=False)
    constraints=cursor.fetchmany(18)
    checks=[r for r in constraints if r[0]=='c']; keys=[r for r in constraints if r[0] in ('p','u')]; fks=[r for r in constraints if r[0]=='f']
    if (len(constraints)!=17 or len(checks)!=14 or sorted(r[10] for r in checks)!=sorted(_CHECKS)
            or any(r[1:4]!=(True,False,False) for r in constraints) or len(keys)!=2
            or {(r[0],tuple(r[4])) for r in keys}!={('p',(1,)),('u',(2,))} or len(fks)!=1):
        raise ValueError('Complete original seal checks and immediate keys required')
    cursor.execute("SELECT c.oid,a.attnum FROM pg_catalog.pg_class c JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace JOIN pg_catalog.pg_attribute a ON a.attrelid=c.oid WHERE n.nspname='truss' AND c.relname='catalog_runtime_installation' AND a.attname='installation_id' AND NOT a.attisdropped", prepare=False)
    target=cursor.fetchmany(2)
    if len(target)!=1 or fks[0][4:10]!=([3],target[0][0],[target[0][1]],'a','a','s'):
        raise ValueError('Exact original installation seal foreign key required')
    for key in keys:
        cursor.execute('SELECT i.indisunique,i.indisprimary,i.indisvalid,i.indisready,i.indimmediate,i.indnkeyatts,i.indnatts,i.indkey::pg_catalog.text,i.indoption::pg_catalog.text,i.indpred IS NULL,i.indexprs IS NULL,i.indnullsnotdistinct,am.amname,n.nspname FROM pg_catalog.pg_index i JOIN pg_catalog.pg_class c ON c.oid=i.indexrelid JOIN pg_catalog.pg_am am ON am.oid=c.relam JOIN pg_catalog.pg_opclass o ON o.oid=i.indclass[0] JOIN pg_catalog.pg_namespace n ON n.oid=o.opcnamespace WHERE i.indexrelid=%s::pg_catalog.oid AND i.indrelid=%s::pg_catalog.oid', (key[11],table_oid), prepare=False)
        if cursor.fetchmany(2)!=[(True,key[0]=='p',True,True,True,1,1,str(key[4][0]),'0',True,True,False,'btree','pg_catalog')]:
            raise ValueError('Original valid immediate seal backing index required')
    cursor.execute("SELECT oid FROM pg_catalog.pg_proc WHERE oid='truss.catalog_immutable()'::pg_catalog.regprocedure AND proowner=%s::pg_catalog.oid", (owner_oid,), prepare=False)
    routine=cursor.fetchmany(2)
    if len(routine)!=1: raise ValueError('Original immutable runtime helper required')
    cursor.execute('SELECT tgname,tgfoid,tgenabled,tgtype,tgnargs,tgargs,tgqual IS NULL,tgisinternal,tgconstraint,tgdeferrable,tginitdeferred FROM pg_catalog.pg_trigger WHERE tgrelid=%s::pg_catalog.oid AND NOT tgisinternal', (table_oid,), prepare=False)
    if cursor.fetchmany(2)!=[('runtime_preparation_seal_immutable',routine[0][0],'A',58,0,b'',True,False,0,False,False)]:
        raise ValueError('Exact original ALWAYS statement immutability trigger required')
    _private_acl(cursor,'table',table_oid,owner_oid,('SELECT','INSERT','UPDATE','DELETE','TRUNCATE','REFERENCES','TRIGGER','MAINTAIN'))
    _private_acl(cursor,'sequence',sequence_oid,owner_oid,('SELECT','UPDATE','USAGE'))
    _private_acl(cursor,'type',type_oid,owner_oid,('USAGE',))
    return table_oid,sequence_oid


def bootstrap_preparation_seal_storage_in_transaction(host, transaction):
    if type(host) is not PsycopgHost:
        return Error(ExecutionFailure('execution_obligation','Original native seal storage installer required'))
    raw=files('truss').joinpath('_security_bootstrap','preparation-seal-storage.sql').read_bytes()
    if sha256(raw).hexdigest()!=_SOURCE_SHA256:
        return Error(ExecutionFailure('execution_obligation','Original UMF seal owner export required'))
    _,_,sources=_release()
    def install(cursor,observed):
        path,identity,owner,actor=_context(cursor)
        _runtime_inventory(cursor,sources,owner)
        cursor.execute("SELECT n.nspowner,r.rolname FROM pg_catalog.pg_namespace n JOIN pg_catalog.pg_roles r ON r.oid=n.nspowner WHERE n.nspname='truss'", prepare=False)
        namespace=cursor.fetchmany(2)
        if len(namespace)!=1 or namespace[0][0]!=owner: raise ValueError('Original seal runtime namespace owner required')
        cursor.execute("SELECT c.oid FROM pg_catalog.pg_class c JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='truss' AND c.relname=ANY(%s::pg_catalog.text[])", ([_TABLE,_SEQUENCE],), prepare=False)
        if cursor.fetchmany(3): raise ValueError('Existing seal storage requires explicit migration')
        cursor.execute("SELECT t.oid FROM pg_catalog.pg_type t JOIN pg_catalog.pg_namespace n ON n.oid=t.typnamespace WHERE n.nspname='truss' AND t.typname=ANY(%s::pg_catalog.text[])", ([_TABLE,'_'+_TABLE],), prepare=False)
        if cursor.fetchmany(3): raise ValueError('Existing seal types require explicit migration')
        cursor.execute(raw.decode('utf8'),prepare=False)
        cursor.execute(sql.SQL('ALTER TABLE truss.runtime_preparation_seal OWNER TO {}').format(sql.Identifier(namespace[0][1])),prepare=False)
        cursor.execute(sql.SQL('ALTER SEQUENCE truss.runtime_preparation_seal_seq OWNER TO {}').format(sql.Identifier(namespace[0][1])),prepare=False)
        table_oid,sequence_oid=verify_preparation_seal_storage_with_cursor(cursor,owner_oid=owner)
        _restore(cursor,path)
        return PendingPreparationSealStorage(identity,owner,table_oid,sequence_oid,_SOURCE_SHA256)
    return host._run_operation(transaction,install)
