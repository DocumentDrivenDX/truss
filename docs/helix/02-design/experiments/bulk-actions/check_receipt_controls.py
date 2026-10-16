#!/usr/bin/env python3
"""Prove a stale/equal-count or unsafe Python receipt refuses before Java dispatch."""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
source=Path(__file__).resolve().parent
evidence=source.parents[2]/'04-build/evidence/bulk-update'
original=json.loads((evidence/'batch-model-results.json').read_text())
cases=[]
for name,expected in [('source','Python receipt source differs'),('passed','Python result not verified safe'),('safe','Python result not verified safe')]:
    altered=copy.deepcopy(original)
    if name=='source':altered['sourceSha256']='0'*64
    elif name=='passed':altered['passed']=False
    else:altered['model']['safe']=False
    with tempfile.TemporaryDirectory(prefix='truss-model-stale-') as directory:
        path=Path(directory)/'receipt.json';path.write_text(json.dumps(altered))
        result=subprocess.run([sys.executable,str(source/'check_tlc.py'),'--java','/nonexistent-java','--jar','/nonexistent-jar','--python-receipt',str(path)],capture_output=True,text=True,timeout=10)
        assert result.returncode!=0 and expected in result.stderr,(name,result.stderr)
        assert altered['model']['states']==original['model']['states']
        cases.append({'id':name,'refusedBeforeJava':True,'sameStateCount':True})
report={'scope':'Model evidence provenance controls; no native effects','passed':True,'cases':cases,'runnerSha256':hashlib.sha256((source/'check_tlc.py').read_bytes()).hexdigest(),'sourceSha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
(evidence/'model-receipt-controls.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
