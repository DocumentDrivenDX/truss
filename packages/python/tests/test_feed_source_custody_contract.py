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


def test_open_serializes_with_consumer_writers_and_checks_stale_backend_identity():
    source = SQL.read_text()
    assert "FROM truss.runtime_feed_consumer WHERE consumer_id=selected_consumer FOR UPDATE NOWAIT" in source
    assert "a.pid=stale.backend_pid AND a.backend_start=stale.backend_start" in source
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
