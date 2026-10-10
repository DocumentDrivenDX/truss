-- Unexecuted PostgreSQL 17 direct hierarchy observation; $1 is original namespace OID.
-- Include links with either endpoint in scope, including index inheritance.
SELECT i.tableoid::pg_catalog.oid::pg_catalog.text AS catalog_class_oid,
       i.inhrelid::pg_catalog.text AS child_relation_oid,
       i.inhparent::pg_catalog.text AS parent_relation_oid,
       i.inhseqno::pg_catalog.text AS parent_ordinal,
       pg_catalog.to_jsonb(i)::pg_catalog.text AS original_catalog_row_json
FROM pg_catalog.pg_inherits AS i
WHERE EXISTS (SELECT 1 FROM pg_catalog.pg_class AS c
              WHERE c.relnamespace = $1::pg_catalog.oid
                AND (c.oid = i.inhrelid OR c.oid = i.inhparent))
ORDER BY i.inhrelid, i.inhseqno, i.inhparent;
