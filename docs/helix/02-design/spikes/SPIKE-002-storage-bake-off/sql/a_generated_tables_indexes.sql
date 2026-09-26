CREATE SCHEMA IF NOT EXISTS "sales";
CREATE TABLE "sales"."customers" (
  "id" bigint NOT NULL,
  "code" varchar(20) NOT NULL,
  "name" varchar(100) NOT NULL,
  "email" varchar(200),
  "createdAt" timestamptz(6) NOT NULL,
  "payload" jsonb,
  CONSTRAINT "ck_customers_payload_object" CHECK ("payload" IS NULL OR jsonb_typeof("payload") = 'object')
);
CREATE TABLE "sales"."orders" (
  "id" bigint NOT NULL,
  "placedAt" timestamptz(6) NOT NULL,
  "status" varchar(20) NOT NULL,
  "channel" varchar(20),
  "total" numeric(14,2) NOT NULL,
  "customerId" bigint NOT NULL
);
CREATE TABLE "sales"."order_lines" (
  "id" bigint NOT NULL,
  "lineNo" smallint NOT NULL,
  "quantity" integer NOT NULL,
  "unitPrice" numeric(12,2) NOT NULL,
  "lineTotal" numeric(14,2) NOT NULL,
  "orderId" bigint NOT NULL,
  "productId" bigint NOT NULL
);
CREATE TABLE "sales"."products" (
  "id" bigint NOT NULL,
  "sku" varchar(32) NOT NULL,
  "name" varchar(200) NOT NULL,
  "price" numeric(12,2) NOT NULL,
  "image" bytea
);
CREATE INDEX "orders_total_btree" ON "sales"."orders" USING btree ("total");
CREATE UNIQUE INDEX "customers_code_unique" ON "sales"."customers" USING btree ("code");
