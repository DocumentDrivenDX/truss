"""Replay four recorded pre-fix guard witnesses from its exact saved function."""
from pathlib import Path
from decimal import Decimal
import json
source=Path(__file__).with_name('before-guard.py')
ns={'expected_guard':(b'i',b'p',1)}
exec(compile(source.read_text(),str(source),'exec'),ns)
class Cursor:
 description=None
 def __init__(self,row):self.row=row;self.fetches=0
 def execute(self,*args,**kwargs):pass
 def fetchmany(self,n):self.fetches+=1;return [self.row]
controls=[]
for name,row in [('missing-descriptor',(b'i',b'p',1)),('boolean-generation',(b'i',b'p',True)),('numeric-generation',(b'i',b'p',Decimal(1))),('mutable-bytea',(bytearray(b'i'),bytearray(b'p'),1))]:
 c=Cursor(row);ns['guard'](c);assert c.fetches==1
 controls.append({'case':name,'accepted':True,'fetches':c.fetches})
assert controls==json.loads(Path(__file__).with_name('before-results.json').read_text())['controls']
print(json.dumps({'preFixWitnessesReplayed':len(controls),'scope':'Saved original guard function with synthetic cursor only'}))
