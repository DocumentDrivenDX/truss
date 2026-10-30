import json,os,subprocess,sys,time
from pathlib import Path
name,seconds,*command=sys.argv[1:]
root=Path('/out');started=time.monotonic();status=125
with (root/(name+'.stdout')).open('wb')as stdout,(root/(name+'.stderr')).open('wb')as stderr:
 try:
  child=subprocess.run(command,stdout=stdout,stderr=stderr,timeout=float(seconds))
  status=child.returncode
 except subprocess.TimeoutExpired:status=124
record={'stage':name,'command':command,'elapsedSeconds':time.monotonic()-started,'exitCode':status}
(root/(name+'.result.json')).write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps(record),flush=True)
if status:
 print((root/(name+'.stderr')).read_text(errors='replace')[-6000:],flush=True)
raise SystemExit(status)
