"""Review immutable published Weft source/artifact bytes, not native execution."""
import gzip,hashlib,json,subprocess
from pathlib import Path
WEFT=Path('/Users/erik/Projects/weft')
HERE=Path(__file__).resolve().parent
COMMIT='3a2a79c'
BASE='docs/helix/04-build/evidence/paths-keys-source-review-20261010/'
def git(*args):return subprocess.check_output(['git',*args],cwd=WEFT)
commit=git('rev-parse',COMMIT).decode().strip()
def raw(path):return git('show',commit+':'+path)
def sha(value):return hashlib.sha256(value).hexdigest()
def artifact(name):
    try:return raw(BASE+name)
    except subprocess.CalledProcessError:return gzip.decompress(raw(BASE+name+'.gz'))
review=json.loads(raw(BASE+'astra-review.json'));results=json.loads(raw(BASE+'results.json'))
source=[]
for item in review['reviewedFiles']:
    value=raw(item['path'])
    if sha(value)!=item['sha256'] or len(value)!=item['bytes']:raise ValueError('Reviewed source drift: '+item['path'])
    source.append(item)
cases=[]
for item in results['cases']:
    request=artifact(item['name']+'.request.json');response=artifact(item['name']+'.response.json')
    if sha(request)!=item['requestSha256'] or sha(response)!=item['responseSha256'] or len(response)!=item['responseBytes']:raise ValueError('Original case drift: '+item['name'])
    actual=json.loads(response)
    if (actual['status']=='compiled')!=item['compiled']:raise ValueError('Original status drift')
    cases.append({'case':item['name'],'compiled':item['compiled'],'requestSha256':sha(request),'responseSha256':sha(response),'detail':item['detail']})
receipt={'scope':'Immutable committed Weft Paths-Keys source and retained compiler artifact review; no rerun/native support/adoption', 'weftCommit':commit,'umfOriginMain':subprocess.check_output(['git','rev-parse','origin/main'],cwd='/Users/erik/Projects/umf').decode().strip(),'sourceFiles':source,'sourceReviewSha256':sha(raw(BASE+'astra-review.json')),'ownerVerdict':review['verdict'],'cases':cases,'compiledCount':sum(c['compiled'] for c in cases),'refusedCount':sum(not c['compiled'] for c in cases),'producerSha256':sha(Path(__file__).read_bytes()),'trussCompilerAdopted':False,'nativeQualification':False,'limitations':review['limitations']}
out=HERE/'weft-paths-keys-implementation-review.json'
with out.open('x') as f:f.write(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({'sourceFiles':len(source),'cases':len(cases),'compiled':receipt['compiledCount'],'refused':receipt['refusedCount'],'adopted':False}))
