"""Public type/profile separation; deliberately no adopted host or SQL."""
import unittest,typing
from truss import CurrentDisclosureExecutor,CurrentDisclosureRows,CurrentQueryExecutor
from truss.catalog_runtime import CatalogReferenceAssembly,CatalogRuntimeConfiguration
from truss.psycopg_host import PsycopgHost
from truss.execution import Ok

class DisclosureApiTests(unittest.TestCase):
 def test_wrong_executor_profiles_refuse_before_host_use(self):
  assembly=CatalogReferenceAssembly(CatalogRuntimeConfiguration(),object.__new__(PsycopgHost))
  for executor in (object.__new__(CurrentQueryExecutor),None,{}):
   result=assembly.query_current_disclosure_in_transaction(None,executor=executor,sql='SELECT r.x FROM R r',document_ids=('d',))
   self.assertIsInstance(result,Ok);self.assertEqual(result.value.code,'invalid_query')
  result=assembly.query_current_in_transaction(None,executor=object.__new__(CurrentDisclosureExecutor),sql='SELECT r.x FROM R r',document_ids=('d',))
  self.assertIsInstance(result,Ok);self.assertEqual(result.value.code,'invalid_query')
 def test_public_v2_result_has_no_private_transport_or_scalar_rows(self):
  result=CurrentDisclosureRows(('alias',),(0,),b'{"rows":[]}',1)
  self.assertEqual(result.outcome,'disclosure')
  for private in ('transport_report','native','parent','current','rows'):
   self.assertFalse(hasattr(result,private))
  self.assertEqual(typing.get_type_hints(CatalogReferenceAssembly.query_current_disclosure_in_transaction)['executor'],CurrentDisclosureExecutor)

if __name__=='__main__':unittest.main()
