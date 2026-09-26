\set c random(1, 20000)
\set p random(1, 5000)
WITH o AS (INSERT INTO sales.orders (id, "placedAt", status, total, "customerId", channel)
           VALUES (nextval('sales.id_seq'), now(), 'placed', 20.00, :c, 'web') RETURNING id)
INSERT INTO sales.order_lines (id, "lineNo", quantity, "unitPrice", "lineTotal", "orderId", "productId")
SELECT nextval('sales.id_seq'), g, 2, 5.00, 10.00, o.id, :p FROM o, generate_series(1, 2) g;
