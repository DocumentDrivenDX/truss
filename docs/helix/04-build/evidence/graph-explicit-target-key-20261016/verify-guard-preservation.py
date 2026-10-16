"""Read-only syntactic preservation check of the retained historical source."""
from pathlib import Path
import ast,zipfile,json,hashlib
root=Path(__file__).resolve().parent
with zipfile.ZipFile(root/'frozen-review.zip') as z:
 pins=json.loads(z.read('manifest.json'))
 for n,pin in pins.items():
  raw=z.read(n);assert {'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}==pin,n
 path='packages/python/src/truss/_current_disclosure_facts.py'
 old=ast.parse(z.read('before/'+path));new=ast.parse(z.read('after/'+path))
 function=next(n for n in new.body if isinstance(n,ast.FunctionDef) and n.name=='_graph_recipes')
 loop=next(n for n in function.body if isinstance(n,ast.For) and isinstance(n.target,ast.Name) and n.target.id=='association')
 at=next(i for i,n in enumerate(loop.body) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='targets' for t in n.targets))
 assert isinstance(loop.body[at+1],ast.If);del loop.body[at:at+2]
 assert ast.dump(old,include_attributes=False)==ast.dump(new,include_attributes=False)
print(json.dumps({'passed':True,'scope':'Only the target binding/refusal is added; all other source AST is unchanged. Not a whole-program or native proof.'}))
