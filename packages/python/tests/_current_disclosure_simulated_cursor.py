"""Simulated cursor only. It executes no SQL and proves no native admission."""
import json,types
class Deadline:
 def check(self):pass
class StageCursor:
 def __init__(self,mode):self._deadline=Deadline();self.connection=self;self.rows=[];self.description=None;self.mode=mode;self.dropped=False
 def execute(self,query,parameters=None,**kw):
  text=query.as_string() if hasattr(query,'as_string') else query
  if text.startswith('INSERT'):self.rows.append(tuple(parameters[1:]));self.description=None
  elif text.startswith('SELECT count'):self.out=(str(len(self.rows)),)
  elif text.startswith('SELECT private_key'):
   self.description=[types.SimpleNamespace(type_code=25)]*len(self.rows[0]) if self.rows else [types.SimpleNamespace(type_code=25)]*2
  elif text.startswith('DROP'):self.dropped=True
  return self
 def fetchone(self):return self.out
 def fetchmany(self,n):return sorted(self.rows)[:n]
class Raw:
 def __init__(self,connection,**kw):self.c=connection
 def __enter__(self):return self
 def __exit__(self,*args):pass
 def execute(self,query,**kw):
  assert query.startswith('SELECT ') and kw=={'prepare':False,'binary':False}
  self.description=[types.SimpleNamespace(type_code=25,name='output_0'),types.SimpleNamespace(type_code=25,name='__weft_source_rows')]
  self.rows=[(row[1],json.dumps({'version':'weft.stage-row-tuple/0.1-candidate','rows':[{'scan':'s0','key':row[0]}]})) for row in reversed(self.c.rows)]
  if self.c.mode=='missing':self.rows=self.rows[1:]
  if self.c.mode=='null' and self.rows:self.rows[0]=(None,self.rows[0][-1])
 def fetchmany(self,n):return self.rows[:n]
