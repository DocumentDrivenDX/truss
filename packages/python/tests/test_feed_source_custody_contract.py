from pathlib import Path

from truss.feed import FeedCursor, FeedPage, FeedSourceCustodyHandle, FeedSourceSelection


ROOT = Path(__file__).resolve().parents[1]
SQL = ROOT / "src/truss/_catalog_runtime/feed-custody.sql"
MIGRATION = ROOT / "src/truss/_migration_execute.py"
RUNTIME = ROOT / "src/truss/catalog_runtime.py"


def test_source_custody_models_are_frozen_and_keep_original_selection():
    page = FeedPage(
        consumer_id="consumer",
        registration_id="registration",
        prior=FeedCursor(content=b"prior"),
        next=FeedCursor(content=b"next"),
        content=b"page",
        sha256="0" * 64,
        writer_xid="10",
        safe_watermark_xid="11",
        outcome="transaction",
    )
    selection = FeedSourceSelection(
        page=page,
        maximum_facts=10,
        maximum_bytes=1024,
        request_bytes=b"request",
        destination_registration_bytes=b"opaque-registration",
        ack_scope_bytes=b"opaque-ack-scope",
        destination_id="destination",
        request_sha256="1" * 64,
        publication_id="publication",
    )
    handle = FeedSourceCustodyHandle(
        custody_id="00000000-0000-0000-0000-000000000001",
        selection_sha256="2" * 64,
        backend_pid="42",
        _connection_identity=1,
        _selection=selection,
    )
    assert handle._selection is selection
    try:
        handle.custody_id = "other"
    except AttributeError:
        pass
    else:
        raise AssertionError("custody handle must be immutable")


def test_open_serializes_with_consumer_writers_and_checks_exact_session_marker():
    source = SQL.read_text()
    assert "FROM truss.runtime_feed_consumer WHERE consumer_id=selected_consumer FOR UPDATE NOWAIT" in source
    assert "truss.runtime_feed_custody_lock_active(stale.backend_pid,stale.lock_key_a,stale.lock_key_b)" in source
    assert "l.locktype='advisory'" in source
    assert "l.database=(SELECT oid FROM pg_catalog.pg_database" in source
    assert "l.classid=selected_key_a::oid AND l.objid=selected_key_b::oid AND l.objsubid=2" in source
    assert "l.pid=selected_pid AND l.mode='ExclusiveLock' AND l.granted" in source
    assert "FROM pg_catalog.pg_stat_activity" not in source
    assert "lock_key_a integer NOT NULL" in source and "lock_key_b integer NOT NULL" in source
    assert "'secretToken'" not in source
    assert "selected_request_sha IS DISTINCT FROM encode(sha256(request_original),'hex')" in source
    assert "(cursor->>'installationId') IS DISTINCT FROM installation.installation_id::text" in source
    assert "opened_xid xid8 NOT NULL" in source
    assert source.count("coalesce(pg_current_xact_id_if_assigned()=active.opened_xid,false)") == 4
    assert "ALTER TABLE truss.runtime_feed_consumer ENABLE ALWAYS TRIGGER runtime_feed_source_custody_guard" in source
    assert "REVOKE ALL ON TABLE truss.runtime_feed_source_custody FROM PUBLIC" in source


def test_migration_locks_every_truss_table_before_active_custody_check():
    source = MIGRATION.read_text()
    lock = source.index("LOCK TABLE {} IN ACCESS EXCLUSIVE MODE NOWAIT")
    prune = source.index("SELECT truss.runtime_feed_custody_prune_stale()")
    check = source.index("SELECT EXISTS(SELECT 1 FROM truss.runtime_feed_source_custody)")
    assert lock < prune < check


def test_consumer_identity_update_checks_both_sides_and_cannot_rekey():
    source = SQL.read_text()
    update = source.index("IF TG_OP='UPDATE' THEN")
    old_check = source.index("runtime_feed_custody_assert_mutable(OLD.consumer_id)", update)
    new_check = source.index("runtime_feed_custody_assert_mutable(NEW.consumer_id)", update)
    immutable = source.index("OLD.consumer_id IS DISTINCT FROM NEW.consumer_id", update)
    assert update < old_check < new_check < immutable
    delete = source.index("IF TG_OP='DELETE' THEN")
    assert "runtime_feed_custody_assert_mutable(OLD.consumer_id)" in source[delete:update]


def test_reregistration_serializes_on_the_same_consumer_row():
    source = RUNTIME.read_text()
    registration = source.index("def register_feed_consumer_in_transaction")
    selection = source.index(
        "WHERE consumer_id=%s FOR UPDATE NOWAIT", registration
    )
    assert selection > registration


def test_host_marker_is_reused_after_a_contained_rollback():
    from types import SimpleNamespace
    from truss.psycopg_host import PsycopgHost

    class Cursor:
        def __init__(self):
            self.calls=[]
        def execute(self, query, params, **kwargs):
            self.calls.append((query,params,kwargs))
            if query=='SELECT pg_catalog.pg_backend_pid()::pg_catalog.text':
                self.admission=(('42','3/7','read_committed','read_write'),None,'10000')
        def fetchone(self):
            return (True,) if self.calls[-1][0]=='SELECT pg_catalog.pg_try_advisory_lock(%s,%s)' else ('42',)

    host=object.__new__(PsycopgHost)
    host._custody=SimpleNamespace(feed_source_lock_key=None,feed_source_session_token=None)
    cursor=Cursor()
    first=host._feed_source_lock_marker(cursor)
    second=host._feed_source_lock_marker(cursor)
    assert first==second
    assert len(cursor.calls)==2
    assert cursor.calls[1][0]=='SELECT pg_catalog.pg_backend_pid()::pg_catalog.text'
    assert cursor.calls[0][0]=='SELECT pg_catalog.pg_try_advisory_lock(%s,%s)'
    assert cursor.calls[0][1]==first[:2]
    assert all(type(part) is int and 1<=part<=2147483647 for part in first[:2])
    assert len(first[2])==64 and all(character in '0123456789abcdef' for character in first[2])
    binding=host._feed_source_custody_binding()
    assert binding==first and len(binding[2])==64
    assert all(character in '0123456789abcdef' for character in binding[2])


def test_connection_custody_marker_and_secret_are_not_handle_fields():
    from dataclasses import fields
    names={item.name for item in fields(FeedSourceCustodyHandle)}
    assert not {'_token','_lock_key_a','_lock_key_b','secret_token'} & names


def test_close_removes_the_row_but_leaves_session_liveness_to_connection_end():
    source=SQL.read_text()
    host=(ROOT / "src/truss/psycopg_host.py").read_text()
    close=source.index("CREATE FUNCTION truss.close_feed_source_custody")
    assert "DELETE FROM truss.runtime_feed_source_custody WHERE custody_id=custody" in source[close:]
    assert "pg_advisory_unlock" not in source
    assert "pg_advisory_unlock" not in host
    assert "the original session may still be live" in host


def test_every_custody_callback_binds_the_guarded_observation_not_callback_argument():
    from types import SimpleNamespace
    from truss.catalog_runtime import _feed_source_cursor_pid, _feed_source_cursor_matches

    good=SimpleNamespace(admission=(('42','3/7','read_committed','read_write'),'99','10000'))
    malformed=(SimpleNamespace(admission=None),SimpleNamespace(admission=(('0','3/7','read_committed','read_write'),None,'10000')),
        SimpleNamespace(admission=(('42','3/7'),None,'10000')))
    assert _feed_source_cursor_pid(good)=='42'
    assert _feed_source_cursor_matches(good,'42')
    assert not _feed_source_cursor_matches(good,'43')
    assert all(_feed_source_cursor_pid(cursor) is None for cursor in malformed)

    source=RUNTIME.read_text()
    start=source.index('def open_feed_source_custody_in_transaction')
    end=source.index('def acknowledge_feed_in_transaction',start)
    custody=source[start:end]
    assert 'observed[0][0]' not in custody
    assert custody.count('_feed_source_cursor_pid(cursor)')==1
    host_source=(ROOT / "src/truss/psycopg_host.py").read_text()
    assert "session_pid = query == 'SELECT pg_catalog.pg_backend_pid()::pg_catalog.text'" in host_source
    assert custody.count('_feed_source_cursor_matches(cursor,backend_pid)')==1
    assert custody.count('_feed_source_cursor_matches(cursor,handle.backend_pid)')==3
