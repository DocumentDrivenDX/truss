#!/usr/bin/python3
import subprocess,sys,json
from pathlib import Path
args=sys.argv[1:]
r=subprocess.run(['/usr/local/bin/docker',*args],capture_output=True,timeout=60)
if args and args[0]=='run' and r.returncode==0:
 Path('/private/tmp/truss-security-main-integration/docs/helix/04-build/evidence/scalar-native-cleanup-control/4f566ee7-dbdc-4426-a479-b9d482ad150d/created.json').write_text(json.dumps({'id':r.stdout.decode().strip(),'cidfile':args[args.index('--cidfile')+1],'arguments':args}))
 sys.stderr.write('controlled-lost-create-50272c798a2e4315a20d631453920103'+'\n');sys.exit(1)
sys.stdout.buffer.write(r.stdout);sys.stderr.buffer.write(r.stderr);sys.exit(r.returncode)
