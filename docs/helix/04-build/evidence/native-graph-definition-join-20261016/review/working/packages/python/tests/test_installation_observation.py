"""Public footprint inspection: no installed or readiness claim."""
import unittest
from test_native_pg8000 import NativeBoundaryFixture
from truss import connect_pg8000_host,inspect_installation,Ok,Error
from truss.host import HostConnection

class InstallationObservationTests(unittest.TestCase):
    def test_invalid_connection_does_not_invoke_raw_port(self):
        class Raw:
            def run(self,*args):raise AssertionError('raw port invoked')
        self.assertIsInstance(inspect_installation(Raw()),Error)
    def test_malformed_or_inconsistent_response_is_not_absence(self):
        class Boundary:
            def __init__(self,response):self.response=response
            def run(self,sql,**parameters):return self.response
        for result in ([],[['false']],[[False]+[None]*6],[['false','r']+[None]*5],
                       [['true','unsupported']+[None]*5]):
            with self.subTest(result=result):
                self.assertIsInstance(inspect_installation(HostConnection(Boundary(result),None)),Error)

class NativeInstallationObservationTests(NativeBoundaryFixture,unittest.TestCase):
    def setUp(self):
        self.host=connect_pg8000_host(user='postgres',database='postgres',unix_sock=self.kwargs['unix_sock'])
    def tearDown(self):
        self.host.close()
    def test_absent_namespace_and_transaction_preservation(self):
        h=self.host;s=h.session
        self.assertIsInstance(s.observe_host_resource_baseline(),Ok)
        self.assertIsInstance(s.begin(),Ok)
        h.connection.run_non_lifecycle('CREATE TEMP TABLE installation_host_work(value text)')
        h.connection.run_non_lifecycle("INSERT INTO installation_host_work VALUES('preserve')")
        observation=inspect_installation(h.connection).value
        self.assertFalse(observation.namespace_present)
        self.assertEqual(observation.readiness,'unverified')
        self.assertTrue(all(r.kind is None for r in observation.relations))
        self.assertIsInstance(s.adopt_transaction(),Ok)
        self.assertEqual(h.connection.run_non_lifecycle('SELECT value FROM installation_host_work'),[['preserve']])
        self.assertEqual(s.rollback().value.state,'rolled_back')
    def test_present_namespace_and_hostile_relation_body_are_only_observed(self):
        h=self.host;s=h.session
        s.observe_host_resource_baseline();s.begin()
        h.connection.run_non_lifecycle('CREATE SCHEMA truss')
        h.connection.run_non_lifecycle("CREATE VIEW truss.schema_head AS SELECT 1/0 AS rev")
        h.connection.run_non_lifecycle('CREATE ROLE truss_footprint_metadata')
        h.connection.run_non_lifecycle('SET LOCAL ROLE truss_footprint_metadata')
        h.connection.run_non_lifecycle('SET LOCAL search_path=truss,pg_catalog')
        observation=inspect_installation(h.connection).value
        self.assertTrue(observation.namespace_present)
        self.assertEqual(observation.relations[0].kind,'v')
        self.assertEqual(observation.readiness,'unverified')
        self.assertEqual(s.rollback().value.state,'rolled_back')
    def test_failed_transaction_preserves_native_failure_for_host_rollback(self):
        from pg8000.exceptions import DatabaseError
        h=self.host;s=h.session
        s.observe_host_resource_baseline();s.begin()
        with self.assertRaises(DatabaseError):
            h.connection.run_non_lifecycle('SELECT 1/0')
        with self.assertRaises(DatabaseError) as raised:
            inspect_installation(h.connection)
        self.assertEqual(raised.exception.args[0]['C'],'25P02')
        self.assertEqual(s.rollback().value.state,'rolled_back')
    def test_unrelated_namespace_contents_do_not_imply_installation(self):
        h=self.host;s=h.session
        s.observe_host_resource_baseline();s.begin()
        h.connection.run_non_lifecycle('CREATE SCHEMA truss')
        h.connection.run_non_lifecycle('CREATE TABLE truss.unrelated(value text)')
        observation=inspect_installation(h.connection).value
        self.assertTrue(observation.namespace_present)
        self.assertTrue(all(r.kind is None for r in observation.relations))
        self.assertEqual(observation.readiness,'unverified')
        self.assertEqual(s.rollback().value.state,'rolled_back')
    def test_catalog_permission_denial_is_not_namespace_absence(self):
        from pg8000.exceptions import DatabaseError
        h=self.host;s=h.session
        s.observe_host_resource_baseline();s.begin()
        h.connection.run_non_lifecycle('CREATE ROLE truss_footprint_denied')
        h.connection.run_non_lifecycle('REVOKE SELECT ON pg_catalog.pg_class FROM PUBLIC')
        h.connection.run_non_lifecycle('SET LOCAL ROLE truss_footprint_denied')
        with self.assertRaises(DatabaseError) as raised:
            inspect_installation(h.connection)
        self.assertEqual(raised.exception.args[0]['C'],'42501')
        self.assertEqual(s.rollback().value.state,'rolled_back')
