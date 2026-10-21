#!/usr/bin/env python3
"""Unauthenticated public downloads followed by exact source/archive/pin checks."""
import argparse,hashlib,importlib.util,json,re,subprocess,sys,time,urllib.request
from pathlib import Path
sys.dont_write_bytecode=True
p=argparse.ArgumentParser();p.add_argument('--repo',type=Path,required=True);p.add_argument('--tag',required=True);p.add_argument('--commit',required=True);p.add_argument('--download',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
helper=Path(__file__).with_name('verify-release-integrity.py')
spec=importlib.util.spec_from_file_location('release_integrity',helper);v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
assert a.tag=='v'+v.VERSION and re.fullmatch('[0-9a-f]{40}',a.commit)
def get(url):
 for attempt in range(4):
  try:
   # Deliberately no authorization, cookies, token, netrc or authenticated session.
   with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Truss-public-artifact-verifier'}),timeout=60) as response:return response.read()
  except Exception:
   if attempt==3:raise
   time.sleep(2)
tag=v.read_json(get('https://api.github.com/repos/DocumentDrivenDX/truss/git/ref/tags/'+a.tag))['object']
for _ in range(8):
 if tag['type']=='commit':break
 assert tag['type']=='tag' and re.fullmatch('[0-9a-f]{40}',tag['sha'])
 tag=v.read_json(get('https://api.github.com/repos/DocumentDrivenDX/truss/git/tags/'+tag['sha']))['object']
assert tag['type']=='commit' and tag['sha']==a.commit
meta=v.read_json(get('https://api.github.com/repos/DocumentDrivenDX/truss/releases/tags/'+a.tag))
assert not meta['draft'] and not meta['prerelease'] and meta['tag_name']==a.tag
expected={f'truss_toolkit-{v.VERSION}-py3-none-any.whl',f'truss_toolkit-{v.VERSION}.tar.gz','release-pins.json','SHA256SUMS','logical-query-abi.json','catalog-registration-summary-v0.1.md','catalog-rebind-report-v0.2.md','catalog-rebind-report-v0.4.md','catalog-source-reference-v0.1.md','catalog-key-backfill-report-v0.1.md'}
names=[x['name'] for x in meta['assets']]
assert len(names)==len(set(names)) and set(names)==expected
assert all(v.safe(n) and Path(n).name==n and chr(0) not in n for n in names)
a.download.mkdir(parents=True,exist_ok=False)
for asset in meta['assets']:
 url=asset['browser_download_url'];assert url.startswith('https://github.com/DocumentDrivenDX/truss/releases/download/'+a.tag+'/')
 data=get(url);assert len(data)==asset['size'],asset['name']
 (a.download/asset['name']).write_bytes(data)
checked=v.verify(argparse.Namespace(repo=a.repo,delivery_dir=a.download,qualified_ref=a.commit,expected_commit=a.commit))
checked.update(checkedAssets={line.split('  ',1)[1]:line.split('  ',1)[0] for line in (a.download/'SHA256SUMS').read_text().splitlines()},checksumManifestSha256=hashlib.sha256((a.download/'SHA256SUMS').read_bytes()).hexdigest(),passed=True,publicRemoteTagCommit=tag['sha'],release=meta['html_url'],publishedAt=meta['published_at'],assetCount=len(names),downloadAuthorization='none; public API and direct public HTTPS assets',verifierSha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),integrityVerifierSha256=hashlib.sha256(helper.read_bytes()).hexdigest())
a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(checked,indent=2)+'\n');print(json.dumps(checked,indent=2))
