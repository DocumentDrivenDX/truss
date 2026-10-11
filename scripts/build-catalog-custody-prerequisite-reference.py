"""Compile original candidate sources in an owned independent PostgreSQL17 DB.

Administrative candidate evidence only. No target connection is accepted. Frozen
source bytes define the reference; target observations never define expected data.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import shutil
import subprocess
import tempfile
from pathlib import Path
import psycopg


def sha(raw):return hashlib.sha256(raw).hexdigest()

def bounded_read(path,limit):
    with path.open('rb') as stream:raw=stream.read(limit+1)
    if not 1<=len(raw)<=limit:raise ValueError('Original file capacity')
    return raw

def unique_object(pairs):
    result={}
    for key,value in pairs:
        if key in result:raise ValueError('Duplicate original selection key')
        result[key]=value
    return result


def freeze(entries, *, count, total_limit):
    if type(entries) is not list or not count[0]<=len(entries)<=count[1]:
        raise ValueError('Selected roster capacity')
    seen=set(); frozen=[]; total=0
    for entry in entries:
        if type(entry) is not dict or set(entry)!={'path','file'}:
            raise ValueError('Closed original source selection required')
        path=entry['path'];file=entry['file']
        if type(path) is not str or not path or len(path.encode())>4096 or path in seen:
            raise ValueError('Unique bounded source identity required')
        if type(file) is not str:raise ValueError('Original file path required')
        source=Path(file)
        raw=bounded_read(source,4194304)
        total+=len(raw)
        if total>total_limit:raise ValueError('Aggregate source capacity')
        frozen.append((path,raw));seen.add(path)
    return frozen


def compile_reference(selection,postgres_bin,output):
    raw_selection=bounded_read(selection,1048576)
    roster=json.loads(raw_selection,object_pairs_hook=unique_object)
    if type(roster) is not dict or set(roster)!={'sources','resources'}:
        raise ValueError('Closed reference selection required')
    sources=freeze(roster['sources'],count=(1,128),total_limit=16777216)
    resources=freeze(roster['resources'],count=(71,71),total_limit=16777216)
    compiled=dict(sources)
    if any(identity in compiled and raw!=compiled[identity] for identity,raw in resources):
        raise ValueError('Compiled and archived originals differ for the same source identity')
    # Freeze all originals before starting the independent native compiler.
    output.mkdir(parents=True,exist_ok=False)
    for family,items in [('sources',sources),('resources',resources)]:
        folder=output/family;folder.mkdir()
        for ordinal,(identity,raw) in enumerate(items):
            (folder/f'{ordinal:03}.original').write_bytes(raw)
    (output/'selection.original.json').write_bytes(raw_selection)
    root=Path(tempfile.mkdtemp(prefix='truss-custody-reference-',dir='/private/tmp'))
    data=root/'data';socket=root/'socket';socket.mkdir();started=False
    receipt={'scope':'owned independent administrative reference compilation','stop':None,'status':None}
    def run(name,*args):
        return subprocess.run([str(postgres_bin/name),*args],check=True,capture_output=True,text=True,timeout=60)
    try:
        version=run('postgres','--version').stdout.strip()
        if version!='postgres (PostgreSQL) 17.11':raise ValueError('Exact PostgreSQL17.11 compiler required')
        run('initdb','-D',str(data),'-U','postgres','--auth=trust','--encoding=UTF8')
        started=True
        run('pg_ctl','-D',str(data),'-l',str(root/'server.log'),'-w','-o',f"-h '' -k {socket}",'start')
        with psycopg.connect(host=str(socket),user='postgres',dbname='postgres',autocommit=True,options='-c statement_timeout=10000') as connection:
            if connection.info.server_version!=170011:raise ValueError('Exact native version required')
            for identity,raw in sources:
                connection.execute(raw.decode('utf8'),prepare=False)
            connection.execute('BEGIN')
            routines=connection.execute('SELECT truss.runtime_collect_catalog_custody_declarations_candidate()::text',prepare=False).fetchone()[0]
            schema=connection.execute('SELECT truss.runtime_collect_catalog_custody_schema_candidate()::text',prepare=False).fetchone()[0]
            manifest={'interfaceVersion':'truss-catalog-custody-prerequisite-independent-reference/0.1-candidate',
                'scope':'administrative_rollback_only_catalog_custody','nativeVersion':'170011',
                'sourceFiles':[{'path':p,'sha256':sha(b)} for p,b in sources],
                'resources':[{'path':p,'sha256':sha(b)} for p,b in resources],
                'routines':json.loads(routines),'custodySchema':json.loads(schema)}
            original=(json.dumps(manifest,ensure_ascii=False,separators=(',',':'))+'\n').encode('utf8')
            if len(original)>4194304 or len(original)+sum(len(b) for _,b in resources)>16777216:
                raise ValueError('Reference/adjunct aggregate capacity')
            connection.rollback()
        receipt.update(nativeVersion='170011',referenceSha256=sha(original),routineCount=len(manifest['routines']),referenceBytes=len(original),adjunctBytes=sum(len(b) for _,b in resources),sourceCount=len(sources))
    finally:
        if started:
            for name,command in [('stop',['-w','-m','immediate','stop']),('status',['status'])]:
                try:
                    observed=subprocess.run([str(postgres_bin/'pg_ctl'),'-D',str(data),*command],capture_output=True,text=True,timeout=30 if name=='stop' else 10)
                    receipt[name]=observed.returncode
                except Exception as error:
                    receipt[name+'Error']=type(error).__name__+': '+str(error)
            receipt['socketAbsent']=not(socket/'.s.PGSQL.5432').exists()
            confirmed=receipt['stop']==0 and receipt['status']==3 and receipt['socketAbsent']
        else:confirmed=True
        log=root/'server.log'
        if log.exists():(output/'server.log').write_bytes(log.read_bytes())
        receipt['cleanupConfirmed']=confirmed
        receipt['retainedFixture']=None if confirmed else str(root)
        (output/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
        if confirmed:shutil.rmtree(root)
        else:raise RuntimeError('Reference fixture shutdown unconfirmed; retained '+str(root))
    (output/'reference.original.json').write_bytes(original)
    return receipt

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--selection',type=Path,required=True)
    parser.add_argument('--postgres-bin',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    print(json.dumps(compile_reference(args.selection,args.postgres_bin,args.output)))
