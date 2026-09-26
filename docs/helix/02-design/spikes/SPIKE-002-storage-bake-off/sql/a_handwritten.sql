-- SPIKE-002 option A: hand-written DDL that UMF's CONTRACT-043 generator (tables + indexes stage, master 24d3bf3)
-- does not emit. Applied after sql/a_generated_tables_indexes.sql and the bulk load.
-- Every statement is marked HAND-n; the list is repeated in the spike document.

-- HAND-1..4: primary keys. Generator residual: "DDD identity is retained; this table slice does not emit a primary or unique key".
ALTER TABLE "sales"."customers"   ADD CONSTRAINT "customers_pkey"   PRIMARY KEY ("id");   -- HAND-1
ALTER TABLE "sales"."orders"      ADD CONSTRAINT "orders_pkey"      PRIMARY KEY ("id");   -- HAND-2
ALTER TABLE "sales"."order_lines" ADD CONSTRAINT "order_lines_pkey" PRIMARY KEY ("id");   -- HAND-3
ALTER TABLE "sales"."products"    ADD CONSTRAINT "products_pkey"    PRIMARY KEY ("id");   -- HAND-4
-- (Customer alternate key account-code: enforced by the generated binding index "customers_code_unique",
--  which comes from a physical index declaration in the binding, not from the authored Key.)

-- HAND-5..7: foreign keys for the three core relationships. Generator residual: "Relationship storage is handled by
-- the relationship-dependent generator". The FK columns themselves exist only because the DDD view carries
-- truss-local stand-in scalar fields (customerId, orderId, productId).
ALTER TABLE "sales"."orders" ADD CONSTRAINT "orders_customer_fk"
  FOREIGN KEY ("customerId") REFERENCES "sales"."customers" ("id");                        -- HAND-5 (order-customer)
ALTER TABLE "sales"."order_lines" ADD CONSTRAINT "order_lines_order_fk"
  FOREIGN KEY ("orderId") REFERENCES "sales"."orders" ("id");                              -- HAND-6 (order-lines)
ALTER TABLE "sales"."order_lines" ADD CONSTRAINT "order_lines_product_fk"
  FOREIGN KEY ("productId") REFERENCES "sales"."products" ("id");                          -- HAND-7 (line-product)

-- HAND-8..9: traversal indexes on FK columns (not declared in the binding; PostgreSQL does not create them).
CREATE INDEX "orders_customer_idx"   ON "sales"."orders" ("customerId");                   -- HAND-8
CREATE INDEX "order_lines_order_idx" ON "sales"."order_lines" ("orderId");                 -- HAND-9

-- HAND-10: record-level invariant OrderLine.line-total. Generator residual: "DDD invariant is retained but not
-- interpreted or enforced". Core 0.7.0 has no invariant concept (CONTRACT-048 proposal).
ALTER TABLE "sales"."order_lines" ADD CONSTRAINT "order_lines_line_total_ck"
  CHECK ("lineTotal" = "quantity" * "unitPrice");                                          -- HAND-10

-- HAND-11: decimal scale guard is NOT possible after numeric(p,s) coercion (input is rounded before any CHECK runs);
-- recorded as a gap, no statement.

-- HAND-12: Order.lines targetMultiplicity min 1 ("each Order has at least one OrderLine"): deferred constraint trigger.
-- Concurrency caveat: under READ COMMITTED two transactions deleting different last lines both pass (see enforcement suite).
CREATE OR REPLACE FUNCTION "sales"."order_min_lines"() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE o bigint;
BEGIN
  IF TG_TABLE_NAME = 'orders' THEN o := NEW."id"; ELSE o := OLD."orderId"; END IF;
  IF EXISTS (SELECT 1 FROM "sales"."orders" WHERE "id" = o)
     AND NOT EXISTS (SELECT 1 FROM "sales"."order_lines" WHERE "orderId" = o) THEN
    RAISE EXCEPTION 'relationship order-lines: Order % has 0 OrderLine (min 1)', o USING ERRCODE = '23514';
  END IF;
  RETURN NULL;
END $$;                                                                                    -- HAND-12
CREATE CONSTRAINT TRIGGER "orders_min_lines" AFTER INSERT ON "sales"."orders"
  DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION "sales"."order_min_lines"();  -- HAND-12
CREATE CONSTRAINT TRIGGER "order_lines_min_lines" AFTER DELETE OR UPDATE OF "orderId" ON "sales"."order_lines"
  DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION "sales"."order_min_lines"();  -- HAND-12

-- HAND-13: sequence for new ids used by the background writer and suites (UMF emits no identity/default policy).
CREATE SEQUENCE IF NOT EXISTS "sales"."id_seq" START 10000000;                             -- HAND-13
ANALYZE "sales"."customers"; ANALYZE "sales"."orders"; ANALYZE "sales"."order_lines"; ANALYZE "sales"."products";
