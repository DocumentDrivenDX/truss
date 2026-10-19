"""Native ordinary caller -> original computations -> guarded public result."""
import subprocess
from .execution import Ok, Error, ExecutionFailure
from .query import QueryRefused
from .psycopg_host import _HostPairReservation
from ._current_query_sources import capture_current_query_sources_with_cursor, _QUERY_PROFILE, _DISCLOSURE_PROFILE
from ._current_disclosure_originals import CurrentDisclosureOriginals,is_graph_disclosure_originals
from ._current_query_originals import CurrentQueryOriginals
from ._current_query_facts import capture_current_query_facts_with_cursor
from ._current_query_subjects import observe_current_query_subject_in_transaction, _verify_helper
from ._current_query_evaluation import evaluate_current_query, CurrentQueryLimit
from ._current_query_stage import stage_and_execute
from ._current_query_protection import verify_current_query_protection,GraphAuthorityProfileRequired
from ._current_query_pipe import CurrentQueryPipeError
from ._owner_evidence_json import decode_owner_evidence_json
from ._security_catalog_subject_installation import _text_rows
from ._security_catalog_assessment import SOURCE_TABLES
from ._installation_privileges import installation_administrator_with_cursor
from .catalog_runtime import _pin_cursor, _release


class _InnerFailure(Exception):
    def __init__(self,outcome):self.outcome=outcome


class _QueryRefusal(ValueError):
    pass


_GRAPH_CONSUMER_MODULES = frozenset((
    '2d64636f1e4929c1cd1529ec9cefff5ab47499fe31f65590af7d0063554f6dac',
    '1a7f9c3e43aa41419725d43c3f54a34499bc28b97f175a6eccbcf1d8b5b3b437',
))


def _verify_graph_caller_cut(cursor,identity):
    """Observe cuts on this original caller transaction; acquire none, issue no permit."""
    actual=_text_rows(cursor,"SELECT pg_catalog.pg_backend_pid()::text,l.virtualtransaction::text FROM pg_catalog.pg_locks l WHERE l.pid=pg_catalog.pg_backend_pid() AND l.locktype='virtualxid' AND l.mode='ExclusiveLock' AND l.granted",limit=1)
    if actual!=[identity]:
        raise ValueError('Original same-backend caller transaction cut required')
    homes=tuple((*SOURCE_TABLES,'source_epoch_current','source_epoch_registry',
        'installation_marker','installation_archive','catalog_subject_map','module_access',
        'object','object_key_bucket','edge'))
    rows=_text_rows(cursor,"""SELECT c.relname::text,c.relkind::text,c.relpersistence::text,
      c.relrowsecurity::text,c.relforcerowsecurity::text,
      EXISTS(SELECT 1 FROM pg_catalog.pg_inherits i WHERE i.inhrelid=c.oid OR i.inhparent=c.oid)::text,
      EXISTS(SELECT 1 FROM pg_catalog.pg_locks l WHERE l.pid=pg_catalog.pg_backend_pid()
        AND l.virtualtransaction=%s AND l.locktype='relation' AND l.granted
        AND l.database=(SELECT oid FROM pg_catalog.pg_database WHERE datname=pg_catalog.current_database())
        AND l.relation=c.oid AND l.mode='ShareLock')::text
      FROM pg_catalog.pg_class c JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace
      WHERE n.nspname='truss' AND c.relname=ANY(%s::text[]) ORDER BY c.relname""",
      (identity[1],list(homes)),limit=len(homes))
    if rows!=[(name,'r','p','false','false','false','true') for name in sorted(homes)]:
        raise ValueError('Original complete ordinary caller Graph source/data cut required')


def _run_guarded_current_query(host,transaction,executor,*,sql,document_ids,parameters,maximum_rows,maximum_scan_rows,maximum_bytes,disclosure):
    try:
        valid=(type(sql) is str and 1<=len(sql.encode())<=1048576 and '\0' not in sql
            and type(document_ids) is tuple and 1<=len(document_ids)<=32
            and all(type(d) is str and 1<=len(d.encode())<=4096 and '\0' not in d for d in document_ids) and len(set(document_ids))==len(document_ids)
            and type(parameters) is dict and len(parameters)<=1024)
    except (TypeError,ValueError,UnicodeError):
        valid=False
    if not valid:
        return Ok(QueryRefused('invalid_query'))
    if (any(type(n) is not int for n in (maximum_rows,maximum_scan_rows,maximum_bytes))
            or not 1<=maximum_rows<=10000 or not 1<=maximum_scan_rows<=10000 or not 1<=maximum_bytes<=16777216):
        return Ok(QueryRefused('limits'))
    inner_failure=[]
    final_caller=[]
    def require(outcome):
        if isinstance(outcome,Error):
            inner_failure.append(outcome)
            raise _InnerFailure(outcome)
        return outcome.value
    try:
        with _HostPairReservation(executor.host,host) as pair:
            def execute(cursor,observed):
                pair.deadline=cursor._deadline
                _pin_cursor(cursor)
                prior=_text_rows(cursor,"SELECT pg_catalog.current_setting('search_path')::pg_catalog.text",limit=1)
                if len(prior)!=1:raise ValueError('Original private executor search path required')
                cursor.execute("SELECT pg_catalog.set_config('search_path','pg_catalog, pg_temp',true)",prepare=False)
                if _text_rows(cursor,"SELECT pg_catalog.current_setting('server_encoding'),pg_catalog.current_setting('client_encoding')",limit=1)!=[('UTF8','UTF8')]:
                    raise ValueError('Exact UTF8 native query profile required')
                if cursor.execute('SELECT pg_catalog.pg_current_xact_id_if_assigned() IS NULL',prepare=False).fetchone()!=(True,):
                    raise ValueError('Dedicated fresh private executor transaction required')
                installation_administrator_with_cursor(cursor)
                sources=capture_current_query_sources_with_cursor(cursor)
                expected_profile,expected_originals=(_DISCLOSURE_PROFILE,CurrentDisclosureOriginals) if disclosure else (_QUERY_PROFILE,CurrentQueryOriginals)
                if sources.source_profile!=expected_profile or type(sources.query_originals) is not expected_originals:raise ValueError('Exact registered current query source profile required')
                graph_candidate=disclosure and is_graph_disclosure_originals(sources.query_originals)
                cursor.execute('LOCK TABLE ONLY truss.module_access IN SHARE MODE NOWAIT',prepare=False)
                cursor.execute('LOCK TABLE pg_catalog.pg_authid,pg_catalog.pg_auth_members IN SHARE MODE NOWAIT',prepare=False)
                cursor.execute('LOCK TABLE ONLY truss.catalog_subject_map,truss.object,truss.object_key_bucket IN SHARE MODE NOWAIT',prepare=False)
                verify_current_query_protection(cursor,sources,executor.subject_registration)
                request=decode_owner_evidence_json(sources.accepted_request_bytes)
                expected_modules={}
                for module in request['modules']:
                    document=decode_owner_evidence_json(module['documentJson'].encode())
                    for item in document['modules']:
                        expected_modules[(document['id'],item['id'])]=(module['pin']['revision'],module['pin']['sha256'])
                manifest,digest,_=_release()
                def caller_check(caller_cursor,caller_observed):
                    _pin_cursor(caller_cursor)
                    caller_prior=_text_rows(caller_cursor,"SELECT pg_catalog.current_setting('search_path')::pg_catalog.text",limit=1)
                    if len(caller_prior)!=1:raise ValueError('Original caller search path required')
                    caller_cursor.execute("SELECT pg_catalog.set_config('search_path','pg_catalog, pg_temp',true)",prepare=False)
                    if _text_rows(caller_cursor,"SELECT pg_catalog.current_setting('server_encoding'),pg_catalog.current_setting('client_encoding')",limit=1)!=[('UTF8','UTF8')]:
                        raise ValueError('Exact UTF8 ordinary query profile required')
                    _verify_helper(caller_cursor,executor.subject_registration)
                    subject_rows=_text_rows(caller_cursor,'SELECT * FROM truss.current_query_subject_current()',limit=1)
                    if len(subject_rows)!=1:raise ValueError('Current ordinary Subject required')
                    if graph_candidate:_verify_graph_caller_cut(caller_cursor,caller_observed[0][:2])
                    raw=caller_cursor.execute('SELECT truss.reader_catalog(%s,%s,%s,%s)',(65536,16777216,manifest['releaseId'],digest),prepare=False).fetchone()
                    if raw is None or type(raw[0]) is not bytes:raise ValueError('Original caller-readable catalog required')
                    view=decode_owner_evidence_json(raw[0])
                    actual={(m['documentId'],m['moduleId']):(m['documentRevision'],m['documentSha256']) for m in view['modules']}
                    if (any(actual.get(k)!=v for k,v in expected_modules.items()) or str(view['catalogRevision'])!=sources.accepted_revision):
                        raise ValueError('Complete interpreted source/prerequisite module access required')
                    caller_cursor.execute("SELECT pg_catalog.set_config('search_path',%s,true)",(caller_prior[0][0],),prepare=False)
                    if caller_cursor.fetchmany(2)!=caller_prior:raise ValueError('Original caller search path restoration required')
                    return subject_rows[0],caller_observed[0][:2]
                cursor._deadline.check()
                before=require(host._run_operation(transaction,caller_check))
                final_caller.append((caller_check,before))
                subject=require(observe_current_query_subject_in_transaction(host,transaction,executor.subject_registration,bun_executable=executor.bun_executable))
                cursor._deadline.check()
                if (subject.source_receipt,subject.installation_id)!=(sources.source_receipt,sources.installation_id):
                    raise ValueError('Same installed original caller/Subject sources required')
                # Compare the actual caller backend/virtual transaction from the
                # reserved ordinary host against this private connection's native
                # activity and lock inventories; no request supplies an actor.
                def peer():
                    cursor.execute('SELECT pg_catalog.pg_stat_clear_snapshot()',prepare=False)
                    return _text_rows(cursor,"SELECT a.datid::text,a.usesysid::text,l.virtualtransaction::text FROM pg_catalog.pg_stat_activity a JOIN pg_catalog.pg_locks l ON l.pid=a.pid AND l.locktype='virtualxid' AND l.mode='ExclusiveLock' AND l.granted WHERE a.pid=%s::int AND a.datid=(SELECT oid FROM pg_catalog.pg_database WHERE datname=pg_catalog.current_database()) AND a.xact_start IS NOT NULL AND a.state IN ('active','idle in transaction')",(before[1][0],),1)
                expected_peer=[(subject.database_oid,subject.role_oid,before[1][1])]
                if peer()!=expected_peer:raise ValueError('Actual same-database ordinary caller transaction required')
                if graph_candidate:
                    from ._current_disclosure_context_capture import capture_context_disclosure_with_cursor
                    captured=capture_context_disclosure_with_cursor(cursor,sql=sql,parameters=parameters,
                        document_ids=document_ids,bun_executable=executor.bun_executable)
                else:
                    captured=capture_current_query_facts_with_cursor(cursor,bun_executable=executor.bun_executable)
                if captured.sources!=sources:raise ValueError('Original held source inventory changed')
                facts=decode_owner_evidence_json(captured.facts_bytes)
                initial=decode_owner_evidence_json(sources.initialize_bytes)['sources']
                subject_facts=[f for f in facts if f['type']==initial['ontology']['subject'] and f['key']==[{'string':subject.key}]]
                if len(subject_facts)!=1:raise ValueError('Actual observed Subject must occur in complete native facts')
                captured_rows=captured.facts.rows if graph_candidate else captured.rows
                matching=[r for r in captured_rows if r[:3]==(subject.object_id,subject.type_id,subject.object_version)]
                if (len(matching)!=1 or bytes.fromhex(decode_owner_evidence_json(matching[0][3])['bytesHex'])!=subject.tuple_bytes):
                    raise ValueError('Original Subject object/version/Key fact correspondence required')
                try:
                    if disclosure:
                        from ._current_disclosure_evaluation import evaluate_and_stage_current_disclosure
                        candidate=evaluate_and_stage_current_disclosure(cursor,captured,subject,sql=sql,parameters=parameters,
                            document_ids=document_ids,bun_executable=executor.bun_executable,
                            maximum_rows=maximum_rows,maximum_scan_rows=maximum_scan_rows,maximum_bytes=maximum_bytes)
                    else:
                        evaluated=evaluate_current_query(cursor,captured,subject,sql=sql,parameters=parameters,document_ids=document_ids,bun_executable=executor.bun_executable)
                        candidate=stage_and_execute(cursor,captured,evaluated,maximum_rows=maximum_rows,
                                                    maximum_scan_rows=maximum_scan_rows,maximum_bytes=maximum_bytes)
                except CurrentQueryLimit:
                    raise
                except (CurrentQueryPipeError,subprocess.TimeoutExpired) as error:
                    cursor._deadline.check()
                    raise RuntimeError('Original computation transport unavailable') from error
                except ValueError as error:
                    raise _QueryRefusal('Original query domain/route or supported profile refused') from error
                cursor._deadline.check()
                if require(host._run_operation(transaction,caller_check))!=before or peer()!=expected_peer:
                    raise ValueError('Original caller/Subject/access changed before release')
                if graph_candidate:
                    from ._current_disclosure_context_capture import verify_context_disclosure_with_cursor
                    verify_context_disclosure_with_cursor(cursor,captured,bun_executable=executor.bun_executable)
                if capture_current_query_sources_with_cursor(cursor)!=sources:
                    raise ValueError('Original query source changed before release')
                verify_current_query_protection(cursor,sources,executor.subject_registration)
                cursor.execute("SELECT pg_catalog.set_config('search_path',%s,true)",(prior[0][0],),prepare=False)
                if cursor.fetchmany(2)!=prior:raise ValueError('Original private executor search path restoration required')
                cursor._deadline.check()
                if disclosure:candidate.require_original_parent()
                return (candidate,sources.accepted_revision) if disclosure else candidate
            outcome=executor.host._run_operation(executor.transaction,execute)
            if isinstance(outcome,Error) and outcome.error.code=='transaction_unusable':return outcome
            if inner_failure:return inner_failure[0]
            if (isinstance(outcome,Error) and outcome.error.code=='invalid_transaction'
                    and isinstance(executor.host._custody.last_attempt.error,GraphAuthorityProfileRequired)):
                return Ok(QueryRefused('execution_obligation'))
            if (isinstance(outcome,Error) and outcome.error.code=='invalid_transaction'
                    and isinstance(executor.host._custody.last_attempt.error,CurrentQueryLimit)):
                return Ok(QueryRefused('limits'))
            if (isinstance(outcome,Error) and outcome.error.code=='invalid_transaction'
                    and isinstance(executor.host._custody.last_attempt.error,_QueryRefusal)):
                return Ok(QueryRefused('unsupported_query'))
            if isinstance(outcome,Ok):
                check,expected=final_caller[0]
                def finish(caller_cursor,caller_observed):
                    if check(caller_cursor,caller_observed)!=expected:
                        raise ValueError('Original ordinary caller changed after private completion')
                # Both actual host operations must finish successfully before
                # handing off data; the Python pair lease alone is not native
                # caller/current authority. Source/object cuts also belong to
                # the ordinary transaction's installed helper.
                completed=host._run_operation(transaction,finish)
                if isinstance(completed,Error):return completed
                if any(h._closed or h._custody.quarantined or h._custody.pending is not None
                       or h.connection.closed or h.connection.broken for h in pair.hosts):
                    return Error(ExecutionFailure('transaction_unusable','Original query host completion unavailable'))
            if disclosure and isinstance(outcome,Ok):
                held,revision=outcome.value
                held.require_original_parent()
                from .current_disclosure import CurrentDisclosureRows
                from ._current_query_evaluation import wire
                staged=held.staged
                metadata=wire({'columns':staged.names,'fieldIndexes':staged.field_indexes,'catalogRevision':int(revision),'outcome':'disclosure'})
                # Bound the whole public representation, including alias metadata.
                if len(metadata)+len(staged.reconstructed_batch)+len(b',"batch":')>maximum_bytes:
                    return Ok(QueryRefused('limits'))
                try:pair.deadline.check()
                except TimeoutError:
                    return Error(ExecutionFailure('transaction_unusable','Original disclosure deadline expired before handoff'))
                return Ok(CurrentDisclosureRows(staged.names,staged.field_indexes,staged.reconstructed_batch,int(revision)))
            return outcome
    except ValueError:
        return Ok(QueryRefused('stale_context'))


def run_current_query(host,transaction,executor,*,sql,document_ids,parameters,maximum_rows,maximum_scan_rows,maximum_bytes):
    return _run_guarded_current_query(host,transaction,executor,sql=sql,document_ids=document_ids,parameters=parameters,
        maximum_rows=maximum_rows,maximum_scan_rows=maximum_scan_rows,maximum_bytes=maximum_bytes,disclosure=False)


def run_current_disclosure(host,transaction,executor,*,sql,document_ids,parameters,maximum_rows,maximum_scan_rows,maximum_bytes):
    return _run_guarded_current_query(host,transaction,executor,sql=sql,document_ids=document_ids,parameters=parameters,
        maximum_rows=maximum_rows,maximum_scan_rows=maximum_scan_rows,maximum_bytes=maximum_bytes,disclosure=True)
