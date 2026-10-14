"""Owner-private native tuple binding only; no authority/anchor/permit claim."""
from importlib.resources import files
import psycopg
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
        with self.assertRaises(psycopg.errors.InsufficientPrivilege):
            data.execute("SELECT truss.mint_preparation_permit_binding(1,1,'1'::xid8)")
        data.execute('BEGIN ISOLATION LEVEL REPEATABLE READ')
        actual_xid = int(data.execute('SELECT pg_catalog.pg_current_xact_id()::text').fetchone()[0])
        def mint(connection, anchor, xid):
            connection.execute('SELECT truss.mint_preparation_permit_binding(%s,%s,%s::xid8)',(anchor,data.info.backend_pid,str(xid)))
        def fields(connection):
            return self.admin.execute("SELECT classid::int8,objid::int8,mode FROM pg_catalog.pg_locks WHERE pid=%s AND locktype='advisory' AND objsubid=2 AND classid BETWEEN 2147400100::oid AND 2147400104::oid ORDER BY classid",(connection.info.backend_pid,)).fetchall()
        self.admin.execute('BEGIN')
        mint(self.admin, 7, actual_xid)
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
        peer.execute('ROLLBACK')
        self.admin.execute('SAVEPOINT duplicate_control')
        with self.assertRaises(psycopg.errors.ObjectNotInPrerequisiteState):
            mint(self.admin,9,actual_xid+1)
        self.admin.execute('ROLLBACK TO duplicate_control')
        self.assertEqual(len(fields(self.admin)),5)
        self.assertEqual(self.admin.execute('COMMIT').statusmessage,'COMMIT')
        self.assertEqual(fields(self.admin),[])
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
