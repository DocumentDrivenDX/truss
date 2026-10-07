"""Original fixture diagnostic-to-Truss-obligation consistency only; no support admission."""
from pathlib import Path
import copy,hashlib,json
ROOT=Path(__file__).resolve().parents[5]
PATH=ROOT/'docs/helix/02-design/contracts/bindings/reference-account-items-diagnostic-handoff-v0.1.proposal.json'
CODES={'EXPERIMENTAL_CORE_NULLABILITY','EXPERIMENTAL_CORE_CARDINALITY','EXPERIMENTAL_CORE_FACETS','EXPERIMENTAL_CORE_KEYS','EXPERIMENTAL_CORE_RELATIONSHIPS'}
def require(ok):
 if not ok:raise ValueError('diagnostic handoff mismatch')
def verify(d):
 require(d['interfaceVersion']=='truss-reference-fixture-diagnostic-handoff/0.1.0')
 p=ROOT/d['sourceReceipt'];require(hashlib.sha256(p.read_bytes()).hexdigest()==d['sourceReceiptSha256']);o=json.loads(p.read_text());require(d['fixture']==o['source'] and d['originalValidation']==o['validation'])
 require(o['validation']['valid'] is True and o['validation']['complete'] is False)
 diagnostics=o['validation']['diagnostics'];require(len(diagnostics)==5 and {x['code'] for x in diagnostics}==CODES)
 require([x['originalDiagnostic'] for x in d['handoffs']]==diagnostics)
 require(all(x['status']=='unresolved; no native support or adoption inferred' and x['trussObligation'].strip() and x['governingContracts'] for x in d['handoffs']))
 require(d['unknownDiagnosticPolicy']=='refuse selected fixture handoff completeness; retain original diagnostic, never severity/code suppression')
original=json.loads(PATH.read_text());verify(original)
def missing(d):d['handoffs'].pop()
def duplicate(d):d['handoffs'][-1]=copy.deepcopy(d['handoffs'][0])
def changed_severity(d):d['handoffs'][0]['originalDiagnostic']['severity']='info'
def promoted(d):d['originalValidation']['complete']=True
def assumed_support(d):d['handoffs'][0]['status']='adopted'
def blank_obligation(d):d['handoffs'][0]['trussObligation']=''
controls=[]
for mutation in [missing,duplicate,changed_severity,promoted,assumed_support,blank_obligation]:
 d=copy.deepcopy(original);mutation(d)
 try:verify(d)
 except (ValueError,KeyError):controls.append({'case':mutation.__name__,'refused':True})
 else:raise RuntimeError('corruption accepted')
result={'scope':'five retained original diagnostic handoffs and six corruption refusals; no native/semantic support or adoption','status':'pass','controls':controls,'manifestSha256':hashlib.sha256(PATH.read_bytes()).hexdigest()}
Path(__file__).with_name('reference-diagnostic-handoff-audit.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'diagnostics':5,'controls':6,'status':'pass'}))
