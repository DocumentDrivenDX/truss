-- Protected parent-row exclusion candidate; not executed or installed.
-- $1 original endpoint type int4, $2 original endpoint ID int8.
-- Execute under the original complete sorted lock plan and authority admission.
-- Return exactly the admitted live parent; missing/mismatched parent requires revalidation.
-- This statement does not observe participation counts or refresh a fixed snapshot.
SELECT o.type_id::pg_catalog.text AS endpoint_type,
       o.id::pg_catalog.text AS endpoint_id
FROM truss.object AS o
WHERE o.type_id = $1::pg_catalog.int4
  AND o.id = $2::pg_catalog.int8
FOR UPDATE;
