// SPIKE-002: validate every model revision with UMF's library (pinned master export in $UMF_DIR) and run
// UMF's CONTRACT-043 DDD-to-PostgreSQL generator (tables stage, then tables+indexes stage) on rev0.
// Writes out/01_model_validation.txt, sql/a_generated_tables.sql, sql/a_generated_tables_indexes.sql,
// out/02_generator_report.json. Run from anywhere: bun model/validate_and_generate.ts
import {readFileSync,writeFileSync} from 'node:fs';
import {dirname,join} from 'node:path';
const here=dirname(new URL(import.meta.url).pathname),spike=join(here,'..');
const UMF=process.env.UMF_DIR;if(!UMF)throw new Error('set UMF_DIR (source env.sh)');
const umf=await import(join(UMF,'src/index.ts'));
const {backend}=await import(join(UMF,'native/postgresql/runtime.ts'));
const lines:string[]=[];const log=(...a:any[])=>{const s=a.map(x=>typeof x==='string'?x:JSON.stringify(x)).join(' ');lines.push(s);console.log(s);};
const read=(f:string)=>JSON.parse(readFileSync(join(here,f),'utf8'));

log('UMF export:',UMF);
for(const rev of ['rev0','rev1','rev2','rev3','rev4','rev5']){
  const doc=read(`sales.${rev}.umf.json`);
  const core=umf.validateDocument(doc);
  const ddd=umf.inspectDdd(doc);
  const errs=(v:any)=>v.diagnostics.filter((d:any)=>d.severity==='error');
  const warns=(v:any)=>v.diagnostics.filter((d:any)=>d.severity!=='error');
  log(`[${rev}] umf=${doc.umf} core.valid=${core.valid} errors=${errs(core).length} warnings=${warns(core).length}; ddd.valid=${ddd.valid} errors=${errs(ddd).length} warnings=${warns(ddd).length}`);
  {const seen=new Set<string>();for(const d of [...core.diagnostics,...ddd.diagnostics]){const k=d.severity+d.code+d.path;if(seen.has(k))continue;seen.add(k);log('   ',d.severity,d.code,d.path,d.message);}}
  if(rev==='rev0'||rev==='rev3'){
    const rel=umf.inspectCoreRelationships(doc,{module:'sales'});
    log(`   inspectCoreRelationships: state=${rel.meaning?.state} count=${rel.meaning?.relationships?.length??'-'} uninterpreted=${JSON.stringify(rel.meaning?.uninterpretedPaths??[])}`);
    for(const r of ['Customer','Order','OrderLine','Product']){
      const k=umf.inspectCoreKeys(doc,{module:'sales',element:r});
      log(`   inspectCoreKeys(${r}): state=${k.meaning.state} keys=${(k.meaning.keys??[]).map((x:any)=>x.id+(x.primary?'*':'')).join(',')}`);
    }
  }
}

// Generator: CONTRACT-043 relationship-independent stages
const logical=read('sales.rev0.umf.json'),binding=read('sales.binding.json'),policy=read('sales.policy.json');
const b=umf.inspectBinding(binding,logical);
log(`[binding] valid=${b.valid}`);for(const d of b.diagnostics)log('   ',d.severity,d.code,d.path,d.message);
for(const [label,fn,out] of [['tables',umf.projectDddTablesToPostgresql,'a_generated_tables.sql'],['tables+indexes',umf.projectDddTablesAndIndexesToPostgresql,'a_generated_tables_indexes.sql']] as const){
  for(const loss of ['strict','report'] as const){
    try{
      const r=await fn(logical,binding,backend,policy,loss);
      log(`[generator ${label} ${loss}] status=${r.status} residuals=${r.residuals.length} mappings=${r.mappings.length} candidate=${r.candidate?'yes':'no'}`);
      if(loss==='report'){
        if(r.candidate)writeFileSync(join(spike,'sql',out),r.candidate);
        writeFileSync(join(spike,'out',label==='tables'?'02_generator_report_tables.json':'02_generator_report_tables_indexes.json'),JSON.stringify({status:r.status,target:r.target,residuals:r.residuals,mappings:r.mappings},null,1)+'\n');
        const byReason=new Map<string,number>();for(const x of r.residuals)byReason.set(x.reason,(byReason.get(x.reason)??0)+1);
        for(const [k,v] of byReason)log(`    residual x${v}: ${k}`);
      }
    }catch(e:any){log(`[generator ${label} ${loss}] THREW ${e.code??''} ${e.message}`);}
  }
}
// Probe: does the generator cross-check the policy's SQL types against the core 0.7.0 facets? Contradict two of them.
{const bad=JSON.parse(JSON.stringify(policy));
 for(const r of bad.fieldTypes){if(r.element==='Customer'&&r.field==='name')r.sqlType='varchar(10)';if(r.element==='Order'&&r.field==='total')r.sqlType='numeric(5,4)';}
 const r=await umf.projectDddTablesAndIndexesToPostgresql(logical,binding,backend,bad,'report');
 const base=await umf.projectDddTablesAndIndexesToPostgresql(logical,binding,backend,policy,'report');
 const key=(x:any)=>x.path+'|'+x.reason;const same=JSON.stringify(r.residuals.map(key).sort())===JSON.stringify(base.residuals.map(key).sort());
 log(`[facet probe] policy Customer.name=varchar(10) (core length max 100), Order.total=numeric(5,4) (core precision 14 scale 2): status=${r.status} residuals=${r.residuals.length} (baseline ${base.residuals.length}); residual paths+reasons identical to baseline: ${same}; candidate contains "name" varchar(10): ${r.candidate?.includes('"name" varchar(10)')} and "total" numeric(5,4): ${r.candidate?.includes('"total" numeric(5,4)')}`);}
// Key tuple encoder on a 0.7.0 document (used later by the option C alternative)
const t0=performance.now();let n=0;
for(let i=0;i<200;i++){umf.encodeCoreKeyTuple(logical,{module:'sales',element:'Customer',key:'account-code'},[{string:'C'+i}]);n++;}
const ms=performance.now()-t0;
const rc=umf.encodeCoreKeyTuple(logical,{module:'sales',element:'Customer',key:'identity'},[{integerToken:'9223372036854775807'}]);
log(`[key-tuple] encodeCoreKeyTuple Customer.identity(9223372036854775807) -> ${rc.bytesHex}; ${n} calls in ${ms.toFixed(0)} ms (${(n/ms*1000).toFixed(0)} keys/s; validates the whole document per call)`);
for(const v of [{decimalToken:'1.201'}]){try{umf.encodeCoreKeyTuple(logical,{module:'sales',element:'Customer',key:'identity'},[v]);log('[key-tuple] unexpected accept');}catch(e:any){log(`[key-tuple] refused ${JSON.stringify(v)} for integer key: ${e.code}`);}}
writeFileSync(join(spike,'out','01_model_validation.txt'),lines.join('\n')+'\n');
