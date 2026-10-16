from pathlib import Path
import re,json,statistics,gzip
root=Path(__file__).parent
pattern=re.compile(r'TRUSS_STAGE function=(\S+) phase=(\S+) pid=(\d+) stage_ms=([\d.]+) total_ms=([\d.]+) check_final=(\S+) attempt=(\S+)')
calls=[];active={}
for line in gzip.decompress((root/'postgres.log.gz').read_bytes()).decode().splitlines():
 m=pattern.search(line)
 if not m:continue
 fn,phase,pid,stage,total,final,attempt=m.groups();key=(fn,pid)
 if phase=='start':
  call={'function':fn,'pid':int(pid),'checkFinal':final,'attempt':attempt,'phases':[]};calls.append(call);active[key]=call
 if key not in active:raise ValueError('marker without start')
 active[key]['phases'].append({'phase':phase,'stageMs':float(stage),'totalMs':float(total)})
for c in calls:
 last=c['phases'][-1];c['totalMs']=last['totalMs'];c['complete']=last['phase']==('output_end' if c['function']=='runtime_owned_prepare' else 'authority_end' if c['checkFinal']=='false' else 'forest_end')
large=[c for c in calls if c['totalMs']>=250]
summary=[]
for fn in sorted({c['function'] for c in large}):
 for final in sorted({c['checkFinal'] for c in large if c['function']==fn}):
  selected=[c for c in large if c['function']==fn and c['checkFinal']==final]
  phases=sorted({p['phase'] for c in selected for p in c['phases'] if p['phase']!='start'})
  summary.append({'function':fn,'checkFinal':final,'calls':len(selected),'incomplete':sum(not c['complete'] for c in selected),'phases':[{'phase':phase,'samples':len(values),'medianMs':statistics.median(values),'maxMs':max(values)} for phase in phases if (values:=[p['stageMs'] for c in selected for p in c['phases'] if p['phase']==phase])]})
report={'scope':'Disposable instrumented phase costs only; large calls selected by >=250ms observed total. No production performance qualification. Missing end markers mean incomplete calls, not zero cost.','calls':len(calls),'incompleteCalls':sum(not c['complete'] for c in calls),'largeCallSummary':summary,'largeCalls':large}
(root/'stage-analysis.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k!='largeCalls'},indent=2))
