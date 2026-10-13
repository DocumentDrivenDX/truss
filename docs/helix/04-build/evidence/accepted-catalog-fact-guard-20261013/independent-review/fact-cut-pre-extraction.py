"""Private flat-table/graph-store fact cuts; no authority or public policy API."""
from dataclasses import dataclass
from ._psycopg_epoch_cut import _run_fenced_epoch_operation


@dataclass(frozen=True)
class _FactColumnComparison:
    name: str
    number: int
    type_oid: int
    type_modifier: int
    not_null: bool
    collation_oid: int
    generated: str = ''
    identity: str = ''


@dataclass(frozen=True)
class _FactRelationComparison:
    schema: str
    name: str
    oid: int
    owner_oid: int
    guard_source: str
    columns: tuple = ()


def _run_fenced_fact_operation(host, transaction, epoch_comparison, relations, callback, *, ddl_barrier=None):
    """Reacquire declared plain-table cuts inside the original epoch scope.

    Independent admitted mapping/installed trigger closure is required. This
    excludes table DML only, not roles, grants, config or other source changes.
    """
    if type(relations) is not tuple or not 1 <= len(relations) <= 32:
        raise ValueError('Bounded exact fact relation tuple required')
    recipe=[]
    for relation in relations:
        if type(relation) is not _FactRelationComparison:
            raise ValueError('Exact relation comparison required')
        schema,name,oid,owner,guard_source=relation.schema,relation.name,relation.oid,relation.owner_oid,relation.guard_source
        if any(type(v) is not str or not 1 <= len(v.encode('utf8')) <= 63 or '\x00' in v for v in (schema,name)):
            raise ValueError('Exact bounded native relation identifiers required')
        if any(type(v) is not int or not 1 <= v <= 4294967295 for v in (oid,owner)):
            raise ValueError('Exact native relation and owner OIDs required')
        if type(guard_source) is not str or not 1 <= len(guard_source.encode('utf8')) <= 65536:
            raise ValueError('Bounded original guard source comparison required')
        if type(relation.columns) is not tuple or len(relation.columns)>1600:
            raise ValueError('Bounded exact column comparisons required')
        columns=[]
        for column in relation.columns:
            if type(column) is not _FactColumnComparison:
                raise ValueError('Exact native column comparison required')
            n,a,t,m,nn,c,g,i=(column.name,column.number,column.type_oid,column.type_modifier,
                            column.not_null,column.collation_oid,column.generated,column.identity)
            if type(n) is not str or not 1<=len(n.encode('utf8'))<=63 or '\x00' in n:
                raise ValueError('Exact native column name required')
            if (type(a) is not int or not 1<=a<=1600 or type(t) is not int or not 1<=t<=4294967295
                    or type(m) is not int or not -2147483648<=m<=2147483647
                    or type(nn) is not bool or type(c) is not int or not 0<=c<=4294967295
                    or type(g) is not str or g not in ('','s') or type(i) is not str or i not in ('','a','d')):
                raise ValueError('Exact selected PostgreSQL16 column descriptor required')
            columns.append((n,a,t,m,nn,c,g,i))
        if len({c[0] for c in columns})!=len(columns) or len({c[1] for c in columns})!=len(columns):
            raise ValueError('Duplicate native column binding')
        recipe.append((schema,name,oid,owner,guard_source,tuple(columns)))
    recipe=tuple(sorted(recipe,key=lambda r:r[2]))
    if len({r[2] for r in recipe}) != len(recipe) or len({r[:2] for r in recipe}) != len(recipe):
        raise ValueError('Duplicate fact relation binding')
    if not callable(callback):raise ValueError('Private fact callback required')

    def acquire(cursor):
        from psycopg import sql
        for schema,name,oid,owner,guard_source,columns in recipe:
            cursor.execute(sql.SQL('LOCK TABLE ONLY {} IN SHARE MODE NOWAIT').format(sql.Identifier(schema,name)),prepare=False)
            cursor.execute("SELECT c.oid::pg_catalog.text,c.relowner::pg_catalog.text,c.relkind::pg_catalog.text,c.relpersistence::pg_catalog.text,c.relrowsecurity::pg_catalog.text,c.relforcerowsecurity::pg_catalog.text,"
                           "EXISTS(SELECT 1 FROM pg_catalog.pg_inherits i WHERE i.inhrelid OPERATOR(pg_catalog.=) c.oid OR i.inhparent OPERATOR(pg_catalog.=) c.oid)::pg_catalog.text "
                           "FROM pg_catalog.pg_class c JOIN pg_catalog.pg_namespace n ON n.oid OPERATOR(pg_catalog.=) c.relnamespace WHERE n.nspname OPERATOR(pg_catalog.=) %s AND c.relname OPERATOR(pg_catalog.=) %s",
                           (schema,name),prepare=False,binary=False)
            if (cursor.description is None or len(cursor.description)!=7
                    or any(d.type_code!=25 for d in cursor.description)):
                raise ValueError('Exact native TEXT relation descriptors required')
            rows=cursor.fetchmany(2)
            if rows != [(str(oid),str(owner),'r','p','false','false','false')]:
                raise ValueError('Exact permanent non-inherited unfiltered fact table required')
            cursor.execute("SELECT t.tgenabled::pg_catalog.text,t.tgtype::pg_catalog.text,t.tgnargs::pg_catalog.text,pg_catalog.encode(t.tgargs,'hex'),"
                           "t.tgisinternal::pg_catalog.text,(t.tgqual IS NULL)::pg_catalog.text,p.proowner::pg_catalog.text,p.prosecdef::pg_catalog.text,"
                           "p.provolatile::pg_catalog.text,pg_catalog.to_jsonb(p.proconfig)::pg_catalog.text,p.prosrc,"
                           "EXISTS(SELECT 1 FROM pg_catalog.aclexplode(coalesce(p.proacl,pg_catalog.acldefault('f',p.proowner))) a WHERE a.grantee OPERATOR(pg_catalog.=) 0 AND a.privilege_type OPERATOR(pg_catalog.=) 'EXECUTE')::pg_catalog.text "
                           "FROM pg_catalog.pg_trigger t JOIN pg_catalog.pg_proc p ON p.oid OPERATOR(pg_catalog.=) t.tgfoid WHERE t.tgrelid OPERATOR(pg_catalog.=) %s::pg_catalog.oid "
                           "AND t.tgname OPERATOR(pg_catalog.=) 'fact_write_fence' AND p.oid OPERATOR(pg_catalog.=) 'truss.runtime_fence_authorization_fact_write()'::pg_catalog.regprocedure",
                           (str(oid),),prepare=False,binary=False)
            if (cursor.description is None or len(cursor.description)!=12
                    or any(d.type_code!=25 for d in cursor.description)):
                raise ValueError('Exact native TEXT guard descriptors required')
            guards=cursor.fetchmany(2)
            expected=('A','62','0','','false','true',str(owner),'false','v',
                      '["search_path=pg_catalog, pg_temp"]',guard_source,'false')
            if guards != [expected]:
                raise ValueError('Exact installed ALWAYS fact guard required')
            for n,a,t,m,nn,c,g,i in columns:
                cursor.execute("SELECT attname::pg_catalog.text,attnum::pg_catalog.text,atttypid::pg_catalog.text,"
                               "atttypmod::pg_catalog.text,attnotnull::pg_catalog.text,attcollation::pg_catalog.text,"
                               "attgenerated::pg_catalog.text,attidentity::pg_catalog.text,attisdropped::pg_catalog.text "
                               "FROM pg_catalog.pg_attribute WHERE attrelid OPERATOR(pg_catalog.=) %s::pg_catalog.oid "
                               "AND attnum OPERATOR(pg_catalog.=) %s::pg_catalog.int2",
                               (str(oid),str(a)),prepare=False,binary=False)
                if (cursor.description is None or len(cursor.description)!=9
                        or any(d.type_code!=25 for d in cursor.description)):
                    raise ValueError('Exact native TEXT column descriptors required')
                actual=cursor.fetchmany(2)
                expected=(n,str(a),str(t),str(m),'true' if nn else 'false',str(c),g,i,'false')
                if actual != [expected]:
                    raise ValueError('Original native field descriptor correspondence required')
        return callback(cursor)
    if ddl_barrier is not None:
        from ._psycopg_epoch_cut import _run_ddl_fenced_epoch_operation
        return _run_ddl_fenced_epoch_operation(host,transaction,epoch_comparison,ddl_barrier,acquire)
    return _run_fenced_epoch_operation(host,transaction,epoch_comparison,acquire)
