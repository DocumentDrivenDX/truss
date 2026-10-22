"""Download and independently verify the actual public source48 migration input."""
import base64,csv,hashlib,io,json,re,stat,subprocess,zipfile
from email.parser import BytesParser
from pathlib import Path


def sha(p):
 return hashlib.sha256(p.read_bytes()).hexdigest()

def safe_member(name):
 return bool(name) and "\\" not in name and "\x00" not in name and all(p not in ('','.','..') for p in name.rstrip('/').split('/')) and not name.startswith('/')

def checksum_entries(text):
 entries={}
 for line in text.splitlines():
  match=re.fullmatch(r'([0-9a-f]{64}) [ *]([^/\\\x00]+)',line)
  if not match:raise ValueError('Malformed checksum row')
  digest,name=match.groups()
  if name in entries or name in ('.','..'):raise ValueError('Duplicate or unsafe checksum name')
  entries[name]=digest
 if not entries:raise ValueError('Empty checksum manifest')
 return entries

def verify_wheel(z):
 infos=z.infolist();names=[i.filename for i in infos]
 if len(names)!=len(set(names)):raise ValueError('Duplicate ZIP member')
 for info in infos:
  kind=stat.S_IFMT(info.external_attr>>16)
  if not safe_member(info.filename) or info.flag_bits&1 or kind not in (0,stat.S_IFREG,stat.S_IFDIR) or (kind==stat.S_IFDIR and not info.is_dir()):
   raise ValueError('Unsafe ZIP member')
 if z.testzip() is not None:raise ValueError('ZIP CRC mismatch')
 record='truss_toolkit-0.0.48.dist-info/RECORD'
 if [n for n in names if n.endswith('.dist-info/RECORD')]!=[record]:raise ValueError('Unexpected wheel RECORD')
 rows={}
 for row in csv.reader(io.StringIO(z.read(record).decode('utf-8'),newline=''),strict=True):
  if len(row)!=3 or not safe_member(row[0]) or row[0] in rows:raise ValueError('Malformed or duplicate RECORD row')
  rows[row[0]]=row[1:]
 if set(rows)!={i.filename for i in infos if not i.is_dir()}:raise ValueError('RECORD membership mismatch')
 for name,(digest,size) in rows.items():
  if name==record:
   if digest or size:raise ValueError('RECORD self entry must be empty')
   continue
  payload=z.read(name);algorithm,sep,expected=digest.partition('=')
  if not sep or algorithm not in ('sha256','sha384','sha512'):raise ValueError('Invalid RECORD digest')
  actual=base64.urlsafe_b64encode(hashlib.new(algorithm,payload).digest()).rstrip(b'=').decode('ascii')
  if actual!=expected or not size.isdecimal() or int(size)!=len(payload):raise ValueError('RECORD digest/size mismatch')
 metadata=BytesParser().parsebytes(z.read('truss_toolkit-0.0.48.dist-info/METADATA'))
 if metadata.get_all('Name')!=['truss-toolkit'] or metadata.get_all('Version')!=['0.0.48']:raise ValueError('Wrong wheel metadata')
 return len(rows)

def verify_files(z,prefix,manifest):
 for name,digest in manifest['files'].items():
  if not safe_member(name) or not re.fullmatch('[0-9a-f]{64}',digest):raise ValueError('Unsafe manifest entry')
  if hashlib.sha256(z.read(prefix+name)).hexdigest()!=digest:raise ValueError('Manifest member digest mismatch: '+name)

def main():
 if not __debug__:raise RuntimeError('Verification requires Python assertions enabled')
 out=Path('/private/tmp/truss-managed-grants-049/public-source48')
 out.mkdir(exist_ok=False)
 def gh(*args):return subprocess.check_output(['gh',*args])
 api=json.loads(gh('api','repos/DocumentDrivenDX/truss/releases/tags/v0.0.48'))
 (out/'release.api.json').write_text(json.dumps(api,indent=2)+'\n')
 assert api['tag_name']=='v0.0.48' and not api['draft'] and not api['prerelease'] and api['published_at']
 tag=json.loads(gh('api','repos/DocumentDrivenDX/truss/git/ref/tags/v0.0.48'))
 (out/'tag.api.json').write_text(json.dumps(tag,indent=2)+'\n')
 assert tag['object']['type']=='commit'
 commit='8e89a068bcb68f1e631388ddc59bc97da748563d'
 assert tag['object']['sha']==commit
 assets={a['name']:a for a in api['assets']}
 assert len(assets)==len(api['assets']) and all(Path(n).name==n and n not in ('.','..') and '\\' not in n for n in assets)
 wheel='truss_toolkit-0.0.48-py3-none-any.whl'
 assert [n for n in assets if n.endswith('.whl')]==[wheel]
 selected=[wheel,'SHA256SUMS','release-pins.json','migration-qualification.json','hf-conformance-qualification.json']
 for name in selected:
  subprocess.run(['gh','release','download','v0.0.48','--repo','DocumentDrivenDX/truss','--pattern',name,'--dir',str(out)],check=True)
  assert assets[name]['digest']=='sha256:'+sha(out/name),(name,'API digest')
 sums=checksum_entries((out/'SHA256SUMS').read_text())
 assert set(sums)==set(assets)-{'SHA256SUMS'}
 for name in selected:
  if name!='SHA256SUMS':assert sha(out/name)==sums[name]
 pins=json.loads((out/'release-pins.json').read_bytes())
 assert pins['tag']=='v0.0.48' and pins['commit']==commit and pins['version']=='0.0.48' and pins['distribution']=='truss-toolkit'
 assert pins['migrationManifestSha256']=='7d165e4a344ca66d41a32b32f6bcf20f1f8fe73e4ba1137e4ca65780dcee6243'
 native='c4339ac7f09ab5a004c272ab00962107a970938004c1765ec4163e4d5ca9b6f0'
 assert pins['runtimeManifestSha256']==native
 assert pins['weftSourceRevision']=='557153731e9f5d0583193a1189a07c6ed485d3d3'
 assert pins['weftNativeModuleSha256']=='ef293922003832fbd87041a28c6dbde33927fee573270f203aa51daf06bcd445'
 assert pins['weftWheelSha256']=='a23142f12b59444138b588a8a764666b025552a14036f62d83af022153f1a0a5'
 with zipfile.ZipFile(out/wheel) as z:
  wheel_members=verify_wheel(z)
  runtime=json.loads(z.read('truss/_catalog_runtime/manifest.json'))
  verify_files(z,'truss/_catalog_runtime/',runtime)
  raw=z.read('truss/_migrations/manifest.json')
  assert hashlib.sha256(z.read('truss/_catalog_runtime/manifest.json')).hexdigest()==native
  assert hashlib.sha256(raw).hexdigest()==pins['migrationManifestSha256']
  lineage=json.loads(raw)
  assert lineage['target']==native
  assert lineage['interfaceVersion']==pins['migrationInterface'] and lineage['sources']==pins['migrationSources'] and lineage['target']==pins['migrationTarget']
  verify_files(z,'truss/_migrations/',lineage)
  (out/'published-migration-manifest.json').write_bytes(raw)
 q=json.loads((out/'migration-qualification.json').read_bytes())
 assert q['passed'] is True and q['failures']==q['errors']==q['skipped']==0 and q['sourceCommit']==commit and q['platform']=='linux'
 assert q['package']=='0.0.48' and q['tests']==80
 assert q['targetManifestSha256']==native and q['recipeSha256']==pins['migrationManifestSha256']
 hf=json.loads((out/'hf-conformance-qualification.json').read_bytes())
 assert hf['passed'] is True and hf['failures']==hf['errors']==hf['skipped']==0 and hf['sourceCommit']==commit and hf['tests']==pins['hfConformanceTests']==62
 assert hf['toolkit']=='0.0.48' and hf['compiler']=='0.4.51'
 assert hf['nativeManifestSha256']==native and hf['compilerNativeModuleSha256']==pins['weftNativeModuleSha256']
 assert hf['profile']==pins['hfConformanceProfile'] and hf['corpusSha256']==pins['hfConformanceCorpusSha256']
 assert hf['compilerSourceRevision']==pins['weftSourceRevision']
 receipt={'passed':True,'scope':__doc__,'publicRelease':api['html_url'],'tagCommit':commit,'wheel':wheel,'wheelSha256':sha(out/wheel),'nativeManifestSha256':native,'migrationManifestSha256':pins['migrationManifestSha256'],'selectedAssets':{n:sha(out/n) for n in selected},'publishedAssetCount':len(assets),'wheelRecordMembers':wheel_members,'migrationTests':q['tests'],'hfTests':hf['tests'],'producerSha256':sha(Path(__file__)),'nativeQualificationExecuted':False,'lakebaseAcceptance':'not_run'}
 (out/'verification.json').write_text(json.dumps(receipt,indent=2)+'\n')
 print(json.dumps(receipt,indent=2))

if __name__=='__main__':
 main()
