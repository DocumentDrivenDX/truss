import gzip,collections
folder=BASE/'4471bc46-d4d3-4390-8130-4055c68548e4';packet=result['packets']['routine-ddl-barrier'];extra_fail=[]
def check(ok,label):
 if not ok:extra_fail.append(label)
logs=[json.loads(line) for line in (folder/'tests.stdout.log').read_text().splitlines() if line.strip()]
expected_pairs=[('test_omitted_table_modes_allow_pending_commit_source_change',('pending','committed'),'pg_proc','prosrc',[' SELECT 333 ',' SELECT 444 ']),('test_selected_ddl_changes_source_not_epoch',('before','after'),'pg_proc','prosrc',[' SELECT 333 ',' SELECT 444 ']),('test_shared_role_change_is_explicitly_outside_barrier',('before-role','after-role'),'pg_roles','bypass',[False,True])]
expected_files={test+'-'+label+'.census.txt.gz' for test,labels,*_ in expected_pairs for label in labels}
check({p.name for p in folder.glob('*.census.txt.gz')}==expected_files,'exact six retained census files')
check(len(logs)==6 and len({(r['test'],r['census']) for r in logs})==6,'six unique stdout census observations')
with zipfile.ZipFile(folder/'sources.zip') as z:
 barrier=z.read(str(ROOT/'packages/postgresql/native/source-epoch-routine-ddl-barrier.sql').lstrip('/')).decode()
 test_source=z.read(str(ROOT/'packages/python/tests/test_routine_ddl_barrier_native.py').lstrip('/')).decode()
 original_body=barrier.split('AS $$',1)[1].split('$$;',1)[0]
function=barrier.split('REVOKE ALL',1)[0].replace('CREATE FUNCTION','CREATE OR REPLACE FUNCTION',1)
lock_marker=' LOCK TABLE truss.source_epoch_current, truss.source_epoch_registry IN ROW EXCLUSIVE MODE NOWAIT;'
own_marker=' IF EXISTS(SELECT 1 FROM pg_catalog.pg_locks l'
check(function.count(lock_marker)==function.count(own_marker)==1,'independent exact mutation marker counts')
mutant_body=original_body.replace(lock_marker,' -- Deliberate omitted writer table modes.')
image_details={};images={};tuples={}
for row in logs:
 name=row['test']+'-'+row['census']+'.census.txt.gz';data=gzip.decompress((folder/name).read_bytes());obj=json.loads(data);images[name]=obj
 check(type(row['octets']) is int and len(data)==row['octets']<=16777216 and sha(data)==row['sha256'],name+' hash/size stdout correspondence')
 check(obj['version']=='truss.security.query-source-census/0.1.0' and obj['serverVersion']=='160015' and obj['database']=='routine_ddl_barrier_component' and len(obj['sections'])==40,name+' census exact version/database/sections')
 sections={k:[json.loads(r) for r in rows] for k,rows in obj['sections'].items()}
 check(int(obj['rowCount'])==sum(len(rows) for rows in sections.values())<=100000 and all(len(rows)<=8192 for rows in sections.values()),name+' complete row count/bounds')
 def only(section,predicate):
  rows=[r for r in sections[section] if predicate(r)];check(len(rows)==1,name+' unique '+section);return rows[0]
 ns=only('pg_namespace',lambda r:r.get('nspname')=='truss')
 subject=only('pg_proc',lambda r:r.get('proname')=='ddl_subject' and r.get('pronamespace')==ns['oid'])
 hook=only('pg_event_trigger',lambda r:r.get('evtname')=='truss_routine_ddl_writer_barrier')
 routine=only('pg_proc',lambda r:r.get('oid')==hook['evtfoid'])
 ordinary=only('pg_roles',lambda r:r.get('name')=='ddl_barrier_ordinary')
 check(subject['pronargs']==0 and subject['proargtypes']==[] and subject['prorettype']=='23' and subject['prokind']=='f',name+' subject exact signature')
 check(hook['evtevent']=='ddl_command_start' and hook['evtenabled']=='A' and hook['evttags']==['CREATE FUNCTION','ALTER FUNCTION','DROP FUNCTION','CREATE PROCEDURE','ALTER PROCEDURE','DROP PROCEDURE'],name+' exact ALWAYS six-tag hook')
 expected_body=mutant_body if row['test'].startswith('test_omitted_table_modes_') else original_body
 check(routine['proname']=='runtime_fence_routine_ddl_writer' and routine['pronamespace']==ns['oid'] and routine['prosrc']==expected_body and routine['prosecdef'] is False and routine['provolatile']=='v' and routine['proconfig']==['search_path=pg_catalog, pg_temp'],name+' exact installed original/mutant body/linkage')
 tuples[name]={'namespaceOid':ns['oid'],'subjectOid':subject['oid'],'subjectBody':subject['prosrc'],'hookOid':hook['oid'],'hookRoutineOid':routine['oid'],'hookBodySha256':sha(routine['prosrc'].encode()),'hookBodyVariant':'omitted-table-modes' if expected_body==mutant_body else 'original','ordinaryRoleOid':ordinary['oid'],'ordinaryRoleBypass':ordinary['bypass']}
 image_details[name]={'compressedSha256':sha((folder/name).read_bytes()),'uncompressedSha256':sha(data),'octets':len(data),'rowCount':obj['rowCount'],'sectionCount':40,'tupleIdentities':tuples[name]}
diffs=[]
for test,labels,wanted_section,wanted_field,wanted_values in expected_pairs:
 names=[test+'-'+label+'.census.txt.gz' for label in labels];a,b=[images[n] for n in names];section_diffs={}
 for sec in a['sections']:
  x,y=collections.Counter(a['sections'][sec]),collections.Counter(b['sections'][sec]);left=list((x-y).elements());right=list((y-x).elements())
  if left or right:
   if len(left)==len(right)==1:
    old,new=json.loads(left[0]),json.loads(right[0]);fields={k:[old.get(k),new.get(k)] for k in old.keys()|new.keys() if old.get(k)!=new.get(k)}
   else:fields=None
   section_diffs[sec]={'removedRows':len(left),'addedRows':len(right),'fieldChanges':fields}
 check(section_diffs=={wanted_section:{'removedRows':1,'addedRows':1,'fieldChanges':{wanted_field:wanted_values}}},test+' exact one-field pair difference')
 check(all(tuples[names[0]][k]==tuples[names[1]][k] for k in ('namespaceOid','subjectOid','hookOid','hookRoutineOid','ordinaryRoleOid')),test+' original object identities retained')
 diffs.append({'test':test,'images':names,'differences':section_diffs})
restored='test_selected_ddl_changes_source_not_epoch-before.census.txt.gz'
check(tuples[restored]['hookBodyVariant']=='original','original hook body independently observed after both erasure tests')
check(image_details[restored]['uncompressedSha256']==image_details['test_shared_role_change_is_explicitly_outside_barrier-before-role.census.txt.gz']['uncompressedSha256'],'exact whole census restored after committed subject edit')
packet['censusAudit']={'images':image_details,'isolatedPairDifferences':diffs,'mutationMarkers':{'tableModeCount':function.count(lock_marker),'ownShareCount':function.count(own_marker)},'restorationEvidence':['Later census retains exact original hook body and ALWAYS metadata after both erasure tests and administrative hook-disable test.','Selected-change before census equals shared-role before census byte-for-byte, corroborating subject restoration.','Role reset runs successfully within the passing source test; no separate post-reset census is retained. Entire owned fixture is then removed.'],'findings':extra_fail}
for f in extra_fail:result['integrityFindings'].append({'packet':'routine-ddl-barrier','finding':f})
if extra_fail:result['status']='integrity-findings'
