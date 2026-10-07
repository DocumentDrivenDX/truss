"""Independent planned-fixture consistency only; no production decoder/native execution."""
import hashlib,json,math,platform,re,struct
from fractions import Fraction
from pathlib import Path
base=Path('docs/helix/02-design/contracts/bindings')
def require(value,message):
 if not value:raise RuntimeError(message)
files={
 'bootstrap-basis-list-order-v0.1.vectors.proposal.json':6,
 'bootstrap-routine-settings-v0.1.vectors.proposal.json':10,
 'bootstrap-address-token-v0.1.vectors.proposal.json':15,
 'bootstrap-float4-v0.1.vectors.proposal.json':12,
}
checked=[]
for name,count in files.items():
 path=base/name;raw=path.read_bytes();data=json.loads(raw)
 cases=data.get('vectors',data.get('cases'))
 require(len(cases)==count,name+': expected fixture inventory changed')
 for index,c in enumerate(cases):
  context=f'{name}:{index}'
  if 'basis-list' in name:
   try:encoded=[x.encode('utf-8') for x in c['input']]
   except UnicodeEncodeError:
    require(c.get('refusal')=='invalid_unicode_scalar',context);continue
   if len(set(encoded))!=len(encoded):require(c.get('refusal')=='duplicate_identity',context)
   else:require(sorted(c['input'],key=lambda x:x.encode('utf-8'))==c['expected'],context)
  elif 'routine-settings' in name:
   x=c['input']
   reason='null_element' if x is None else 'invalid_native_text' if '\x00' in x else 'missing_separator' if '=' not in x else 'empty_name' if x.startswith('=') else None
   if reason:require(c.get('refusal')==reason,context)
   else:
    name_part,value=x.split('=',1)
    require(c['expected']=={'name':name_part,'value':value},context)
  elif 'address-token' in name:
   token=c['token'];domain=c['domain'];require(domain in ('oid','int4'),context)
   valid=bool(re.fullmatch('0|[1-9][0-9]*' if domain=='oid' else '0|-?[1-9][0-9]*',token)) and len(token.lstrip('-'))<=10
   if valid:valid=0<=int(token)<=4294967295 if domain=='oid' else -2147483648<=int(token)<=2147483647
   require(valid==('acceptedToken' in c),context)
   if valid:require(c['acceptedToken']==token,context)
   else:require(c.get('refusal')=='invalid_native_integer',context)
  else:
   h=c['hex']
   if not re.fullmatch('[0-9a-f]{8}',h):require(c.get('refusal')=='invalid_hex',context);continue
   value=struct.unpack('>f',bytes.fromhex(h))[0];expected=c['expected']
   require(expected['sign']==('negative' if math.copysign(1,value)<0 else 'positive'),context)
   if math.isnan(value):
    require(expected['class']=='nan',context)
    require(expected['fractionBits']==str(int(h,16)&8388607),context)
   elif math.isinf(value):require(expected['class']=='infinity',context)
   elif value==0:require(expected['class']=='zero',context)
   else:
    require(expected['class']=='finite',context)
    m=int(expected['mantissa']);e=int(expected['exponent'])
    require(0<m<=16777215 and -149<=e<=104,context)
    factor=Fraction(2**e) if e>=0 else Fraction(1,2**(-e))
    require(Fraction.from_float(abs(value))==m*factor,context)
 require(path.read_bytes()==raw,name+': fixture changed during audit')
 checked.append({'path':str(path),'sha256':hashlib.sha256(raw).hexdigest(),'cases':count})
receipt={'scope':'Independent planned fixture consistency only; no Truss decoder, complete basis, original custody, native send/settings/privilege or runtime support qualification','pythonVersion':platform.python_version(),'verifierSha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'fixtures':checked,'cases':sum(files.values()),'pass':True}
Path('docs/helix/04-build/evidence/design-audit/bootstrap-decoder-fixtures.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({'fixtures':len(checked),'cases':receipt['cases'],'pass':True,'scope':receipt['scope']}))
