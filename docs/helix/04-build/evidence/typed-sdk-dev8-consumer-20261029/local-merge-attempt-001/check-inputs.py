from pathlib import Path
import sys,json,hashlib,zipfile,tarfile,importlib.metadata
root=Path('/out');source=Path('/tmp/work/packages/python/src/truss')
expected={p.relative_to(source).as_posix():p.read_bytes()for p in source.rglob('*')if p.is_file()and '__pycache__'not in p.parts and p.suffix!='.pyc'}
wheel=root/'artifacts/umf_truss-0.0.52-py3-none-any.whl'
with zipfile.ZipFile(wheel)as z:
 actual={n.removeprefix('truss/'):z.read(n)for n in z.namelist()if n.startswith('truss/')and not n.endswith('/')}
assert actual==expected
with tarfile.open(next((root/'artifacts').glob('*.tar.gz')))as t:
 actual={m.name.split('/src/truss/',1)[1]:t.extractfile(m).read()for m in t.getmembers()if m.isfile()and '/src/truss/'in m.name}
assert actual==expected
sys.path.insert(0,str(root/'generated'))
from native_sales.models import Order,OrderIdentity
from native_sales.keys import OrderKey,CustomerKey
assert set(Order.model_fields)=={'id','status'}
assert set(OrderIdentity.model_fields)=={'id'}
assert set(OrderKey.model_fields)=={'id'}
assert set(CustomerKey.model_fields)=={'customer_id'}
raw=Path('/tmp/work/scripts/fixtures/typed-sdk-core010/model.json').read_bytes()
assert Order.UMF_SOURCE.document_sha256==hashlib.sha256(raw).hexdigest()
assert Order.UMF_SOURCE.core_version=='0.10.0'
assert importlib.metadata.version('umf-access')=='0.1.0.dev8'
assert importlib.metadata.version('pydantic')=='2.13.5'
for name,expectedsha in [('umf_access-0.1.0.dev8-py3-none-any.whl','1a21c1ddd59f6b23e9f0b33228280564af0e96bb4d13699b89616d5143e4fd23')]:
 assert hashlib.sha256((root/'originals'/name).read_bytes()).hexdigest()==expectedsha
report=json.loads((root/'public-install-report.json').read_bytes())
for item in report['install']:
 name=item['metadata']['name'].lower().replace('_','-')
 if name!='umf-truss':assert item['download_info']['url'].startswith('https://files.pythonhosted.org/'),item
print(json.dumps({'sourcePayloadFiles':len(expected),'generatedShape':'Order/OrderIdentity/OrderKey/CustomerKey verified against original Core0.10 source','publicDependencyURLsVerified':True}))
