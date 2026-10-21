# SPDX-License-Identifier: MIT OR Apache-2.0
"""Original indexed grant errors leave the complete accepted batch unchanged."""
from truss import (Ok, ModuleAccessGrant, ModuleAccessBatchRefused, CatalogRuntimeConfiguration,
    adopt_psycopg_host, create_reference_assembly)
import test_group_create_native as base


class ModuleAccessBatchNativeTests(base.PublicCreateGroupTests):
    for _name in tuple(n for n in dir(base.PublicCreateGroupTests) if n.startswith('test_')):
        locals()[_name]=None

    def test_invalid_batch_reports_all_original_indexes_without_partial_grants(self):
        c,h,a,t=self.ready();h.detach();c.rollback()
        before=self.admin.execute('SELECT document_id,module,reader_role,writer_role FROM truss.module_access ORDER BY 1,2').fetchall()
        self.admin.execute('BEGIN');host=adopt_psycopg_host(self.admin,statement_timeout_ms=10000,operation_timeout_ms=30000)
        self.addCleanup(host.detach);tx=host.adopt_transaction().value
        assembly=create_reference_assembly(CatalogRuntimeConfiguration(),host).value
        good=ModuleAccessGrant('zdoc','m','group_reader','group_writer')
        grants=(good,ModuleAccessGrant('adoc','missing','group_reader','group_writer'),
            ModuleAccessGrant('adoc','m','missing-role','consumer'))
        result=assembly.configure_module_access_in_transaction(tx,grants)
        self.assertIsInstance(result,Ok,repr(result));self.assertIsInstance(result.value,ModuleAccessBatchRefused)
        self.assertEqual([(e.index,e.code) for e in result.value.errors],[(1,'unknown_module'),(2,'unknown_role'),(2,'unsafe_role')])
        self.assertEqual(self.admin.execute('SELECT document_id,module,reader_role,writer_role FROM truss.module_access ORDER BY 1,2').fetchall(),before)
        duplicates=assembly.configure_module_access_in_transaction(tx,(good,good))
        self.assertEqual([(e.index,e.code) for e in duplicates.value.errors],[(0,'duplicate_selection'),(1,'duplicate_selection')])
        valid=assembly.configure_module_access_in_transaction(tx,(ModuleAccessGrant('adoc','m','group_reader','group_writer'),good))
        self.assertIsInstance(valid,Ok,repr(valid))
        self.assertEqual(valid.value.grants,(ModuleAccessGrant('adoc','m','group_reader','group_writer'),good))
        host.detach();self.admin.commit()
        rows=self.admin.execute("SELECT document_id FROM truss.module_access WHERE reader_role='group_reader' ORDER BY document_id").fetchall()
        self.assertEqual(rows,[('adoc',),('zdoc',)])
