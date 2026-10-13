from pathlib import Path
import sys,json
sys.path.insert(0,'/private/tmp/truss-psycopg-baseline-env/lib/python3.11/site-packages')
from psycopg.adapt import Transformer,Loader
from psycopg.pq import Format
calls=[]
class SelectedLoader(Loader):
 def __init__(self,*a,**k):calls.append('constructor');super().__init__(*a,**k)
 def load(self,data):calls.append('load');return 'test'
t=Transformer();t.adapters.register_loader(19,SelectedLoader);loader=t.get_loader(19,Format.TEXT)
assert calls==['constructor']
result={'passed':True,'callsBeforeAnyRowLoad':calls,'scope':'Actual supported binary Transformer loader factory; no SQL/native result execution. Constructor can execute before load; descriptor-first fetch refusal is not an adapter callback sandbox.'}
Path('/private/tmp/python-subject-review-20261013/loader-constructor.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result))
