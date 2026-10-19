# SPDX-License-Identifier: MIT OR Apache-2.0
"""Owner-private native tuple binding only; no authority/anchor/permit claim."""
from importlib.resources import files
import psycopg
import time
from psycopg import sql
import test_group_create_native as base


class PreparationPermitBindingNativeTests(base.PublicCreateGroupTests):
    for name in tuple(n for n in dir(base.PublicCreateGroupTests) if n.startswith('test_')):
        locals()[name] = None

    def test_private_one_tuple_full_xid_codec_and_transaction_lifetime(self):
        data, host, assembly, tx = self.ready(document_ids=('adoc',))
        host.detach(); data.commit()
        names = ('pg_advisory_lock','pg_advisory_lock_shared','pg_try_advisory_lock',
            'pg_try_advisory_lock_shared','pg_advisory_xact_lock','pg_advisory_xact_lock_shared',
            'pg_try_advisory_xact_lock','pg_try_advisory_xact_lock_shared')
        for name in names:
            self.admin.execute(sql.SQL('REVOKE ALL ON FUNCTION pg_catalog.{}(int4,int4) FROM PUBLIC').format(sql.Identifier(name)))
        owner = self.installation.owner_role
        for name in ('pg_try_advisory_xact_lock','pg_try_advisory_xact_lock_shared'):
            self.admin.execute(sql.SQL('GRANT EXECUTE ON FUNCTION pg_catalog.{}(int4,int4) TO {}').format(sql.Identifier(name),sql.Identifier(owner)))
        self.admin.execute(files('truss').joinpath('_security_bootstrap','preparation-permit-mint.sql').read_text())
        self.admin.execute(sql.SQL('ALTER FUNCTION truss.mint_preparation_permit_binding(int4,int4,xid8) OWNER TO {}').format(sql.Identifier(owner)))
        self.admin.execute(sql.SQL('GRANT pg_read_all_stats TO {} WITH INHERIT TRUE').format(sql.Identifier(owner)))
        self.admin.execute(files('truss').joinpath('_security_bootstrap','preparation-peer-xid.sql').read_text())
        self.admin.execute(sql.SQL('ALTER FUNCTION truss.require_preparation_peer_xid(int4,xid8) OWNER TO {}').format(sql.Identifier(owner)))
        self.admin.execute(files('truss').joinpath('_security_bootstrap','preparation-permit-binding-check.sql').read_text())
        self.admin.execute(sql.SQL('ALTER FUNCTION truss.check_preparation_permit_binding(int4,int4) OWNER TO {}').format(sql.Identifier(owner)))
        # Diagnostic wrapper only: no protected rows or authority are returned.
        # Production callers receive no execution on either private primitive.
        self.admin.execute('CREATE FUNCTION truss.binding_check_probe(a int4,c int4) RETURNS boolean LANGUAGE sql SECURITY DEFINER SET search_path=pg_catalog,pg_temp AS $$ SELECT truss.check_preparation_permit_binding(a,c) $$')
        self.admin.execute(sql.SQL('ALTER FUNCTION truss.binding_check_probe(int4,int4) OWNER TO {}').format(sql.Identifier(owner)))
        self.admin.execute('REVOKE ALL ON FUNCTION truss.binding_check_probe(int4,int4) FROM PUBLIC')
        self.admin.execute('GRANT EXECUTE ON FUNCTION truss.binding_check_probe(int4,int4) TO consumer')
        with self.assertRaises(psycopg.errors.InsufficientPrivilege):
            data.execute("SELECT truss.mint_preparation_permit_binding(1,1,'1'::xid8)")
        with self.assertRaises(psycopg.errors.InsufficientPrivilege):
            data.execute('SELECT truss.check_preparation_permit_binding(1,1)')
        data.execute('BEGIN ISOLATION LEVEL REPEATABLE READ')
        actual_xid = int(data.execute('SELECT pg_catalog.pg_current_xact_id()::text').fetchone()[0])
        self.assertEqual(self.admin.execute('SELECT truss.require_preparation_peer_xid(%s,%s::xid8)::text',(data.info.backend_pid,str(actual_xid))).fetchone(),(str(actual_xid),))
        # The forged epoch has identical native32 bits but is outside the
        # native allocator horizon. It cannot become admission evidence.
        self.assertEqual((actual_xid+2**32) & 0xffffffff,actual_xid & 0xffffffff)
        with self.assertRaises(psycopg.errors.ObjectNotInPrerequisiteState):
            self.admin.execute('SELECT truss.require_preparation_peer_xid(%s,%s::xid8)',(data.info.backend_pid,str(actual_xid+2**32)))
        snapshot = data.execute('SELECT pg_catalog.pg_current_snapshot()::text').fetchone()
        def check(anchor, coordinator):
            return data.execute('SELECT truss.binding_check_probe(%s,%s)',(anchor,coordinator.info.backend_pid)).fetchone()[0]
        def mint(connection, anchor, xid):
            connection.execute('SELECT truss.mint_preparation_permit_binding(%s,%s,%s::xid8)',(anchor,data.info.backend_pid,str(xid)))
        def fields(connection):
            return self.admin.execute("SELECT classid::int8,objid::int8,mode FROM pg_catalog.pg_locks WHERE pid=%s AND locktype='advisory' AND objsubid=2 AND classid BETWEEN 2147400100::oid AND 2147400104::oid ORDER BY classid",(connection.info.backend_pid,)).fetchall()
        self.admin.execute('BEGIN')
        mint(self.admin, 7, actual_xid)
        self.assertTrue(check(7,self.admin))
        self.assertFalse(check(8,self.admin))
        self.assertEqual(fields(self.admin),[(2147400100,self.admin.info.backend_pid,'ExclusiveLock'),
            (2147400101,7,'ShareLock'),(2147400102,data.info.backend_pid,'ShareLock'),
            (2147400103,actual_xid & 0xffffffff,'ShareLock'),(2147400104,actual_xid >> 32,'ShareLock')])
        # A second original backend may share individual field values; its
        # own coherent tuple/slot remains separate and never unioned by PID.
        peer = psycopg.connect(**psycopg.conninfo.conninfo_to_dict(self.info.connection_uri),autocommit=True)
        self.addCleanup(peer.close)
        peer.execute('BEGIN')
        mint(peer,8,actual_xid)
        self.assertEqual(len(fields(peer)),5)
        self.assertTrue(check(8,peer))
        self.assertFalse(check(7,peer))
        other_params=psycopg.conninfo.conninfo_to_dict(self.info.connection_uri)
        other_params['user']='consumer'
        with psycopg.connect(**other_params,autocommit=True) as other:
            other.execute('BEGIN ISOLATION LEVEL REPEATABLE READ')
            self.assertEqual(other.execute('SELECT truss.binding_check_probe(%s,%s)',(7,self.admin.info.backend_pid)).fetchone(),(False,))
            other.execute('ROLLBACK')
        peer.execute('ROLLBACK')
        self.admin.execute('SAVEPOINT duplicate_control')
        with self.assertRaises(psycopg.errors.ObjectNotInPrerequisiteState):
            mint(self.admin,9,actual_xid+1)
        self.admin.execute('ROLLBACK TO duplicate_control')
        self.assertEqual(len(fields(self.admin)),5)
        self.assertTrue(check(7,self.admin))
        self.assertEqual(self.admin.execute('COMMIT').statusmessage,'COMMIT')
        self.assertEqual(fields(self.admin),[])
        self.assertFalse(check(7,self.admin))
        self.assertEqual(data.execute('SELECT pg_catalog.pg_current_snapshot()::text').fetchone(),snapshot)
        # Weakened control: bare binding can be re-minted in a later
        # coordinator transaction. It is not original-anchor/attempt custody.
        self.admin.execute('BEGIN')
        mint(self.admin,7,actual_xid)
        self.assertTrue(check(7,self.admin))
        self.admin.execute('ROLLBACK')
        self.assertFalse(check(7,self.admin))
        peer.execute('BEGIN')
        mint(peer,11,actual_xid)
        self.assertTrue(check(11,peer))
        lost_pid=peer.info.backend_pid
        peer.close()
        deadline=time.monotonic()+5
        while True:
            self.admin.execute('SELECT pg_catalog.pg_stat_clear_snapshot()')
            if not self.admin.execute('SELECT EXISTS(SELECT 1 FROM pg_catalog.pg_stat_activity WHERE pid=%s)',(lost_pid,)).fetchone()[0]:
                break
            if time.monotonic()>=deadline:
                self.fail('Original coordinator termination not observed')
            time.sleep(.01)
        self.assertEqual(data.execute('SELECT truss.binding_check_probe(%s,%s)',(11,lost_pid)).fetchone(),(False,))
        # These are native xid8 codec vectors, not live authenticated cuts.
        for xid in (1,2**31-1,2**31,2**32-1,2**32,2**63-1,2**63,2**64-2**32-1,2**64-2,2**64-1):
            with self.subTest(xid=xid):
                self.admin.execute('BEGIN')
                mint(self.admin,10,xid)
                rows = fields(self.admin)
                self.assertEqual(rows[3][1],xid & 0xffffffff)
                self.assertEqual(rows[4][1],xid >> 32)
                self.admin.execute('ROLLBACK')
                self.assertEqual(fields(self.admin),[])
        data.execute('ROLLBACK')
        with self.assertRaises(psycopg.errors.ObjectNotInPrerequisiteState):
            self.admin.execute('SELECT truss.require_preparation_peer_xid(%s,%s::xid8)',(data.info.backend_pid,str(actual_xid)))
