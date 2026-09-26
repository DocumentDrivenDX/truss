-- SPIKE-002 option A: hand-written per-type migrations for R1-R5 (what a team or a truss runtime must write).
-- R1 add optional Customer.phone
ALTER TABLE sales.customers ADD COLUMN phone varchar(30);
-- R2 tighten Customer.name 100 -> 60: attempt (rejected by existing data), list violators, remediate, apply
ALTER TABLE sales.customers ALTER COLUMN name TYPE varchar(60);
SELECT id, char_length(name) FROM sales.customers WHERE char_length(name) > 60;
UPDATE sales.customers SET name = left(name, 60) WHERE char_length(name) > 60;
ALTER TABLE sales.customers ALTER COLUMN name TYPE varchar(60);
-- R3 add Customer -> Customer referredBy (targetMultiplicity 0..1)
ALTER TABLE sales.customers ADD COLUMN "referredById" bigint REFERENCES sales.customers (id);
CREATE INDEX customers_referred_by_idx ON sales.customers ("referredById");
-- R4 Customer.email one -> array
ALTER TABLE sales.customers ALTER COLUMN email TYPE varchar(200)[] USING CASE WHEN email IS NULL THEN NULL ELSE ARRAY[email] END;
-- R5 Order.channel absent-allowed -> required, backfill 'web'
UPDATE sales.orders SET channel = 'web' WHERE channel IS NULL;
ALTER TABLE sales.orders ALTER COLUMN channel SET NOT NULL;
