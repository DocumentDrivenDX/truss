#!/usr/bin/python3
import subprocess,sys,json
from pathlib import Path
args=sys.argv[1:]
r=subprocess.run(['/usr/local/bin/docker',*args],capture_output=True,timeout=60)
if args and args[0]=='run' and r.returncode==0:
 Path('/private/tmp/truss-security-main-integration/docs/helix/04-build/evidence/scalar-native-cleanup-control/02a6c6cf-d232-48a2-b759-da7886f71811/created.json').write_text(json.dumps({'id':r.stdout.decode().strip(),'cidfile':args[args.index('--cidfile')+1],'arguments':args}))
 sys.stderr.write('controlled-lost-create-f2ce6c17a1694d72a88170291c143e25'+'\n');sys.exit(1)
sys.stdout.buffer.write(r.stdout);sys.stderr.buffer.write(r.stderr);sys.exit(r.returncode)
