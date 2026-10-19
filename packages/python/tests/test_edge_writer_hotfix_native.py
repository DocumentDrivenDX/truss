# SPDX-License-Identifier: MIT OR Apache-2.0
"""Public edge writer closure after attempt flush."""
import psycopg
from truss.contracts import MapValue
from truss.groups import StoredObjectReference, GroupSuccess
import test_edge_mutations_native as edge_tests

class EdgeWriterHotfixTests(edge_tests.EdgeMutationTests):
    for _name in tuple(n for n in dir(edge_tests.EdgeMutationTests) if n.startswith('test_')):
        locals()[_name]=None

    def test_writer_revocation_after_attempt_flush_aborts(self):
        connection,host,assembly,tx,a,b,pin=self.initialized()
        result,_,_=self.run_group(assembly,tx,(self.link(pin,StoredObjectReference(identity=a),StoredObjectReference(identity=b)),),'pending-edge')
        self.assertIsInstance(result,GroupSuccess)
        connection.execute('SET CONSTRAINTS truss.runtime_object_attempt_commit IMMEDIATE')
        self.admin.execute('GRANT group_reader TO consumer WITH SET FALSE')
        self.admin.execute('REVOKE group_writer FROM consumer')
        host.detach()
        with self.assertRaises(psycopg.errors.InsufficientPrivilege):connection.commit()
        connection.rollback()
        self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.edge').fetchone(),(0,))
        self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.runtime_edge_transition').fetchone(),(0,))
