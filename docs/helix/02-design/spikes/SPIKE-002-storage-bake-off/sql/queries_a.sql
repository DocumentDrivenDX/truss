-- q1_fetch (per type, hand-written)
SELECT * FROM sales.customers WHERE id = :k;

-- q2_hop1 (per type, hand-written)
SELECT * FROM sales.order_lines WHERE "orderId" = :k;

-- q3_hop2 (per type, hand-written)
SELECT l.* FROM sales.orders o
  JOIN sales.order_lines l ON l."orderId" = o.id
  WHERE o."customerId" = :k;

-- q4_hop3 (per type, hand-written)
SELECT p.* FROM sales.orders o
  JOIN sales.order_lines l ON l."orderId" = o.id
  JOIN sales.products p ON p.id = l."productId"
  WHERE o."customerId" = :k;

-- q5_range (per type, hand-written)
SELECT * FROM sales.orders WHERE total BETWEEN :lo AND :lo + 10;

-- q6_update (per type, hand-written)
UPDATE sales.orders SET status = :s WHERE id = :k;
