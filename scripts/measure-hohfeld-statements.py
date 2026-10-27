#!/usr/bin/env python3
# SPDX-License-Identifier: MIT OR Apache-2.0
"""Measure original Hohfeld read/write workflows; test-only SQL text, never binds."""
import sys,json,time,hashlib,importlib.metadata,tomllib
from pathlib import Path
from unittest.mock import patch
import argparse
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--consumer',type=Path,required=True)
p.add_argument('--consumer-commit',required=True)
p.add_argument('--output',type=Path,required=True)
a=p.parse_args()
assert len(a.consumer_commit)==40 and all(c in '0123456789abcdef' for c in a.consumer_commit)
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root/'scripts'))
from publish_pypi_release import distribution_for_version
project=tomllib.loads((root/'packages/python/pyproject.toml').read_text())['project']
truss_distribution=distribution_for_version(project['version'])
sys.path[:0]=[str(a.consumer/'src'),str(a.consumer/'tests')]
assert not any(__import__('shutil').which(name) for name in ('bun','node','nodejs')), 'Use Python-only deployment PATH'
import psycopg,bench_latency as b
calls=[]
original=psycopg.Cursor.execute
commit=psycopg.Connection.commit
rollback=psycopg.Connection.rollback
def execute(self,query,*args,**kw):
    text=query.as_string(self.connection) if isinstance(query,psycopg.sql.Composable) else query.decode('utf-8') if isinstance(query,bytes) else str(query)
    calls.append({'kind':'execute','sql':text})
    return original(self,query,*args,**kw)
def committed(self,*args,**kw):
    calls.append({'kind':'commit'})
    return commit(self,*args,**kw)
def rolled(self,*args,**kw):
    calls.append({'kind':'rollback'})
    return rollback(self,*args,**kw)
world=b.load_world(None,True)
results=[]
try:
    h,sources=world.hohfeld(warm=True)
    try:
        ops=b.Ops(h.session(world.principal),'release44budget')
        for label,fn in [('read-with-facts',ops.read_key),('single-object-update',ops.rename),('describe-type-enumeration',ops.describe)]:
            fn(9000)
            for i in range(3):
                calls.clear();b.METER.reset();started=time.perf_counter()
                with patch.object(psycopg.Cursor,'execute',execute),patch.object(psycopg.Connection,'commit',committed),patch.object(psycopg.Connection,'rollback',rolled):
                    value=fn(9100+i)
                results.append({'operation':label,'sample':i,'seconds':time.perf_counter()-started,'driverWaitCalls':b.METER.round_trips,'connects':b.METER.connects,'calls':list(calls)})
        ops.clean()
    finally:sources.close();h.close()
finally:world.close()
import truss
manifest=Path(truss.__file__).parent/'_catalog_runtime/manifest.json'
out={'distribution':truss_distribution,'version':importlib.metadata.version(truss_distribution),'runtimeManifestSha256':hashlib.sha256(manifest.read_bytes()).hexdigest(),'consumerCommit':a.consumer_commit,'platform':__import__('platform').platform(),'python':sys.version,'scope':'Unmodified original Hohfeld bench Ops over one warm kept person connection; setup/warmup/cleanup excluded; all driver SQL/control calls retained; server-internal work excluded','samples':results}
a.output.parent.mkdir(parents=True,exist_ok=True)
a.output.write_text(json.dumps(out,indent=2)+'\n')
for sample in results:print(sample['operation'],len(sample['calls']),sample['driverWaitCalls'],round(sample['seconds'],3))
