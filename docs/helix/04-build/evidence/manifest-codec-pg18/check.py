"""Rollback-only PG18 codec controls; no accepted catalog or finalization claim."""
import base64,copy,hashlib,json,os,tempfile,unittest,shutil
from unittest.mock import Mock
from pathlib import Path
import psycopg
from psycopg.types.json import Jsonb
from truss import LocalPostgres
ROOT=Path(__file__).resolve().parents[5]
DRAFT=ROOT/'packages/postgresql/native/catalog-finalization'

def tagged(value):
    if value is None:return {'kind':'null'}
    if type(value) is str:return {'kind':'string','utf8Hex':value.encode().hex()}
    if type(value) is bool:return {'kind':'boolean','value':value}
    if type(value) is list:return {'kind':'array','items':[tagged(v) for v in value]}
    if type(value) is dict:return {'kind':'object','members':[{'keyUtf8Hex':k.encode().hex(),'node':tagged(v)} for k,v in value.items()]}
    raise TypeError('numeric-free expected tree')

def manifest(docs,cfg):
    return {'prerequisites':[{'artifact':{'bytesBase64':base64.b64encode(d).decode()}} for d in docs],
            'configurationPrerequisites':[{'artifact':{'bytesBase64':base64.b64encode(cfg).decode()}}]}

def cleanup_owned(directory,runtime,connection):
    try:
        if connection is not None:connection.close()
    finally:
        runtime.close()
    if (directory/'data/postmaster.pid').exists():raise AssertionError('server retained')
    shutil.rmtree(directory)

class Cleanup(unittest.TestCase):
    def test_unconfirmed_stop_preserves_owned_directory(self):
        directory=Path(tempfile.mkdtemp(prefix='truss-codec-cleanup-control-'))
        try:
            (directory/'data').mkdir();(directory/'data/postmaster.pid').write_text('test marker')
            runtime=Mock();runtime.close.side_effect=RuntimeError('unconfirmed stop')
            with self.assertRaisesRegex(RuntimeError,'unconfirmed stop'):cleanup_owned(directory,runtime,None)
            self.assertTrue((directory/'data/postmaster.pid').exists())
            runtime.close.side_effect=None
            with self.assertRaisesRegex(AssertionError,'server retained'):cleanup_owned(directory,runtime,None)
            self.assertTrue(directory.exists())
        finally:shutil.rmtree(directory)

class Codec(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.directory=Path(tempfile.mkdtemp(prefix='truss-manifest-pg18-'))
        cls.runtime=LocalPostgres(cls.directory/'data');cls.conn=None
        cls.addClassCleanup(lambda:cleanup_owned(cls.directory,cls.runtime,cls.conn))
        cls.runtime.__enter__()
        cls.conn=psycopg.connect(cls.runtime.info.connection_uri)
        cls.conn.execute("SET statement_timeout='30s'");cls.conn.execute('CREATE SCHEMA truss')
        cls.conn.execute((ROOT/'packages/postgresql/native/canonical-string-bytes.sql').read_text())
        cls.conn.execute((DRAFT/'manifest-encoder.owner-export.sql').read_text())
        cls.version=cls.conn.execute('SHOW server_version_num').fetchone()[0]
        if cls.version!='180006':raise AssertionError(cls.version)
    @classmethod
    def tearDownClass(cls):
        cls.conn.rollback()
    def encode(self,value,docs,cfg):
        return bytes(self.conn.execute('SELECT truss.runtime_manifest_artifact_tree_bytes_candidate(%s,%s,%s)',(Jsonb(tagged(value)),docs,cfg)).fetchone()[0])
    def refuses(self,value,docs,cfg,state):
        self.conn.execute('SAVEPOINT codec_case')
        try:
            with self.assertRaises(psycopg.Error) as caught:self.encode(value,docs,cfg)
            self.assertEqual(caught.exception.sqlstate,state)
        finally:
            self.conn.execute('ROLLBACK TO SAVEPOINT codec_case');self.conn.execute('RELEASE SAVEPOINT codec_case')
    def test_wide_originals_exact_independent_bytes(self):
        docs=[b'z'*70000,b'a'*70001];cfg=b'configuration'*6000
        value=manifest(docs,cfg);value['note']='nul\0 quote" slash\\ unicode é'
        expected=json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
        self.assertEqual(self.encode(value,docs,cfg),expected)
    def test_wrong_bytes_and_original_order(self):
        docs=[b'z',b'a'];cfg=b'cfg';value=manifest(docs,cfg)
        self.refuses(value,list(reversed(docs)),cfg,'55000')
        self.refuses(value,docs,b'changed','55000')
    def test_missing_extra_and_null_slots(self):
        docs=[b'doc'];cfg=b'cfg'
        for key in ['prerequisites','configurationPrerequisites']:
            for slots in [[],[None],[{'artifact':{'bytesBase64':'ZG9j'}},None]]:
                value=manifest(docs,cfg);value[key]=slots
                self.refuses(value,docs,cfg,'55000' if len(slots)!=1 else '22023')
        value=manifest(docs,cfg);del value['configurationPrerequisites']
        self.refuses(value,docs,cfg,'55000')
    def test_ordinary_and_lookalike_scalars_keep_limits(self):
        docs=[b'd'];cfg=b'c'
        for key in ['note','lookalike']:
            value=manifest(docs,cfg);value[key]=('x'*65537 if key=='note' else {'artifact':{'bytesBase64':'x'*65537}})
            self.refuses(value,docs,cfg,'54000')
        value=manifest(docs,cfg);value['note']='x'*65536
        self.assertEqual(len(json.loads(self.encode(value,docs,cfg))['note']),65536)
    def test_original_document_inclusive_and_one_over(self):
        docs=[b'x'*1048576];cfg=b'c';value=manifest(docs,cfg)
        self.assertEqual(self.encode(value,docs,cfg),json.dumps(value,sort_keys=True,separators=(',',':')).encode())
        docs=[b'x'*1048577];self.refuses(manifest(docs,cfg),docs,cfg,'54000')
        docs=[b'x'*524289,b'y'*524288];self.refuses(manifest(docs,cfg),docs,cfg,'54000')
    def test_document_count_inclusive_and_one_over(self):
        docs=[b'd']*512;cfg=b'c';value=manifest(docs,cfg)
        self.assertEqual(self.encode(value,docs,cfg),json.dumps(value,sort_keys=True,separators=(',',':')).encode())
        docs.append(b'd');self.refuses(manifest(docs,cfg),docs,cfg,'54000')
    def test_duplicate_key_and_malformed_native_tree(self):
        docs=[b'd'];cfg=b'c'
        trees=[]
        tree=tagged(manifest(docs,cfg));tree['members'].append(copy.deepcopy(tree['members'][0]));trees.append((tree,'22023'))
        tree=tagged(manifest(docs,cfg));tree['members'].append({'keyUtf8Hex':'ff','node':tagged('x')});trees.append((tree,'22021'))
        tree=tagged(manifest(docs,cfg));tree['members'].append({'keyUtf8Hex':'6e6f7465','node':{'kind':'string','utf8Hex':'ff'}});trees.append((tree,'22021'))
        tree=tagged(manifest(docs,cfg));tree['members'].append({'keyUtf8Hex':'6e6f7465','node':{'kind':'number','value':'1'}});trees.append((tree,'22023'))
        for tree,state in trees:
            self.conn.execute('SAVEPOINT malformed')
            try:
                with self.assertRaises(psycopg.Error) as caught:
                    self.conn.execute('SELECT truss.runtime_manifest_artifact_tree_bytes_candidate(%s,%s,%s)',(Jsonb(tree),docs,cfg))
                self.assertEqual(caught.exception.sqlstate,state)
            finally:
                self.conn.execute('ROLLBACK TO SAVEPOINT malformed');self.conn.execute('RELEASE SAVEPOINT malformed')
    def test_configuration_inclusive_and_one_over(self):
        docs=[b'd'];cfg=b'x'*4194304;value=manifest(docs,cfg)
        self.assertEqual(self.encode(value,docs,cfg),json.dumps(value,sort_keys=True,separators=(',',':')).encode())
        cfg=b'x'*4194305;self.refuses(manifest(docs,cfg),docs,cfg,'54000')

if __name__=='__main__':unittest.main(verbosity=2)
