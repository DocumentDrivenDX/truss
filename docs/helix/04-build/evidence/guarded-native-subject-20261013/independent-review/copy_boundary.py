from pathlib import Path
from unittest.mock import patch
from dataclasses import replace,dataclass
from types import ModuleType
import json,sys,hashlib
ROOT=Path('/private/tmp/truss-security-main-integration');OUT=Path(__file__).parent
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'packages/python/src')]
import security_catalog_subject_read as current
from truss._psycopg_fact_cut import _FactRelationComparison,_FactColumnComparison
from truss._psycopg_subject_observation import _SubjectSelection
from truss._security_mapping import PreparedSecurityMapping
from truss.psycopg_host import PsycopgHost
raw=(OUT/'subject-pre-fix.py').read_bytes()
mod=ModuleType('captured_subject_before_copy_fix');mod.__file__=str(ROOT/'scripts/security_catalog_subject_read.py');exec(compile(raw,str(OUT/'subject-pre-fix.py'),'exec'),mod.__dict__)
E=ROOT/'docs/helix/04-build/evidence/accepted-catalog-policy-read-20261013'
req=(E/'request.json').read_bytes();mapping=PreparedSecurityMapping(req,b'{}',accepted_catalog_assessment=(E/'assessment.json').read_bytes())
selection=_SubjectSelection(req,(current.BASE/'document.json').read_bytes(),'m','Staff','pk','consumer','truss','catalog_subject_current',('staff_id',))
caller=object.__new__(PsycopgHost);executor=object.__new__(PsycopgHost);column=_FactColumnComparison('id',1,25,-1,True,0)
base=(_FactRelationComparison('truss','object',10,20,'body'),_FactRelationComparison('truss','catalog_subject_map',11,20,'body'))
class EnteredPreparation(Exception):pass
outputs=[]
def probe(label,columns):
 entries=[]
 def prepare(*a,**k):entries.append(True);raise EnteredPreparation()
 try:
  with patch.object(mod,'_prepare_subject_operation',prepare):mod.run_guarded_native_catalog_resource_read(caller,None,executor,None,mapping,selection,None,(replace(base[0],columns=columns),base[1]))
  outcome='unexpected return'
 except EnteredPreparation:outcome='input reached subject preparation'
 except Exception as e:outcome=type(e).__name__+': '+str(e)
 outputs.append({'case':label,'outcome':outcome,'subjectPreparationEntries':len(entries)})
probe('valid tuple baseline',(column,))
probe('list coerced into accepted tuple',[column])
visits=[]
def source():visits.append('iterated');yield column
probe('generator entered and coerced into accepted tuple',source())
assert len(visits)==1
construction=[]
@dataclass
class Foreign:
 value:int=0
 def __post_init__(self):construction.append(True)
f=Foreign();construction.clear();probe('foreign column constructor executes before refusal',(f,))
assert len(construction)==1
assert all(v['subjectPreparationEntries']==1 for v in outputs[:3]) and outputs[-1]['subjectPreparationEntries']==0
result={'scope':'Captured actual pre-fix wrapper; valid original named source selection and exact-type host shells. Execution stops before inspector/host/native work. No infinite iterable or large allocation attempted.','sourceSha256':hashlib.sha256(raw).hexdigest(),'observations':outputs,'generatorIterations':len(visits),'foreignConstructorCallsBeforeRefusal':len(construction)}
(OUT/'copy-boundary-before.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
