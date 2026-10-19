# SPDX-License-Identifier: MIT OR Apache-2.0
"""Decoded replay frames retain live cross-module property authority."""
import psycopg
from truss import Ok,ModuleAccessGrant,adopt_psycopg_host,create_reference_assembly,CatalogRuntimeConfiguration
from truss.groups import GroupSuccess,GroupFailed,CommittedReceiptReplay
import test_group_create_native as base
class ReplayFrameTests(base.PublicCreateGroupTests):
    for _name in tuple(n for n in dir(base.PublicCreateGroupTests) if n.startswith('test_')):locals()[_name]=None
    @staticmethod
    def separate_property_module(source):
        module=source['modules'][0]
        moved=next(e for e in module['elements'] if e['id']=='A-value')
        module['elements'].remove(moved)
        for record in (e for e in module['elements'] if e['kind']=='record'):
            for reference in record['members']:
                if reference['element']=='A-value':reference['module']='fields'
            for key in record['keys']:
                for reference in key['fields']:
                    if reference['element']=='A-value':reference['module']='fields'
        source['modules'].append({'id':'fields','namespace':'fields','elements':[moved],'relationships':[],'extensions':{}})
    def test_committed_replay_rechecks_property_module_reader(self):
        connection,host,assembly,tx=self.ready(self.separate_property_module,document_ids=('adoc',))
        for role in ('field_reader','field_writer'):
            self.admin.execute(psycopg.sql.SQL('CREATE ROLE {} NOLOGIN').format(psycopg.sql.Identifier(role)))
            self.addCleanup(self.admin.execute,psycopg.sql.SQL('DROP ROLE {}').format(psycopg.sql.Identifier(role)))
        self.admin.execute('BEGIN');admin_host=adopt_psycopg_host(self.admin)
        try:
            admin_assembly=create_reference_assembly(CatalogRuntimeConfiguration(),admin_host).value
            configured=admin_assembly.configure_module_access_in_transaction(admin_host.adopt_transaction().value,
                (ModuleAccessGrant('adoc','fields','field_reader','field_writer'),))
            self.assertIsInstance(configured,Ok,repr(configured))
        finally:admin_host.detach()
        self.admin.commit();self.admin.execute('GRANT field_reader TO consumer WITH SET FALSE')
        input,request=self.input(assembly,tx)
        created=self.apply(assembly,tx,input,request);self.assertIsInstance(created,GroupSuccess)
        host.detach();connection.commit();connection,host,assembly,tx=self.consumer()
        replay=self.apply(assembly,tx,input,request);self.assertIsInstance(replay.response,CommittedReceiptReplay)
        host.detach();connection.commit();self.admin.execute('REVOKE field_reader FROM consumer')
        connection,host,assembly,tx=self.consumer()
        refused=assembly.apply_in_transaction(tx,input,request,documents=self.documents)
        self.assertIsInstance(refused,Ok,repr(refused));self.assertIsInstance(refused.value,GroupFailed,repr(refused))
        self.assertEqual(refused.value.failure.code,'unauthorized_person')
        host.detach();connection.rollback()
        self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.object').fetchone(),(1,))
