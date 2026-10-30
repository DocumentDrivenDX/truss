#!/bin/bash
set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1 PIP_DISABLE_PIP_VERSION_CHECK=1 PIP_NO_INPUT=1
export CARGO_BUILD_JOBS=1 RAYON_NUM_THREADS=1 TOKIO_WORKER_THREADS=1
export HOME=/tmp/truss-home
mkdir -p "$HOME" /tmp/work /out/native /out/artifacts /out/originals
cp -a /source/. /tmp/work/
cp -a /generator-original /tmp/generator
cd /tmp/work
python3 -m venv /tmp/testenv
export PATH=/tmp/testenv/bin:$PATH
stage(){ python /control/stage.py "$@"; }
python - <<'PY'
import json,platform,sys,subprocess
from pathlib import Path
Path('/out/toolchain.json').write_text(json.dumps({'platform':platform.platform(),'machine':platform.machine(),'python':sys.version,'bun':subprocess.check_output(['bun','--version'],text=True).strip(),'execution':'Local Linux amd64 emulation on ARM OrbStack; no macOS runtime proof'},indent=2)+'\n')
PY
stage build-tools 90 python -m pip install --only-binary=:all: --index-url https://pypi.org/simple build==1.3.0 'setuptools>=77' wheel
stage build-package 90 python -m build --no-isolation --outdir /out/artifacts packages/python
stage public-extras-install 150 python -m pip install --only-binary=:all: --index-url https://pypi.org/simple --report /out/public-install-report.json '/out/artifacts/umf_truss-0.0.52-py3-none-any.whl[native,query,typed-sdk]' pydantic==2.13.5
stage retain-original-dependencies 90 python -m pip download --only-binary=:all: --no-deps --index-url https://pypi.org/simple --dest /out/originals umf-access==0.1.0.dev8 weft-sql==0.4.51
stage pip-check 30 python -m pip check
stage original-generator-dependencies 60 bun install --cwd /tmp/generator
digest=$(python -c 'import json;print(json.load(open("/out/operation-inputs.json"))["generatorSourceSha256"])')
stage generate-current-models 90 bun scripts/generate-typed-sdk-consumer-fixture.ts /tmp/generator scripts/fixtures/typed-sdk-core010 /out/generated "$digest"
stage verify-installed-payload-and-generated-shape 60 python /control/check-inputs.py
stage local-runtime-install 150 python scripts/install-local-runtime.py --wheelhouse /out/pg-wheels --truss-wheel /out/artifacts/umf_truss-0.0.52-py3-none-any.whl
pgbin=$(python -c 'import importlib.resources;print(importlib.resources.files("pgserver")/"pginstall/bin")')
cp -a /out/generated /out/generated-related
chown -R nobody:nogroup /out/native /out/generated /out/generated-related
wheelsha=$(sha256sum /out/artifacts/umf_truss-0.0.52-py3-none-any.whl | cut -d' ' -f1)
sdk=/out/originals/umf_access-0.1.0.dev8-py3-none-any.whl
weft=$(find /out/originals -maxdepth 1 -name 'weft_sql-*.whl' -print -quit)
common=(--sdk-wheel "$sdk" --sdk-wheel-sha256 1a21c1ddd59f6b23e9f0b33228280564af0e96bb4d13699b89616d5143e4fd23 --weft-wheel "$weft" --weft-wheel-sha256 a23142f12b59444138b588a8a764666b025552a14036f62d83af022153f1a0a5 --consumer-wheel /out/artifacts/umf_truss-0.0.52-py3-none-any.whl --consumer-wheel-sha256 "$wheelsha" --require-consumer --pg-bin "$pgbin")
stage typed-native-basic 180 runuser -u nobody -- /tmp/testenv/bin/python -B scripts/check-typed-sdk-native.py --streams-basic --output /out/native/basic --model-request /out/generated/model-request.json --generated /out/generated --bun-executable /usr/local/bun/bin/bun "${common[@]}"
stage typed-native-related 180 runuser -u nobody -- /tmp/testenv/bin/python -B scripts/check-typed-sdk-related-native.py --output /out/native/related --model scripts/fixtures/typed-sdk-core010/model.json --generated /out/generated-related --bun-executable /usr/local/bun/bin/bun "${common[@]}"
stage typed-binary-stream-controls 60 python -B -m unittest scripts.test_typed_sdk_binary scripts.test_typed_sdk_stream_limits
python - <<'PY'
import json,platform,sys
from pathlib import Path
root=Path('/out')
records=[json.loads(p.read_bytes())for p in root.glob('*.result.json')]
assert records and all(r['exitCode']==0 for r in records)
assert not list((root/'native').rglob('postmaster.pid'))
(root/'qualification.json').write_text(json.dumps({'status':'PASS_AFFECTED_TYPED_CONSUMER_GATES','source':json.loads((root/'operation-inputs.json').read_bytes()),'platform':platform.platform(),'python':sys.version,'stages':records,'ownedPostgresStopped':True,'limits':'Affected typed SDK behavior only; full migration/HF/managed/installed release gates remain separate'},indent=2)+'\n')
PY
