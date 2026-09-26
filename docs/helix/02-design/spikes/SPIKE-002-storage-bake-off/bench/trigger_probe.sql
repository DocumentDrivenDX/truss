-- Catalog-driven validation trigger (sql/c_validate_trigger.sql): violating and control writes, each rolled back.
\set VERBOSITY terse
BEGIN; INSERT INTO c.object (type_id, props, rev) VALUES (5, '{"22":990001,"23":"T","25":1.00}', 0); ROLLBACK;
BEGIN; INSERT INTO c.object (type_id, props, rev) VALUES (5, '{"22":990001,"23":"T","24":"n","25":1.005}', 0); ROLLBACK;
BEGIN; INSERT INTO c.object (type_id, props, rev) VALUES (5, '{"22":990001,"23":"xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx","24":"n","25":1.00}', 0); ROLLBACK;
BEGIN; INSERT INTO c.object (type_id, props, rev) VALUES (5, '{"22":990001,"23":"T","24":"n","25":1.00,"99":1}', 0); ROLLBACK;
BEGIN; INSERT INTO c.object (type_id, props, rev) VALUES (5, '{"22":990001,"23":"T","24":"n","25":1.00,"26":"not base64!"}', 0); ROLLBACK;
BEGIN; INSERT INTO c.object (type_id, props, rev) VALUES (1, '{"1":990001,"2":"T990001","3":"n","5":"2026-09-25T10:00:00Z","6":["ok","tttttttttttttttttttttttttttttttt"]}', 0); ROLLBACK;
BEGIN; INSERT INTO c.object (type_id, props, rev) VALUES (5, '{"22":990001,"23":"T","24":"n","25":1.00}', 0); SELECT 'control accepted' AS result; ROLLBACK;
-- A revision is a catalog UPDATE; detecting existing violators reuses the same function (R2: name length 60):
\timing on
SELECT count(*) AS customers_violating_name_len_60 FROM c.object o JOIN c.prop_def p ON p.type_id = o.type_id AND p.element = 'Customer.name'
 WHERE c.validate_scalar(p.scalar_type, '{"length":{"max":60}}', o.props -> p.prop_id::text) IS NOT NULL;
