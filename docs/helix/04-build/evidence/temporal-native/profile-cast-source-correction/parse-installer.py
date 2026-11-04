from pathlib import Path
import re,json,subprocess
from pglast import parse_sql,parse_plpgsql,ast
import sys
root=Path(sys.argv[1]) if len(sys.argv)>1 else Path('/private/tmp/umf-stack-release-truss/packages/python/src/truss/_catalog_runtime')
results=[];errors=[];total=0
rowtypes=set(re.findall(r'CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?truss\.([a-z_][a-z_0-9]*)', '\n'.join(p.read_text() for p in root.glob('*.sql')),re.I))
for path in sorted(root.glob('*.sql')):
 text=path.read_text()
 # Two source files contain a pre-install planned-basis section. The installer
 # consumes only their suffix, exactly as catalog_runtime._verified_release.
 if path.name in ('catalog-rebind.sql','catalog-key-backfill.sql'):text='-- Planned basis'+text.split('-- Planned basis',1)[1]
 try:stmts=parse_sql(text)
 except Exception as e:errors.append({'file':path.name,'stage':'SQL','error':str(e)});continue
 for raw in stmts:
  n=raw.stmt
  if not isinstance(n,ast.CreateFunctionStmt):continue
  total+=1
  options={o.defname:o.arg for o in n.options}
  lang=options.get('language');lang=getattr(lang,'sval','')
  if lang!='plpgsql':continue
  fragment=text[raw.stmt_location:raw.stmt_location+raw.stmt_len] if raw.stmt_len else text[raw.stmt_location:]
  # libpg_query has no live catalog. Replace only table-row declarations with
  # record for syntax diagnostics; never use this to claim native compilation.
  fragment=re.sub(r'\btruss\.[a-z_][a-z_0-9]*%ROWTYPE\b','record',fragment,flags=re.I)
  diagnostic=re.sub(r'\btruss\.[a-z_][a-z_0-9]*(?:%ROWTYPE)?\b(?!\s*\()',lambda m:'record' if re.match(r'\s*[,;:=]',fragment[m.end():]) else m.group(),fragment,flags=re.I)
  for rowtype in rowtypes:diagnostic=re.sub(r'\btruss\.'+rowtype+r'\b','record',diagnostic)
  diagnostic=diagnostic.replace('record[]','pg_catalog.pg_class[]')
  try:parse_plpgsql(diagnostic);results.append({'file':path.name,'function':'.'.join(x.sval for x in n.funcname),'parsed':True})
  except Exception as e:errors.append({'file':path.name,'function':'.'.join(x.sval for x in n.funcname),'stage':'PLpgSQL','error':str(e)})
print(json.dumps({'scope':'offline grammar diagnostic only, rowtypes replaced with record, composite arrays with pg_catalog.pg_class[] for catalog-free grammar only; actual PG compilation mandatory','sqlFiles':len(list(root.glob('*.sql'))),'functions':total,'plpgsqlParsed':len(results),'errors':errors,'parsed':results},indent=2))
