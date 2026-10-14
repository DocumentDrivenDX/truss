"""Transactional transition-storage upgrade used by the public runtime installer."""
from psycopg import sql

_COLUMNS = {
    'runtime_object_transition': (
        'transition_id', 'attempt_id', 'operation_index', 'writer_xid',
        'object_id', 'type_id', 'before_object', 'after_object', 'after_keys', 'journal'),
    'runtime_edge_transition': (
        'transition_id', 'attempt_id', 'operation_index', 'writer_xid',
        'edge_id', 'rel_type_id', 'before_edge', 'after_edge', 'journal',
        'old_source', 'old_target', 'source_identity', 'target_identity'),
}
_KEYS = {
    'runtime_object_transition': ('attempt_id', 'operation_index', 'object_id', 'type_id'),
    'runtime_edge_transition': ('attempt_id', 'operation_index', 'edge_id', 'rel_type_id'),
}


def upgrade_transition_storage(cursor, generated_sql: str, owner_oid: int):
    """Caller already holds the installation fence and verified source release."""
    cursor.execute('LOCK TABLE truss.runtime_object_transition, truss.runtime_edge_transition IN ACCESS EXCLUSIVE MODE NOWAIT', prepare=False)
    snapshots = {}
    for table, columns in _COLUMNS.items():
        cursor.execute('SELECT relowner FROM pg_class WHERE oid=%s::regclass', ('truss.' + table,), prepare=False)
        if cursor.fetchone() != (owner_oid,):
            raise ValueError('Original protected transition owner required')
        cursor.execute('SELECT attname FROM pg_attribute WHERE attrelid=%s::regclass AND attnum>0 AND NOT attisdropped ORDER BY attnum', ('truss.' + table,), prepare=False)
        if tuple(row[0] for row in cursor.fetchall()) != columns:
            raise ValueError('Original transition column inventory required')
        cursor.execute("""SELECT c.conname, c.condeferrable, c.condeferred, c.convalidated,
            ARRAY(SELECT a.attname::text FROM unnest(c.conkey) WITH ORDINALITY k(n,ord)
                JOIN pg_attribute a ON a.attrelid=c.conrelid AND a.attnum=k.n ORDER BY k.ord)
            FROM pg_constraint c WHERE c.conrelid=%s::regclass AND c.contype='u'""", ('truss.' + table,), prepare=False)
        expected = (table + '_attempt_id_operation_index_key', False, False, True, ['attempt_id', 'operation_index'])
        if cursor.fetchall() != [expected]:
            raise ValueError('Original immediate single-entity transition constraint required')
        snapshot = table + '_upgrade_before'
        projection = sql.SQL(',').join(map(sql.Identifier, columns))
        cursor.execute(sql.SQL('CREATE TEMP TABLE {} ON COMMIT DROP AS SELECT {} FROM truss.{}').format(sql.Identifier(snapshot), projection, sql.Identifier(table)), prepare=False)
        snapshots[table] = (snapshot, projection)
    # The statements are hash-verified owner exports from the packaged UMF model.
    cursor.execute(generated_sql, prepare=False)
    for table, columns in _COLUMNS.items():
        target_columns = columns + (('endpoint_ownership',) if table == 'runtime_edge_transition' else ())
        cursor.execute('SELECT attname FROM pg_attribute WHERE attrelid=%s::regclass AND attnum>0 AND NOT attisdropped ORDER BY attnum', ('truss.' + table,), prepare=False)
        if tuple(row[0] for row in cursor.fetchall()) != target_columns:
            raise ValueError('Complete target transition column inventory required')
        cursor.execute("""SELECT c.condeferrable,c.condeferred,c.convalidated,
            ARRAY(SELECT a.attname::text FROM unnest(c.conkey) WITH ORDINALITY k(n,ord)
                JOIN pg_attribute a ON a.attrelid=c.conrelid AND a.attnum=k.n ORDER BY k.ord)
            FROM pg_constraint c WHERE c.conrelid=%s::regclass AND c.contype='u'""", ('truss.' + table,), prepare=False)
        if cursor.fetchall() != [(False, False, True, list(_KEYS[table]))]:
            raise ValueError('Exact immediate multi-entity transition constraint required')
        snapshot, projection = snapshots[table]
        cursor.execute(sql.SQL('SELECT EXISTS((SELECT {} FROM pg_temp.{} EXCEPT ALL SELECT {} FROM truss.{}) UNION ALL (SELECT {} FROM truss.{} EXCEPT ALL SELECT {} FROM pg_temp.{}))').format(projection, sql.Identifier(snapshot), projection, sql.Identifier(table), projection, sql.Identifier(table), projection, sql.Identifier(snapshot)), prepare=False)
        if cursor.fetchone() != (False,):
            raise ValueError('All original transition rows must survive unchanged')
        cursor.execute(sql.SQL('DROP TABLE pg_temp.{}').format(sql.Identifier(snapshot)), prepare=False)
    cursor.execute("""SELECT format_type(atttypid,atttypmod),attnotnull,atthasdef FROM pg_attribute
        WHERE attrelid='truss.runtime_edge_transition'::regclass AND attname='endpoint_ownership' AND NOT attisdropped""", prepare=False)
    if cursor.fetchone() != ('jsonb', False, False):
        raise ValueError('Nullable original endpoint context without synthetic default required')
    cursor.execute('SELECT EXISTS(SELECT 1 FROM truss.runtime_edge_transition WHERE endpoint_ownership IS NOT NULL)', prepare=False)
    if cursor.fetchone() != (False,):
        raise ValueError('Legacy contexts must remain absent rather than backfilled')
