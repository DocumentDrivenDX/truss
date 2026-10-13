#!/bin/sh
set -eu
docker run --rm -i --mount type=bind,src=/private/tmp/truss-security-main-integration,dst=/app/truss,readonly --mount type=bind,src=/Users/erik/.codex/worktrees/security-main-integration/umf,dst=/Users/erik/.codex/worktrees/security-main-integration/umf,readonly --workdir /app/truss --env PYTHONDONTWRITEBYTECODE=1 --env PYTHONPATH=/app/weft-native:/app/truss/packages/python/src:/app/truss/packages/python/tests:/app/truss/scripts --env TRUSS_SECURITY_MAPPING_WEFT_MODULE_DIR=/app/weft-native truss-security-linux-composition:source-6fc0a27 python - <<'PY'
import os,pathlib,shutil,sys
with open('/etc/passwd','a') as f:f.write('security-test:x:1000:1000:Security test:/tmp:/bin/sh\n')
with open('/etc/group','a') as f:f.write('security-test:x:1000:\n')
for target in ['/app/weft-native','/private/tmp/subject-consumer-python','/private/tmp']:
 pathlib.Path(target).mkdir(parents=True,exist_ok=True)
 os.chmod(target,0o777)
source=next(pathlib.Path('/usr/local/lib/python3.11/site-packages/weft').glob('*.so'))
for target in ['/app/weft-native/weft.so','/private/tmp/subject-consumer-python/weft.so']:shutil.copyfile(source,target)
os.setgid(1000);os.setuid(1000)
os.environ['HOME']='/tmp';os.environ['XDG_RUNTIME_DIR']='/tmp/runtime-1000'
os.execv(sys.executable,[sys.executable,'-m','unittest','test_security_catalog_channel_native','-v'])
PY
