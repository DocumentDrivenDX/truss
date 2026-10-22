#!/bin/bash
set -euo pipefail
test "$(gh run view 39838914360 --repo DocumentDrivenDX/truss --json conclusion --jq .conclusion)" = success
test "$(gh api repos/DocumentDrivenDX/truss/actions/runs/39838914360 --jq .run_attempt)" = 1
test "$(git -C /private/tmp/truss-hf048-release rev-parse HEAD)" = 8e89a068bcb68f1e631388ddc59bc97da748563d
mkdir /private/tmp/truss-public-048-verification
mkdir /private/tmp/truss-public-048-verification/assets
gh release view v0.0.48 --repo DocumentDrivenDX/truss --json tagName,isDraft,isPrerelease,assets,url > /private/tmp/truss-public-048-verification/release-metadata.json
gh run view 39838914360 --repo DocumentDrivenDX/truss --json databaseId,headSha,status,conclusion,url,jobs > /private/tmp/truss-public-048-verification/tag-run.json
gh release download v0.0.48 --repo DocumentDrivenDX/truss --dir /private/tmp/truss-public-048-verification/assets
/private/tmp/truss-public-048-clean-venv/bin/python /private/tmp/truss-public-048-verify-assets.py \
  --assets /private/tmp/truss-public-048-verification/assets \
  --metadata /private/tmp/truss-public-048-verification/release-metadata.json \
  --artifacts /private/tmp/truss-048-tag-artifacts \
  --source 8e89a068bcb68f1e631388ddc59bc97da748563d \
  --repository /private/tmp/truss-hf048-release \
  --output /private/tmp/truss-public-048-verification/verification.json
/private/tmp/truss-public-048-clean-venv/bin/python - <<'PY'
from pathlib import Path
import hashlib,json
p=Path('/private/tmp/truss-public-048-verification')
run=json.loads((p/'tag-run.json').read_bytes())
assert run['headSha']=='8e89a068bcb68f1e631388ddc59bc97da748563d'
assert run['status']=='completed' and run['conclusion']=='success'
for name in ['package','native (ubuntu-24.04)','publish']:
    job,=[j for j in run['jobs'] if j['name']==name]
    assert job['conclusion']=='success'
native,=[j for j in run['jobs'] if j['name']=='native (ubuntu-24.04)']
for name in ['Run installed original public workload','Run exact installed compiler cohort and asset-cache unit module','Run installed disclosure source correspondence regressions']:
    step,=[s for s in native['steps'] if s['name']==name]
    assert step['conclusion']=='success'
w=Path('/private/tmp/truss-048-tag-artifacts/original-public-workflow-ubuntu-24.04')
status=json.loads((w/'status.json').read_bytes());report=json.loads((w/'report.json').read_bytes())
assert status['source']==run['headSha'] and status['outcome']=='success' and status['functionalPassed']
assert report['sourceCommit']==run['headSha'] and report['passed'] and report['functionalPassed']
assert report['runtimePackage']['mode']=='installed' and report['runtimePackage']['version']=='0.0.48'
assert report['statementTimeoutMs']==10000 and report['operationTimeoutMs']==30000
case,=report['cases'];assert case['workload']['nodes']==case['workload']['edges']==case['createdEdges']==case['loaded']==1000
s=(p/'assets/SHA256SUMS').read_bytes();pins=json.loads((p/'assets/release-pins.json').read_bytes())
base='https://github.com/DocumentDrivenDX/truss/releases/download/v0.0.48/'
handoff={'release':'https://github.com/DocumentDrivenDX/truss/releases/tag/v0.0.48','sourceCommit':run['headSha'],'tagWorkflow':run['url'],'checksumManifestUrl':base+'SHA256SUMS','checksumManifestSha256':hashlib.sha256(s).hexdigest(),'checksumManifestText':s.decode(),'releasePins':pins,'verificationPath':str(p/'verification.json'),'linuxOriginalWorkloadPassed':True,'publicMacQualification':'pending; root will run actual public package80/62, driver30 and isolated2-instance UVX checks','assetUrls':{x.name:base+x.name for x in sorted((p/'assets').iterdir()) if x.is_file()}}
(p/'handoff.json').write_text(json.dumps(handoff,indent=2)+'\n')
print(json.dumps({'publicAssetsVerified':True,'assets':len(handoff['assetUrls']),'checksumManifestSha256':handoff['checksumManifestSha256'],'sourceCommit':run['headSha'],'linuxWorkloadPassed':True}))
PY
