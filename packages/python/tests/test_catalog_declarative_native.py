"""Basic native declaration-only admission and unsupported-shape refusals."""
import base64,copy,json,os,sys,tempfile,unittest
from hashlib import sha256
from pathlib import Path
import psycopg
from truss import LocalPostgres,CatalogDocument
from truss.catalog_preparation import prepare_catalog
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'examples'))
from adopter_workflow import transaction,success


class DeclarativeCatalogNativeTests(unittest.TestCase):
    def test_native_scalar_declaration_does_not_admit_unknown_or_container_homes(self):
        content=(Path(__file__).resolve().parents[3]/'docs/helix/04-build/evidence/named-current-native-refusal-20261015/original-core.json').read_bytes()
        prepared=prepare_catalog((CatalogDocument('domain','named-query-core-r1',content),),source_version='0.8.0',bun_executable=os.environ.get('TRUSS_BUN_EXECUTABLE','bun'))
        with tempfile.TemporaryDirectory(prefix='truss-declarative-') as directory,LocalPostgres(Path(directory)/'data') as runtime:
            with psycopg.connect(runtime.info.connection_uri,autocommit=True,options='-c statement_timeout=10000') as admin:
                with transaction(admin) as (assembly,tx):success(assembly.install_in_transaction(tx))
                for mutation in (None,'unknown_scalar','orphan_container','unknown_home'):
                    with self.subTest(mutation=mutation):
                        source=json.loads(content)
                        clear=next(e for m in source['modules'] for e in m['elements'] if e['id']=='clear')
                        if mutation=='unknown_scalar':clear['scalarType']='future'
                        elif mutation=='orphan_container':
                            clear['cardinality']='array';clear['itemType']={'module':'m','element':'salary'}
                            clear.pop('scalarType');clear.pop('facets')
                        elif mutation=='unknown_home':clear['futureStorage']={'home':'unselected'}
                        raw=json.dumps(source,separators=(',',':')).encode()
                        inputs=copy.deepcopy(prepared.input());archive=json.loads(prepared.archive_documents_bytes)
                        inputs['documents'][0]['artifact']['sha256']=sha256(raw).hexdigest()
                        archive[0]['originalText']=raw.decode()
                        args=(json.dumps(inputs).encode(),json.dumps(archive).encode(),prepared.declarations_bytes)
                        if mutation is None:
                            admin.execute('SELECT truss.catalog_check_source_correspondence(%s,%s,%s)',args)
                        else:
                            with self.assertRaises(psycopg.Error) as refused:
                                admin.execute('SELECT truss.catalog_check_source_correspondence(%s,%s,%s)',args)
                            self.assertEqual(refused.exception.sqlstate,'22023')
