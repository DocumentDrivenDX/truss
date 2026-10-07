"""Review-profile algorithm experiment; not a bounded production parser or native codec."""
import hashlib,json,sys
from pathlib import Path

def require(ok,message):
    if not ok: raise ValueError(message)
def quoted(value):
    pieces=['"']
    for character in value:
        code=ord(character)
        if 0xd800<=code<=0xdfff: raise ValueError('unpaired surrogate')
        if character in ('"','\\'): pieces.append('\\'+character)
        elif code<32: pieces.append('\\u'+format(code,'04x'))
        else: pieces.append(character)
    return ''.join(pieces)+'"'
def canonical(value,depth=0):
    require(depth<=64,'experiment depth guard')
    if value is None: return 'null'
    if value is True: return 'true'
    if value is False: return 'false'
    if isinstance(value,str): return quoted(value)
    if isinstance(value,list): return '['+','.join(canonical(v,depth+1) for v in value)+']'
    if isinstance(value,dict):
        require(all(isinstance(k,str) for k in value),'structural key type')
        keys=sorted(value,key=lambda k:k.encode('utf-8',errors='strict'))
        return '{'+','.join(quoted(k)+':'+canonical(value[k],depth+1) for k in keys)+'}'
    raise ValueError('native number/unsupported node')
def pairs(members):
    result={}
    for key,value in members:
        require(key not in result,'duplicate structural member')
        result[key]=value
    return result
def forbidden_number(_): raise ValueError('native number')
def admit(raw):
    require(len(raw)<=65536,'experiment byte guard')
    value=json.loads(raw.decode('utf-8',errors='strict'),object_pairs_hook=pairs,parse_int=forbidden_number,parse_float=forbidden_number,parse_constant=forbidden_number)
    require(canonical(value).encode('utf-8')==raw,'noncanonical original bytes')
    return value
positives=[
 ('structural order',{'z':False,'a':None},'{"a":null,"z":false}'),
 ('exact token',{'token':'1.00','kind':'number'},'{"kind":"number","token":"1.00"}'),
 ('control escapes',{'text':'\x00\n\t\r'},'{"text":"\\u0000\\u000a\\u0009\\u000d"}'),
 ('quote and reverse solidus',{'text':'"\\/'},'{"text":"\\"\\\\/"}'),
 ('Unicode scalar',{'text':'é雪😀'},'{"text":"é雪😀"}'),
 ('decomposed Unicode',{'text':'e\u0301'},'{"text":"e\u0301"}'),
 ('ordered domain members',{'members':[{'name':'z'},{'name':'a'}]},'{"members":[{"name":"z"},{"name":"a"}]}'),
 ('empty structures',{'a':[],'b':{}},'{"a":[],"b":{}}')
]
outcomes=[]
for name,value,expected in positives:
    raw=canonical(value).encode('utf-8')
    require(raw==expected.encode('utf-8'),'expected original bytes '+name)
    require(admit(raw)==value,'decoded semantic tree '+name)
    outcomes.append({'name':name,'passed':True,'expectedSha256':hashlib.sha256(expected.encode()).hexdigest()})
negatives=[('duplicate keys',b'{"a":null,"a":true}'),('wrong structural order',b'{"z":false,"a":null}'),('short control escape',b'{"text":"\\n"}'),('escaped solidus',b'{"text":"\\/"}'),('escaped admitted Unicode',b'{"text":"\\u00e9"}'),('integer node',b'{"v":1}'),('floating node',b'{"v":1.0}'),('nonfinite node',b'{"v":NaN}'),('trailing data',b'{}{}'),('invalid UTF8',b'{"text":"\xff"}'),('unpaired surrogate',b'{"text":"\\ud800"}'),('extra whitespace',b'{ "a":null}')]
for name,raw in negatives:
    try: admit(raw)
    except (ValueError,UnicodeError): outcomes.append({'name':name,'refused':True})
    else: raise ValueError('invalid canonical input admitted '+name)
print(json.dumps({'scope':'eight independently specified canonical-byte cases and twelve refusal cases only; 64-depth/65536-byte experiment guards are not production resource proof','pythonVersion':sys.version.split()[0],'helperSha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'outcomes':outcomes,'profile':'truss-journal-json/0.2.0-proposal','nativeExecuted':False,'productionParserQualified':False,'adopted':False},indent=2))
