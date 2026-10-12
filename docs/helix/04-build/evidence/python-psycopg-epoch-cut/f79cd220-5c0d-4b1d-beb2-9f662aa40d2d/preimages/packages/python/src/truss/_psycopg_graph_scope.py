"""Private original graph-scope registration/readback, never caller authorization."""
from dataclasses import dataclass
import json
from ._psycopg_epoch_cut import _run_fenced_epoch_operation


@dataclass(frozen=True)
class _GraphScopeComparison:
    association_ids: tuple
    evidence: bytes


def _run_graph_scope_operation(host, transaction, epoch, comparison, callback):
    if type(comparison) is not _GraphScopeComparison:
        raise ValueError('Exact original graph scope comparison required')
    ids,evidence=comparison.association_ids,comparison.evidence
    if (type(ids) is not tuple or not 1 <= len(ids) <= 32
            or any(type(v) is not int or not 1 <= v <= 2147483647 for v in ids)
            or len(set(ids)) != len(ids) or type(evidence) is not bytes
            or not 1 <= len(evidence) <= 65536 or not callable(callback)):
        raise ValueError('Bounded original graph scope recipe required')
    ids=tuple(sorted(ids))

    def acquire(c):
        from psycopg.types.numeric import IntDumper
        from psycopg.types.string import BytesDumper
        from psycopg.types.array import ListDumper
        c.adapters.register_dumper(int,IntDumper)
        c.adapters.register_dumper(bytes,BytesDumper)
        c.adapters.register_dumper(list,ListDumper)
        c.execute('LOCK TABLE ONLY truss.edge IN SHARE MODE NOWAIT',prepare=False)
        c.execute("SELECT pg_catalog.pg_current_xact_id()::pg_catalog.text,"
                  "(SELECT oid::pg_catalog.text FROM pg_catalog.pg_database WHERE datname OPERATOR(pg_catalog.=) pg_catalog.current_database()),"
                  "pg_catalog.pg_backend_pid()::pg_catalog.text,session_user::pg_catalog.text,current_user::pg_catalog.text,"
                  "(SELECT oid::pg_catalog.text FROM pg_catalog.pg_roles WHERE rolname OPERATOR(pg_catalog.=) current_user),"
                  "(SELECT oid::pg_catalog.text FROM pg_catalog.pg_roles WHERE rolname OPERATOR(pg_catalog.=) session_user)",prepare=False,binary=False)
        identity=c.fetchmany(2)
        if (c.description is None or len(c.description)!=7 or any(d.type_code!=25 for d in c.description)
                or len(identity)!=1 or len(identity[0])!=7 or any(type(v) is not str for v in identity[0])):
            raise ValueError('Exact original native graph context required')
        expected=dict(zip(('xid','databaseOid','backendPid','sessionUser','actingUser','actorRoleOid','sessionRoleOid'),identity[0]))
        def unique(pairs):
            result={}
            for k,v in pairs:
                if k in result:raise ValueError('Duplicate native context field')
                result[k]=v
            return result
        def read_scope():
            c.execute("SELECT rel_type_id::pg_catalog.text,pg_catalog.encode(original_context_bytes,'hex'),pg_catalog.encode(original_evidence_bytes,'hex') "
                      "FROM truss.authorization_graph_fact_scope WHERE original_writer_xid OPERATOR(pg_catalog.=) pg_catalog.pg_current_xact_id() ORDER BY rel_type_id",prepare=False,binary=False)
            rows=c.fetchmany(33)
            if (c.description is None or len(c.description)!=3 or any(d.type_code!=25 for d in c.description) or len(rows)>32):
                raise ValueError('Bounded original graph scope rows required')
            found=[];contexts=set()
            for row in rows:
                if len(row)!=3 or any(type(v) is not str for v in row):raise ValueError('Exact native scope text required')
                number,context_hex,evidence_hex=row
                if not number.isascii() or not number.isdecimal() or not 1<=len(number)<=10 or str(int(number))!=number or not 1<=int(number)<=2147483647:
                    raise ValueError('Exact native association identity required')
                if len(context_hex)>8192 or len(evidence_hex)>131072 or evidence_hex!=evidence.hex():raise ValueError('Original scope evidence required')
                context=json.loads(bytes.fromhex(context_hex),object_pairs_hook=unique)
                if type(context) is not dict or context!=expected or any(type(v) is not str for v in context.values()):raise ValueError('Original native scope context required')
                found.append(int(number));contexts.add(context_hex)
            if found!=sorted(set(found)) or len(contexts)>1:raise ValueError('Unique original native scope required')
            return tuple(found)
        before=read_scope();required=tuple(sorted(set(before)|set(ids)))
        if len(required)>32:raise ValueError('Graph scope capacity reached')
        c.execute('SELECT truss.runtime_register_graph_fact_scope(%s,%s)::pg_catalog.text AS registered_types',(list(ids),evidence),prepare=False,binary=False)
        response=c.fetchmany(2)
        if (c.description is None or len(c.description)!=1 or c.description[0].name!='registered_types'
                or c.description[0].type_code!=25 or response!=[(str(len(required)),)]):
            raise ValueError('Exact original registration result required')
        if read_scope()!=required:raise ValueError('Complete original registered scope required')
        return callback(c)
    return _run_fenced_epoch_operation(host,transaction,epoch,acquire)
