#!/usr/bin/env python3
"""Time real sample registration and public create/read/update/reopen workflows.

Uses the existing native test fixture only for isolated PostgreSQL/role setup.
Business operations use the public Truss API. No private table writes or mocks.
"""
import argparse
import gzip
import hashlib
import importlib.metadata
import importlib.resources
import json
import math
import os
from pathlib import Path
import platform
import statistics
import subprocess
import sys
import time
import unittest

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--truss-root',type=Path,required=True)
parser.add_argument('--installed-package',action='store_true',help='Exercise the installed wheel; refuse imports from the checkout source')
parser.add_argument('--examples-root',type=Path)
parser.add_argument('--matrix-case',nargs='+',help='Run selected workloads.json cases instead of real samples')
parser.add_argument('--samples',nargs='+',default=['pizza','northwind','catalog'])
parser.add_argument('--bulk-size',type=int,default=100)
parser.add_argument('--expected-group-limit',type=int,default=1024,help='Expected engine atomic capacity; actual calls must still succeed')
parser.add_argument('--read-samples',type=int,default=1000)
parser.add_argument('--write-samples',type=int,default=200)
parser.add_argument('--profile-native-functions',action='store_true',help='Diagnostic run: enable PostgreSQL PL function timing for benchmark consumer')
parser.add_argument('--load-only',action='store_true',help='Measure and verify object/edge loading, omitting the later read/update matrix')
parser.add_argument('--forbid-external-javascript',action='store_true',help='Fail if any code attempts to launch Bun, Node, or NodeJS')
parser.add_argument('--profile-read',type=Path,help='Optional separate cProfile of one warm public ID read, outside timed samples')
parser.add_argument('--output',type=Path,default=Path('truss-public-performance.json'))
args=parser.parse_args()
external_processes=[]
if args.forbid_external_javascript:
    def process_audit(event,values):
        if event!='subprocess.Popen':return
        executable,arguments=values[:2]
        name=Path(os.fsdecode(executable)).name.lower()
        if name in ('bun','node','nodejs'):
            raise AssertionError('External JavaScript process attempted: '+str(arguments))
        external_processes.append(name)
    sys.addaudithook(process_audit)
if min(args.bulk_size,args.read_samples,args.write_samples)<1:parser.error('sample sizes must be positive')
if args.expected_group_limit<1:parser.error('--expected-group-limit must be positive')
if args.bulk_size>args.expected_group_limit:parser.error('--bulk-size exceeds the configured expected group limit')

from performance_workloads import workloads, schema as workload_schema, values as workload_values, edges as workload_edges
selected_workloads=workloads()
matrix_settings=json.loads((Path(__file__).resolve().parents[1]/'docs/helix/03-test/performance/workloads.json').read_text())
selected_cases=args.matrix_case or args.samples
root=args.truss_root.resolve()
sys.path[:0]=([str(root/'packages/python/src')] if not args.installed_package else [])+[str(root/'packages/python/tests')]
import truss
package_path=Path(truss.__file__).resolve()
if args.installed_package and package_path.is_relative_to(root/'packages/python/src'):
    parser.error('--installed-package resolved Truss from the checkout source')
runtime_resource=importlib.resources.files('truss').joinpath('_catalog_runtime/manifest.json')
runtime_manifest=runtime_resource.read_bytes()
runtime_package={'mode':'installed' if args.installed_package else 'checkout','path':str(package_path),
    'version':importlib.metadata.version('truss-toolkit') if args.installed_package else None,
    'manifestPath':str(runtime_resource)}
from truss import (Ok,ModuleAccessGrant,CatalogDocument,CatalogRuntimeConfiguration,
                   adopt_psycopg_host,create_reference_assembly,ObjectFound,EdgeFound)
from truss.catalog_results import CatalogRegistration,CatalogUnchanged
from truss.contracts import MapValue,TextValue
from truss.groups import (CreateObject,RootlessOwnership,AuthoredValue,RequestNone,
                          GroupSuccess,UpdateObject,StoredObjectReference,CreateEdge,NullOrderKey)
import psycopg
from test_catalog_runtime_native import PublicCatalogRuntimeTests

measurements=[]
results=[]
args.output.parent.mkdir(parents=True,exist_ok=True)
progress_path=args.output.with_suffix('.jsonl')
progress_path.write_text('')
def record_measurement(measurement):
    measurements.append(measurement)
    with progress_path.open('a') as stream:
        stream.write(json.dumps(measurement,separators=(',',':'))+'\n')


def timed(case,operation,call,rows=1):
    start=time.perf_counter_ns()
    try:
        result=call()
    except BaseException as error:
        failure=dict(case=case,operation=operation,rows=rows,ms=(time.perf_counter_ns()-start)/1e6,status='failed',error=str(error))
        diagnostics=getattr(error,'diagnostics',())
        if diagnostics:failure['diagnostics']=[d.decode('utf-8',errors='replace')[:4096] if isinstance(d,bytes) else str(d)[:4096] for d in diagnostics[:4]]
        record_measurement(failure)
        raise
    record_measurement(dict(case=case,operation=operation,rows=rows,ms=(time.perf_counter_ns()-start)/1e6,status='ok'))
    if operation in ('install','prepare','register','registrar_catalog_view','bulk_create','bulk_edges'):
        print(f'{case}: {operation} {measurements[-1]["ms"]:.2f} ms ({rows} rows)',file=sys.stderr,flush=True)
    return result

def ok(value):
    if not isinstance(value,Ok):raise AssertionError(repr(value))
    return value.value

class RealWorkflows(PublicCatalogRuntimeTests):
    for _name in tuple(n for n in dir(PublicCatalogRuntimeTests) if n.startswith('test_')):
        locals()[_name]=None

    @classmethod
    def setUpClass(cls):
        timed('runtime','cold_server_start',lambda:super(RealWorkflows,cls).setUpClass())

    @classmethod
    def cleanup(cls):
        timed('runtime','server_cleanup',lambda:super(RealWorkflows,cls).cleanup())

    def workflow(self,sample):
        case={'sample':sample,'status':'running'};results.append(case)
        workload=selected_workloads[sample] if args.matrix_case else None
        record='R0' if workload else {'pizza':'Country','northwind':'Category','catalog':'UseCase'}[sample]
        if workload:raw=json.dumps(workload_schema(workload),separators=(',',':')).encode()
        elif args.examples_root:raw=(args.examples_root/sample/(sample+'.umf.json')).read_bytes()
        else:
            corpus=json.loads(gzip.decompress((root/'packages/python/tests/fixtures/hohfeld/originals.json.gz').read_bytes()))
            fixture=next(d for d in corpus['documents'] if d['sample']==sample)
            raw=fixture['sourceText'].encode()
            if hashlib.sha256(raw).hexdigest()!=fixture['sha256']:raise AssertionError('Original real-schema fixture hash mismatch')
            case['sourceCommit']=corpus['sourceCommit'] if 'sourceCommit' in corpus else fixture.get('sourceCommit')
        source=json.loads(raw);module=source['modules'][0];document_id=source['id'];module_id=module['id']
        if workload:case['workload']=workload
        count=workload['nodes'] if workload else args.bulk_size
        case.update(schemaBytes=len(raw),records=sum(e['kind']=='record' for e in module['elements']),elements=len(module['elements']),actions=len(module.get('actions',[])))
        documents=(CatalogDocument(document_id,'performance-v1',raw),)
        timed(sample,'install',self.install)
        case['databaseSettings']=dict(self.admin.execute("SELECT name,setting FROM pg_catalog.pg_settings WHERE name IN ('server_version','fsync','synchronous_commit','full_page_writes','shared_buffers')").fetchall())
        if args.profile_native_functions:self.admin.execute("ALTER ROLE consumer SET track_functions='pl'")
        connection,host,assembly,tx=self.consumer()
        prepared=timed(sample,'prepare',lambda:assembly.prepare_catalog(documents,source_version=source['umf'],bun_executable=os.environ.get('TRUSS_BUN_EXECUTABLE','bun')))
        def register():
            result=assembly.accept_in_transaction(tx,prepared,request_key=sample+'-register')
            if not isinstance(result,Ok):
                raise AssertionError(repr(result)+'; native-test diagnostic: '+str(host._custody.last_attempt.error))
            if not isinstance(result.value,(CatalogRegistration,CatalogUnchanged)):raise AssertionError('Registration refused: '+repr(result.value))
            return result.value
        registration=timed(sample,'register',register)
        view=timed(sample,'registrar_catalog_view',lambda:ok(assembly.catalog_view_in_transaction(tx,assembly.catalog_view_request())).view)
        timed(sample,'registration_commit',lambda:(host.detach(),connection.commit()))
        case['schemaStorage']=dict(zip(('sourceBytes','compiledTypeBytes','compiledDocumentBytes'),
            self.admin.execute('''SELECT
                (SELECT coalesce(sum(octet_length(document)),0) FROM truss.schema_doc),
                (SELECT coalesce(sum(pg_column_size(metadata)+pg_column_size(value_readers)),0) FROM truss.runtime_type_schema),
                (SELECT coalesce(sum(pg_column_size(metadata)),0) FROM truss.runtime_document_schema)''').fetchone()))
        # Configure ordinary public access. The consumer is never the private owner.
        for role in ('perf_reader','perf_writer'):
            self.admin.execute(psycopg.sql.SQL('CREATE ROLE {} NOLOGIN').format(psycopg.sql.Identifier(role)))
            self.addCleanup(self.admin.execute,psycopg.sql.SQL('DROP ROLE {}').format(psycopg.sql.Identifier(role)))
        self.admin.execute('BEGIN')
        self.host=adopt_psycopg_host(self.admin,statement_timeout_ms=10000,operation_timeout_ms=30000);self.tx=ok(self.host.adopt_transaction())
        self.assembly=ok(create_reference_assembly(CatalogRuntimeConfiguration(),self.host))
        ok(self.assembly.configure_module_access_in_transaction(self.tx,(ModuleAccessGrant(document_id,module_id,'perf_reader','perf_writer'),)))
        self.host.detach();self.admin.commit()
        self.admin.execute('GRANT perf_writer TO consumer WITH SET FALSE')
        self.admin.execute(psycopg.sql.SQL('REVOKE {} FROM consumer').format(psycopg.sql.Identifier(self.installation.registrar_role)))
        connection,host,assembly,tx=self.consumer()
        type_refs={d.reference.authored_identity:d.reference for d in view.definitions if d.reference.kind=='type' and d.reference.owner.document_id==document_id}
        type_to_record={ref.type_id:identity for identity,ref in type_refs.items()}
        type_ref=type_refs[record]
        fields={e['id']:e for e in module['elements'] if e['kind']=='field'}
        # Binding fallback uses ID, never modifies or fills in the original schema.
        code='p0' if workload else fields[record+'.code'].get('name',record+'.code')
        name='p1' if workload else fields[record+'.name'].get('name',record+'.name')
        def apply(operations):
            context=ok(assembly.group_context_in_transaction(tx))
            outcome=assembly.apply_in_transaction(tx,context.input(operations,MapValue(entries=())),RequestNone(),documents=documents,bun_executable=os.environ.get('TRUSS_BUN_EXECUTABLE','bun'))
            if not isinstance(outcome,Ok):raise AssertionError(repr(outcome)+'; native-test diagnostic: '+str(host._custody.last_attempt.error))
            result=outcome.value
            if not isinstance(result,GroupSuccess):raise AssertionError(repr(result)+'; native-test diagnostic: '+str(host._custody.last_attempt.error))
            return result
        def rebind():
            nonlocal host,assembly,tx
            connection.execute('BEGIN')
            host=adopt_psycopg_host(connection,statement_timeout_ms=10000,operation_timeout_ms=30000);self.addCleanup(host.detach)
            tx=ok(host.adopt_transaction())
            assembly=ok(create_reference_assembly(CatalogRuntimeConfiguration(),host))
        def creations(first,last):
            return tuple(CreateObject(type_definition_pin=type_refs['R'+str(i%workload['types'])].definition_pin if workload else type_ref.definition_pin,
                values=workload_values(workload,i) if workload else (AuthoredValue(name=code,value=TextValue(kind='string',text='perf-'+str(i))),AuthoredValue(name=name,value=TextValue(kind='string',text='Record '+str(i)))),
                ownership=RootlessOwnership(),alias='row'+str(i)) for i in range(first,last))
        identities=[];start=time.perf_counter_ns()
        for first in range(0,count,args.bulk_size):
            last=min(count,first+args.bulk_size)
            created=timed(sample,'bulk_create',lambda:apply(creations(first,last)),last-first)
            identities.extend(item.identity for item in created.response.semantic.results)
            timed(sample,'bulk_create_commit',lambda:(host.detach(),connection.commit()),last-first)
            if last<count:rebind()
        case['bulkCreateIncludingCommitMs']=(time.perf_counter_ns()-start)/1e6
        case['bulkCreateRowsPerSecondIncludingCommit']=count/(case['bulkCreateIncludingCommitMs']/1000)
        if args.profile_native_functions:
            retained=self.admin.execute('''SELECT count(*),coalesce(sum(pg_column_size(plan)),0),
                coalesce(sum(octet_length(plan::text)),0),coalesce(max(octet_length(plan::text)),0),
                coalesce(sum((SELECT count(*) FROM jsonb_object_keys(plan->'beforeNodes'))),0),
                coalesce(sum((SELECT count(*) FROM jsonb_object_keys(plan->'afterNodes'))),0)
                FROM truss.runtime_owned_operation''').fetchone()
            case['retainedPlanningAfterLoad']=dict(zip(('plans','storedDatumBytes','logicalJsonBytes','maximumLogicalPlanBytes','beforeNodeReferences','afterNodeReferences'),map(int,retained)))
        if len(identities)!=count:raise AssertionError('Wrong created count')
        # SQL is used only for independent verification, never to seed data.
        if self.admin.execute('SELECT count(*) FROM truss.object').fetchone()[0]!=count:raise AssertionError('Wrong persisted object count')
        rebind()
        if workload and workload['edges']:
            edge_start=time.perf_counter_ns()
            relation_refs={d.reference.authored_identity:d.reference for d in view.definitions if d.reference.kind=='relationship'}
            batch=[];created_edges=0;edge_samples=[];batch_expected=[]
            for t,source_index,target_index in workload_edges(workload):
                batch.append(CreateEdge(relationship_definition_pin=relation_refs['R'+str(t)+'.link'].definition_pin,
                    source=StoredObjectReference(identity=identities[source_index]),target=StoredObjectReference(identity=identities[target_index]),values=(),order_key=NullOrderKey()))
                batch_expected.append((t,source_index,target_index))
                if len(batch)==args.bulk_size:
                    size=len(batch);edge_result=timed(sample,'bulk_edges',lambda:apply(tuple(batch)),size)
                    if len(edge_samples)<5:edge_samples.extend(zip(batch_expected[:5-len(edge_samples)],[item.identity for item in edge_result.response.semantic.results][:5-len(edge_samples)]))
                    timed(sample,'bulk_edges_commit',lambda:(host.detach(),connection.commit()),size)
                    created_edges+=size;batch=[];batch_expected=[];rebind()
            if batch:
                size=len(batch);edge_result=timed(sample,'bulk_edges',lambda:apply(tuple(batch)),size)
                if len(edge_samples)<5:edge_samples.extend(zip(batch_expected[:5-len(edge_samples)],[item.identity for item in edge_result.response.semantic.results][:5-len(edge_samples)]))
                timed(sample,'bulk_edges_commit',lambda:(host.detach(),connection.commit()),size)
                created_edges+=size;rebind()
            if created_edges!=workload['edges'] or self.admin.execute('SELECT count(*) FROM truss.edge').fetchone()[0]!=created_edges:raise AssertionError('Wrong persisted edge count')
            for (t,source_index,target_index),edge_identity in edge_samples:
                found=ok(assembly.get_edge_in_transaction(tx,document_id=document_id,module_id=module_id,relationship_id='R'+str(t)+'.link',edge_id=int(edge_identity.id)))
                if not isinstance(found,EdgeFound) or found.edge.source!=identities[source_index] or found.edge.target!=identities[target_index]:raise AssertionError('Wrong persisted edge endpoints')
            case['createdEdges']=created_edges
            case['edgeLoadIncludingCommitMs']=(time.perf_counter_ns()-edge_start)/1e6
            case['edgeRowsPerSecondIncludingCommit']=created_edges/(case['edgeLoadIncludingCommitMs']/1000)
        if args.load_only:
            if args.profile_native_functions:
                connection.execute('SELECT pg_stat_force_next_flush()')
                self.admin.execute('SELECT pg_stat_clear_snapshot()')
                columns=('function','calls','totalMs','selfMs')
                case['nativeFunctionProfile']=[dict(zip(columns,row)) for row in self.admin.execute("SELECT funcid::regprocedure::text,calls,total_time,self_time FROM pg_stat_user_functions WHERE schemaname='truss' ORDER BY self_time DESC").fetchall()]
            host.detach();connection.rollback()
            case.update(status='passed',loaded=count,scope='Committed object/edge load and persisted row/endpoint verification')
            return
        def read(identity):
            result=ok(assembly.get_object_in_transaction(tx,document_id=document_id,module_id=module_id,record_id=type_to_record[identity.type_id] if workload else record,object_id=int(identity.id)))
            if not isinstance(result,ObjectFound):raise AssertionError('Committed object not found: '+repr(result)+'; native: '+str(host._custody.last_attempt.error))
            return result.object
        positions=sorted(set(range(min(workload['types'],count)))|{i*count//100 for i in range(100)}|{count-1}) if workload else range(count)
        for i in positions:
            actual=dict(read(identities[i]).values)
            if actual[name]!='Record '+str(i):raise AssertionError('Wrong committed value')
            if workload:
                expected={value.name:(value.value.text if isinstance(value.value,TextValue) and value.value.kind=='string' else value.value.value if hasattr(value.value,'kind') and value.value.kind=='boolean' else value.value) for value in workload_values(workload,i)}
                if actual!=expected:raise AssertionError('Stress workload values changed or disappeared')
        # Exercise the list route the embedding application actually uses, including
        # relationship columns supplied by complete-entity itself.
        from truss.query import QueryRows
        quote=lambda value:'"'+value.replace('"','""')+'"'
        selected_record=next(e for e in module['elements'] if e['id']==record and e['kind']=='record')
        list_sql='SELECT x.* FROM '+quote(module.get('namespace',module_id))+'.'+quote(selected_record.get('name',record))+' x LIMIT 51'
        def list_entities():
            listed=ok(assembly.query_in_transaction(tx,sql=list_sql,document_ids=(document_id,),
                parameters=None,maximum_rows=100,read_profile='complete-entity'))
            if not isinstance(listed,QueryRows):raise AssertionError('Complete entity list refused: '+repr(listed))
            expected_rows=min(51,sum(1 for identity in identities if identity.type_id==identities[0].type_id))
            if len(listed.rows)!=expected_rows:raise AssertionError('Complete entity list returned the wrong row count')
            return listed
        # Whole-entity list qualification is additional to the declared ID/key
        # stress workload. The released query profile admits 10,000 source rows;
        # the million-node case has 100,000 per type and remains outside it.
        list_supported=not workload or math.ceil(count/workload['types'])<=10000
        if list_supported:
            listing=timed(sample,'list_complete_entities',list_entities)
            case['listRead']={'status':'passed','sql':list_sql,'rows':len(listing.rows),'columns':list(listing.columns)}
        else:
            case['listRead']={'status':'outside_published_query_scan_bound','sql':list_sql,
                'sourceRowsPerType':math.ceil(count/workload['types']),'maximumScanRows':10000,
                'scope':'Declared million-node ID/key read and write stress workload still runs in full'}
        for i in range(matrix_settings['warmupOperations']):read(identities[i%len(identities)])
        if args.profile_read:
            import cProfile
            profiler=cProfile.Profile()
            profiler.runcall(read,identities[0])
            profiler.dump_stats(str(args.profile_read))
        for i in range(args.read_samples):timed(sample,'read_by_id',lambda:read(identities[i%len(identities)]))
        for i in range(min(100,args.read_samples)):
            position=i%count;selected_identity=identities[position]
            def key_read():
                result=ok(assembly.lookup_key_in_transaction(tx,document_id=document_id,module_id=module_id,
                    record_id=type_to_record[selected_identity.type_id] if workload else record,
                    key_id='key0' if workload else 'identity',values=(('p0-' if workload else 'perf-')+str(position),),
                    bun_executable=os.environ.get('TRUSS_BUN_EXECUTABLE','bun')))
                if not isinstance(result,ObjectFound) or str(result.object.identity.id)!=str(selected_identity.id):raise AssertionError('Key lookup returned wrong record')
                return result
            timed(sample,'read_by_key',key_read)
        identity=identities[0]
        version=read(identity).version
        host.detach();connection.commit()
        # Reuse the connection, but include BEGIN, adoption, public update and COMMIT.
        for i in range(args.write_samples):
            def committed_update():
                nonlocal host,assembly,tx,version
                connection.execute('BEGIN')
                host=adopt_psycopg_host(connection,statement_timeout_ms=10000,operation_timeout_ms=30000)
                tx=ok(host.adopt_transaction())
                assembly=ok(create_reference_assembly(CatalogRuntimeConfiguration(),host))
                update=UpdateObject(target=StoredObjectReference(identity=identity),
                    set=(AuthoredValue(name=name,value=TextValue(kind='string',text='Updated '+str(i))),),
                    unset=(),expected_version=str(version))
                result=apply((update,))
                item=result.response.semantic.results[0]
                if item.outcome!='changed':raise AssertionError('Single update became a no-op')
                version=item.version
                host.detach();connection.commit()
                return result
            # Snapshot one actual update separately from setup/read statistics.
            # Force this backend's counters outside the timed operation.
            if args.profile_native_functions and i==args.write_samples-1:
                connection.execute('SELECT pg_stat_force_next_flush()')
                self.admin.execute('SELECT pg_stat_clear_snapshot()')
                before_functions={row[0]:row[1:] for row in self.admin.execute("SELECT funcid::regprocedure::text,calls,total_time,self_time FROM pg_stat_user_functions WHERE schemaname='truss'").fetchall()}
            timed(sample,'single_update_including_commit',committed_update)
            if args.profile_native_functions and i==args.write_samples-1:
                connection.execute('SELECT pg_stat_force_next_flush()')
                self.admin.execute('SELECT pg_stat_clear_snapshot()')
                delta=[]
                for function,calls,total_ms,self_ms in self.admin.execute("SELECT funcid::regprocedure::text,calls,total_time,self_time FROM pg_stat_user_functions WHERE schemaname='truss'").fetchall():
                    old=before_functions.get(function,(0,0,0))
                    if calls>old[0]:delta.append(dict(function=function,calls=calls-old[0],totalMs=total_ms-old[1],selfMs=self_ms-old[2]))
                case['lastCommittedUpdateNativeFunctions']=sorted(delta,key=lambda row:row['selfMs'],reverse=True)
        connection,host,assembly,tx=self.consumer()
        after=read(identity)
        if dict(after.values)[name]!='Updated '+str(args.write_samples-1):raise AssertionError('Update not durable after reopen')
        if len(identities)>1 and dict(read(identities[1]).values)[name]!='Record 1':raise AssertionError('Unselected record changed')
        host.detach();connection.rollback()
        if workload:
            for batch_size in matrix_settings['batchSizes']:
                if batch_size>count:continue
                if batch_size>args.expected_group_limit:
                    measurements.append(dict(case=sample,operation='atomic_bulk_update_'+str(batch_size),rows=batch_size,status='unsupported',ms=0,reason='Above configured expected group capacity: '+str(args.expected_group_limit)))
                    continue
                for repeat in range(matrix_settings['bulkRepeats']):
                    rebind()
                    unselected=read(identities[batch_size]) if batch_size<count else None
                    unselected_before=(dict(unselected.values),unselected.version) if unselected else None
                    host.detach();connection.rollback()
                    def update_batch():
                        operations=tuple(UpdateObject(target=StoredObjectReference(identity=identities[i]),
                            set=(AuthoredValue(name=name,value=TextValue(kind='string',text=f'Bulk {batch_size}/{repeat}/{i}')),),unset=()) for i in range(batch_size))
                        result=apply(operations)
                        if len(result.response.semantic.results)!=batch_size or any(item.outcome!='changed' for item in result.response.semantic.results):raise AssertionError('Bulk update changed wrong count or became no-op')
                        return result
                    def committed_batch_update():
                        rebind()
                        timed(sample,'bulk_update_'+str(batch_size),update_batch,batch_size)
                        timed(sample,'bulk_update_commit_'+str(batch_size),lambda:(host.detach(),connection.commit()),batch_size)
                    timed(sample,'bulk_update_end_to_end_'+str(batch_size),committed_batch_update,batch_size)
                    rebind()
                    for position in range(batch_size):
                        if dict(read(identities[position]).values)[name]!=f'Bulk {batch_size}/{repeat}/{position}':raise AssertionError('Bulk update did not persist')
                    if unselected_before is not None:
                        unselected_after=read(identities[batch_size])
                        if (dict(unselected_after.values),unselected_after.version)!=unselected_before:raise AssertionError('Unselected bulk row changed')
                    host.detach();connection.rollback()
            case['installedPhysicalIndexes']=[row[0] for row in self.admin.execute("SELECT indexname FROM pg_catalog.pg_indexes WHERE schemaname='truss' ORDER BY indexname").fetchall()]
            case['indexWorkload']='Unique business-key properties; optional nonunique lookup indexes not represented'
            key_rows=self.admin.execute('''SELECT t.element,t.type_id,
                (SELECT count(*) FROM truss.key_def k WHERE k.type_id=t.type_id AND k.retired_rev IS NULL),
                (SELECT count(*) FROM truss.object o WHERE o.type_id=t.type_id),
                (SELECT count(*) FROM truss.object_key_bucket b WHERE b.type_id=t.type_id)
                FROM truss.type_def t WHERE t.document_id=%s AND t.kind='record' AND t.retired_rev IS NULL ORDER BY t.type_id''',(document_id,)).fetchall()
            case['maintainedBusinessKeys']=[dict(record=row[0],typeId=row[1],declaredKeys=row[2],objects=row[3],maintainedKeyRows=row[4]) for row in key_rows]
            if len(key_rows)!=workload['types'] or any(row[2]!=workload['indexedPropertiesPerType'] or row[4]!=row[3]*row[2] for row in key_rows):raise AssertionError('Declared business keys are not fully maintained')
        if args.profile_native_functions:
            self.admin.execute('SELECT pg_stat_clear_snapshot()')
            columns=('function','calls','totalMs','selfMs')
            case['nativeFunctionProfile']=[dict(zip(columns,row)) for row in self.admin.execute("SELECT funcid::regprocedure::text,calls,total_time,self_time FROM pg_stat_user_functions WHERE schemaname='truss' ORDER BY self_time DESC").fetchall()]
        case.update(status='passed',loaded=count,readSamples=args.read_samples,committedUpdates=args.write_samples,reopenedValuesVerified=True)

for sample in selected_cases:
    if sample not in (selected_workloads if args.matrix_case else ('pizza','northwind','catalog')):parser.error('unknown case '+sample)
    def test(self,sample=sample):self.workflow(sample)
    setattr(RealWorkflows,'test_'+sample,test)

start=time.perf_counter()
suite=unittest.TestSuite(RealWorkflows('test_'+sample) for sample in selected_cases)
class ImmediateFailures(unittest.TextTestResult):
    def addFailure(self,test,error):
        super().addFailure(test,error)
        self.stream.writeln(self.failures[-1][1])
    def addError(self,test,error):
        super().addError(test,error)
        self.stream.writeln(self.errors[-1][1])
result=unittest.TextTestRunner(verbosity=2,resultclass=ImmediateFailures).run(suite)
summary=[]
for sample in ['runtime',*selected_cases]:
    for operation in sorted({m['operation'] for m in measurements if m['case']==sample}):
        matching=[m for m in measurements if m['case']==sample and m['operation']==operation]
        unsupported=sum(m['status']=='unsupported' for m in matching)
        attempts=[m for m in matching if m['status']!='unsupported']
        values=sorted(m['ms'] for m in attempts if m['status']=='ok')
        row={'case':sample,'operation':operation,'attempts':len(attempts),'unsupportedCount':unsupported,'failures':sum(m['status']!='ok' for m in attempts),'totalElapsedMs':sum(m['ms'] for m in attempts),'failedElapsedMs':[m['ms'] for m in attempts if m['status']!='ok']}
        if values and (operation=='bulk_create' or operation.startswith('bulk_update_') and 'commit' not in operation or operation=='bulk_edges'):row['rowsPerSecond']=sum(m['rows'] for m in attempts if m['status']=='ok')/(sum(values)/1000)
        if values:
            row.update(p50Ms=statistics.median(values),minMs=min(values),maxMs=max(values))
            if len(values)>=100:row['p95Ms']=values[math.ceil(.95*len(values))-1]
            if len(values)>=1000:row['p99Ms']=values[math.ceil(.99*len(values))-1]
        summary.append(row)
for case in results:
    if case['status']=='running':case['status']='failed'
    def elapsed(operation):
        return [m['ms'] for m in measurements if m['case']==case['sample'] and m['operation']==operation and m['status']=='ok']
    one=elapsed('bulk_update_end_to_end_1');hundred=elapsed('bulk_update_end_to_end_100')
    if one and hundred:
        t1=statistics.median(one);t100=statistics.median(hundred)
        per_row=(t100-t1)/99;fixed=t1-per_row
        singles=elapsed('single_update_including_commit')
        case['napkinMath']={'model':'T(n) = fixedMs + n * perRowMs, fitted to median atomic groups 1 and 100',
            'fixedMs':fixed,'perRowMs':per_row,'fitValid':fixed>=0 and per_row>=0,
            'bulk100SpeedupOverCommittedSingles':100*statistics.median(singles)/t100 if singles else None,
            'qualification':'Local estimate only; no extrapolated atomic support beyond the configured and exercised limit. Requires independent batch sizes and repeated runs before a budget is agreed.'}
        thousand=elapsed('bulk_update_end_to_end_1000')
        if thousand and fixed>=0 and per_row>=0:
            predicted=fixed+1000*per_row
            observed=statistics.median(thousand)
            case['napkinMath']['independent1000RowCheck']={'predictedMs':predicted,'observedMedianMs':observed,'observedToPredictedRatio':observed/predicted if predicted else None}

# These are the matrix's declared triage signals, not invented latency guarantees.
performance_signals=[]
for case in results:
    model=case.get('napkinMath',{})
    speedup=model.get('bulk100SpeedupOverCommittedSingles')
    if speedup is not None and speedup<matrix_settings['minimumBulkImprovementOverSingles']:
        performance_signals.append({'case':case['sample'],'signal':'bulk100_speedup',
            'observed':speedup,'triageThreshold':matrix_settings['minimumBulkImprovementOverSingles']})
    check=model.get('independent1000RowCheck',{})
    ratio=check.get('observedToPredictedRatio')
    if ratio is not None and ratio>2:
        performance_signals.append({'case':case['sample'],'signal':'nonlinear_1000_row_cost',
            'observed':ratio,'triageThreshold':2})
performance_qualification=('incomplete' if not result.wasSuccessful() or args.load_only else
    'measured_with_triage_signals' if performance_signals else 'measured')

git_head=subprocess.run(['git','rev-parse','HEAD'],cwd=root,capture_output=True,text=True)
source_commit=git_head.stdout.strip() if git_head.returncode==0 else None
source_dirty=bool(subprocess.run(['git','status','--porcelain'],cwd=root,capture_output=True,text=True,check=True).stdout) if source_commit else None
atomic_attempts=[m for m in measurements if m['operation'] in ('bulk_create','bulk_edges','single_update_including_commit')
    or m['operation'].startswith('bulk_update_') and not m['operation'].startswith(('bulk_update_commit_','bulk_update_end_to_end_'))]
atomic_commits=[m for m in measurements if m['status']=='ok' and (m['operation'] in ('bulk_create_commit','bulk_edges_commit','single_update_including_commit') or m['operation'].startswith('bulk_update_commit_'))]
capacity_scope={'targetAtomicOperations':matrix_settings['targetAtomicGroupLimit'],
    'configuredExpectedAtomicOperations':args.expected_group_limit,
    'attemptedAtomicGroupSizes':sorted({m['rows'] for m in atomic_attempts}),
    'committedAtomicGroupSizes':sorted({m['rows'] for m in atomic_commits}),
    'qualification':'Only observed attempts and commits; configured limits do not establish actual maximum capacity.'}
report={'runtimePackage':runtime_package,'runtimeManifestSha256':hashlib.sha256(runtime_manifest).hexdigest(),'sourceCommit':source_commit,'sourceWorkingTreeDirty':source_dirty,'machine':platform.platform(),'python':platform.python_version(),'trussSource':str(root),
        'externalJavaScriptForbidden':args.forbid_external_javascript,'externalProcessExecutables':sorted(set(external_processes)),
        'statementTimeoutMs':10000,'operationTimeoutMs':30000,'expectedAtomicGroupLimit':args.expected_group_limit,'warmupReads':matrix_settings['warmupOperations'],
        'seconds':time.perf_counter()-start,'passed':result.wasSuccessful(),'functionalPassed':result.wasSuccessful(),
        'performanceQualification':performance_qualification,'performanceTriageSignals':performance_signals,
        'performanceBudgetStatus':'Latency budgets remain provisional; no prior-run nominal regression baseline supplied',
        'capacityScope':capacity_scope,
        'cases':results,'summary':summary,'samples':measurements,
        'scope':'Actual public workflows on isolated local PostgreSQL. Connection reopen, not server restart. Cold server/install separate. '+('Only the selected generated cases; indexes are unique business-key properties.' if args.matrix_case else 'Real-sample results only; no synthetic stress result implied.')}
args.output.parent.mkdir(parents=True,exist_ok=True)
args.output.write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'passed':report['passed'],'functionalPassed':report['functionalPassed'],'performanceQualification':report['performanceQualification'],'capacityScope':capacity_scope,'cases':results,'summary':summary},indent=2))
sys.exit(0 if result.wasSuccessful() else 1)
