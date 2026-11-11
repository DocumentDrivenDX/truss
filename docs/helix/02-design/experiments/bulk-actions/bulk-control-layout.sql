-- Candidate fixed-layout control homes for frozen-manifest bulk jobs (CONTRACT-013, UMF CONTRACT-904).
-- DESIGN CANDIDATE: not part of the qualified Truss install baseline, not exported by UMF, no grants,
-- no runtime writer. Constraints encode the job-state invariants so an invalid row cannot persist
-- even if a worker is wrong; transition legality (which event may follow which) stays in the
-- executor under the job lock (see _bulk_job_control.py). One home per concern; never per job.
CREATE SCHEMA truss_bulk;

CREATE TABLE truss_bulk.job (
  namespace            text    NOT NULL CHECK (namespace ~ '^[A-Za-z0-9_-]{1,128}$'),
  job_id               text    NOT NULL CHECK (job_id ~ '^[A-Za-z0-9_-]{1,128}$'),
  status               text    NOT NULL CHECK (status IN ('queued','running','reconciling','completed','stopped','cancelled')),
  batch_count          integer NOT NULL CHECK (batch_count >= 0),
  committed_batches    integer NOT NULL CHECK (committed_batches >= 0),
  fence                text    NOT NULL CHECK (fence ~ '^(0|[1-9][0-9]*)$'),
  claim_batch          integer,
  claim_fence          text    CHECK (claim_fence ~ '^(0|[1-9][0-9]*)$'),
  effect_admitted      boolean,
  cancel_requested     boolean NOT NULL,
  stop_batch           integer,
  stop_code            text    CHECK (stop_code ~ '^[A-Z][A-Z0-9_]{0,63}$'),
  manifest_sha256      bytea   NOT NULL CHECK (octet_length(manifest_sha256) = 32),
  manifest_bytes       bytea   NOT NULL CHECK (octet_length(manifest_bytes) BETWEEN 1 AND 16777216),
  PRIMARY KEY (namespace, job_id),
  -- Job status counts only confirmed contiguous batch outcomes.
  CONSTRAINT committed_within_batches CHECK (committed_batches <= batch_count),
  -- A claim is all-or-nothing and names the next unconfirmed batch under the current fence.
  CONSTRAINT claim_all_or_none CHECK ((claim_batch IS NULL) = (claim_fence IS NULL) AND (claim_batch IS NULL) = (effect_admitted IS NULL)),
  CONSTRAINT claim_is_next_batch CHECK (claim_batch IS NULL OR (claim_batch = committed_batches AND claim_batch < batch_count)),
  CONSTRAINT claim_fence_is_current CHECK (claim_fence IS NULL OR claim_fence = fence),
  CONSTRAINT stop_all_or_none CHECK ((stop_batch IS NULL) = (stop_code IS NULL)),
  CONSTRAINT stop_within_batches CHECK (stop_batch IS NULL OR stop_batch < batch_count),
  CONSTRAINT status_shape CHECK (
    CASE status
      WHEN 'queued'      THEN claim_batch IS NULL AND stop_batch IS NULL AND committed_batches < batch_count
      WHEN 'running'     THEN claim_batch IS NOT NULL AND stop_batch IS NULL
      WHEN 'reconciling' THEN claim_batch IS NOT NULL AND effect_admitted AND stop_batch IS NULL
      WHEN 'completed'   THEN claim_batch IS NULL AND stop_batch IS NULL AND committed_batches = batch_count
      WHEN 'stopped'     THEN claim_batch IS NULL AND stop_batch IS NOT NULL
      WHEN 'cancelled'   THEN claim_batch IS NULL AND stop_batch IS NULL AND committed_batches < batch_count
    END),
  -- A cancel request is recorded only against an admitted attempt and stays as history once the job
  -- is terminal (including a final batch that committed before the cancel could fence anything);
  -- an idle (queued) job never carries one.
  CONSTRAINT cancel_request_shape CHECK (NOT cancel_requested OR status IN ('completed','stopped','cancelled') OR (status IN ('running','reconciling') AND effect_admitted))
);

-- Complete batch/item outcomes, written only in the batch's confirmed commit (never rewritten).
CREATE TABLE truss_bulk.batch_receipt (
  namespace        text    NOT NULL,
  job_id           text    NOT NULL,
  batch            integer NOT NULL CHECK (batch >= 0),
  fence            text    NOT NULL CHECK (fence ~ '^(0|[1-9][0-9]*)$'),
  result_bytes     bytea   NOT NULL CHECK (octet_length(result_bytes) BETWEEN 1 AND 2097152), -- R = 2 MiB
  result_sha256    bytea   NOT NULL CHECK (octet_length(result_sha256) = 32),
  PRIMARY KEY (namespace, job_id, batch),
  FOREIGN KEY (namespace, job_id) REFERENCES truss_bulk.job (namespace, job_id)
);

-- Safety net (owner decision 2026-11-10, option 1): at COMMIT, a job's committed_batches must equal the number of
-- its receipts and those receipts must be exactly batches 0..n-1. An executor that writes a receipt without
-- advancing the prefix (or the reverse) cannot commit. This adds no transition logic; the explicit functions
-- still make the advance. DEFERRABLE INITIALLY DEFERRED so a single transaction may do both in either order.
CREATE FUNCTION truss_bulk._check_prefix() RETURNS trigger
LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog, pg_temp AS $$  -- deferred triggers run as the session role
DECLARE ns text; jb text; n integer; hi integer; c integer;
BEGIN
  IF TG_OP = 'DELETE' THEN ns := OLD.namespace; jb := OLD.job_id; ELSE ns := NEW.namespace; jb := NEW.job_id; END IF;
  SELECT committed_batches INTO c FROM truss_bulk.job WHERE namespace = ns AND job_id = jb;
  IF NOT FOUND THEN
    IF EXISTS (SELECT 1 FROM truss_bulk.batch_receipt WHERE namespace = ns AND job_id = jb) THEN
      RAISE EXCEPTION 'receipts without a job row (%/%)', ns, jb USING ERRCODE = 'integrity_constraint_violation';
    END IF;
    RETURN NULL;
  END IF;
  SELECT count(*), coalesce(max(batch), -1) INTO n, hi FROM truss_bulk.batch_receipt WHERE namespace = ns AND job_id = jb;
  IF n <> c OR hi <> c - 1 THEN
    RAISE EXCEPTION 'committed prefix % does not match % receipts (highest batch %) for %/%', c, n, hi, ns, jb
      USING ERRCODE = 'integrity_constraint_violation';
  END IF;
  RETURN NULL;
END $$;
CREATE CONSTRAINT TRIGGER job_prefix_matches_receipts AFTER INSERT OR UPDATE OR DELETE ON truss_bulk.job
  DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION truss_bulk._check_prefix();
CREATE CONSTRAINT TRIGGER receipts_match_job_prefix AFTER INSERT OR UPDATE OR DELETE ON truss_bulk.batch_receipt
  DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION truss_bulk._check_prefix();
