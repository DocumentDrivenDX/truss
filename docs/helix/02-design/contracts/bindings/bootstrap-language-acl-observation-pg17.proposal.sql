-- Unexecuted PG17 original admitted object OIDs; unique nonnull 1D <=256.
-- Complete default/explicit ACL expansion; not effective rights or runtime admission.
SELECT p.tableoid::pg_catalog.oid::pg_catalog.text AS catalog_class_oid,
       p.oid::pg_catalog.text AS object_oid,
       p.lanowner::pg_catalog.text AS owner_oid,
       p.lanacl IS NULL AS original_acl_is_null,
       p.lanacl::pg_catalog.text AS original_acl_native_text,
       pg_catalog.array_dims(p.lanacl) AS original_acl_native_dimensions,
       pg_catalog.cardinality(COALESCE(p.lanacl,
           pg_catalog.acldefault('l'::pg_catalog."char", p.lanowner))) AS assumed_acl_item_count,
       a.grantor IS NOT NULL AS has_expanded_grant,
       a.grantor::pg_catalog.text AS grantor_oid,
       a.grantee::pg_catalog.text AS grantee_oid,
       a.privilege_type,
       a.is_grantable
FROM pg_catalog.pg_language AS p
LEFT JOIN LATERAL pg_catalog.aclexplode(COALESCE(p.lanacl,
    pg_catalog.acldefault('l'::pg_catalog."char", p.lanowner))) AS a ON true
WHERE p.oid = ANY($1::pg_catalog.oid[])
ORDER BY p.oid, a.grantor, a.grantee, a.privilege_type, a.is_grantable;
