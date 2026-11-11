-- Candidate job-control functions over truss_bulk.job (apply after bulk-control-layout.sql).
-- DESIGN CANDIDATE, not qualified, not in the install baseline. Roles are created by the installer/test
-- harness, never here. Every state change goes through these SECURITY DEFINER functions; the worker
-- role has no table privileges, so a raw consumer INSERT/UPDATE into the control home is impossible.
--
-- Lock level: the job row lock taken here (SELECT ... FOR UPDATE) IS lock level 4a of CONTRACT-009
-- (owner decision 2026-11-10). It is the first and only lock these functions acquire. The CALLER owns
-- levels 1-4 (catalog, authority, namespace lifecycle, request identity) and must already hold them
-- when it calls in; this file cannot verify that. The job lock is held until the calling native
-- transaction terminates, and business/group locks (levels 5-9) are acquired by the executor after it.

CREATE FUNCTION truss_bulk._state(j truss_bulk.job) RETURNS jsonb
LANGUAGE sql IMMUTABLE AS $$
  SELECT jsonb_build_object('status', j.status, 'batchCount', j.batch_count, 'nextBatch', j.committed_batches,
    'committedBatches', j.committed_batches, 'fence', j.fence,
    'claim', CASE WHEN j.claim_batch IS NULL THEN NULL ELSE
       jsonb_build_object('batch', j.claim_batch, 'fence', j.claim_fence, 'effectAdmitted', j.effect_admitted) END,
    'cancelRequested', j.cancel_requested,
    'stop', CASE WHEN j.stop_batch IS NULL THEN NULL ELSE jsonb_build_object('batch', j.stop_batch, 'code', j.stop_code) END)
$$;

-- Seal: control-plane only. Creates the job row from the retained manifest bytes.
CREATE FUNCTION truss_bulk.submit(p_ns text, p_job text, p_batch_count integer, p_manifest bytea) RETURNS jsonb
LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog, pg_temp AS $$
DECLARE j truss_bulk.job;
BEGIN
  INSERT INTO truss_bulk.job (namespace, job_id, status, batch_count, committed_batches, fence, cancel_requested, manifest_sha256, manifest_bytes)
  VALUES (p_ns, p_job, CASE WHEN p_batch_count = 0 THEN 'completed' ELSE 'queued' END, p_batch_count, 0, '0', false,
          sha256(p_manifest), p_manifest) RETURNING * INTO j;
  RETURN jsonb_build_object('ok', true, 'state', truss_bulk._state(j),
    'basis', CASE WHEN p_batch_count = 0 THEN 'empty-manifest' ELSE 'seal-delegation-intent-capacity' END);
END $$;

-- Shared transition. p_result is the complete batch result retained on a confirmed commit.
CREATE FUNCTION truss_bulk._apply(p_ns text, p_job text, p_event jsonb, p_result bytea) RETURNS jsonb
LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog, pg_temp AS $$
DECLARE
  j truss_bulk.job; k text := p_event->>'kind'; basis text := NULL; nxt integer; ev text;
BEGIN
  SELECT * INTO j FROM truss_bulk.job WHERE namespace = p_ns AND job_id = p_job FOR UPDATE;  -- level 4a
  IF NOT FOUND THEN RETURN jsonb_build_object('ok', false, 'code', 'PAP_JOB'); END IF;

  IF j.status IN ('completed', 'stopped', 'cancelled') THEN
    IF k = 'cancel' THEN RETURN jsonb_build_object('ok', true, 'state', truss_bulk._state(j), 'basis', 'terminal-noop'); END IF;
    IF j.status = 'cancelled' AND k IN ('claim', 'execute') THEN RETURN jsonb_build_object('ok', false, 'code', 'PAP_CANCELLED'); END IF;
    RETURN jsonb_build_object('ok', false);
  END IF;

  IF k = 'cancel' THEN
    IF j.status = 'queued' OR (j.status = 'running' AND j.claim_batch IS NOT NULL AND NOT j.effect_admitted) THEN
      UPDATE truss_bulk.job SET status = 'cancelled', claim_batch = NULL, claim_fence = NULL, effect_admitted = NULL
        WHERE namespace = p_ns AND job_id = p_job RETURNING * INTO j;
      RETURN jsonb_build_object('ok', true, 'state', truss_bulk._state(j));
    END IF;
    UPDATE truss_bulk.job SET cancel_requested = true WHERE namespace = p_ns AND job_id = p_job RETURNING * INTO j;
    RETURN jsonb_build_object('ok', true, 'state', truss_bulk._state(j), 'basis', 'cancel-requested');
  END IF;

  IF j.status = 'queued' THEN
    IF k = 'claim' THEN
      UPDATE truss_bulk.job SET status = 'running', fence = (fence::numeric + 1)::text,
             claim_batch = committed_batches, claim_fence = (fence::numeric + 1)::text, effect_admitted = false
        WHERE namespace = p_ns AND job_id = p_job RETURNING * INTO j;
      RETURN jsonb_build_object('ok', true, 'state', truss_bulk._state(j));
    END IF;
    IF k = 'execute' THEN RETURN jsonb_build_object('ok', false, 'code', 'PAP_FENCE'); END IF;
    RETURN jsonb_build_object('ok', false);
  END IF;

  IF j.status = 'running' AND j.claim_batch IS NOT NULL THEN
    IF k = 'execute' THEN
      IF j.cancel_requested THEN RETURN jsonb_build_object('ok', false, 'code', 'PAP_CANCELLED'); END IF;
      IF p_event->>'fence' IS DISTINCT FROM j.claim_fence THEN RETURN jsonb_build_object('ok', false, 'code', 'PAP_FENCE'); END IF;
      IF (p_event->>'batch')::integer IS DISTINCT FROM j.claim_batch THEN RETURN jsonb_build_object('ok', false, 'code', 'PAP_ORDER'); END IF;
      IF j.effect_admitted THEN RETURN jsonb_build_object('ok', false); END IF;
      UPDATE truss_bulk.job SET effect_admitted = true WHERE namespace = p_ns AND job_id = p_job RETURNING * INTO j;
      RETURN jsonb_build_object('ok', true, 'state', truss_bulk._state(j));
    ELSIF k = 'commit' THEN
      IF NOT j.effect_admitted THEN RETURN jsonb_build_object('ok', false); END IF;
      RETURN truss_bulk._advance(j, p_result);
    ELSIF k = 'failure' THEN
      UPDATE truss_bulk.job SET status = 'stopped', stop_batch = claim_batch, stop_code = p_event->>'code',
             claim_batch = NULL, claim_fence = NULL, effect_admitted = NULL
        WHERE namespace = p_ns AND job_id = p_job RETURNING * INTO j;
      RETURN jsonb_build_object('ok', true, 'state', truss_bulk._state(j));
    ELSIF k = 'lose-custody' THEN
      IF NOT j.effect_admitted THEN RETURN jsonb_build_object('ok', false); END IF;
      UPDATE truss_bulk.job SET status = 'reconciling' WHERE namespace = p_ns AND job_id = p_job RETURNING * INTO j;
      RETURN jsonb_build_object('ok', true, 'state', truss_bulk._state(j));
    ELSIF k = 'expire-claim' THEN
      IF j.effect_admitted OR NOT COALESCE((p_event->>'confirmedNoExecution')::boolean, false) THEN RETURN jsonb_build_object('ok', false); END IF;
      UPDATE truss_bulk.job SET status = 'queued', claim_batch = NULL, claim_fence = NULL, effect_admitted = NULL
        WHERE namespace = p_ns AND job_id = p_job RETURNING * INTO j;
      RETURN jsonb_build_object('ok', true, 'state', truss_bulk._state(j));
    END IF;
    RETURN jsonb_build_object('ok', false);
  END IF;

  IF j.status = 'reconciling' AND j.claim_batch IS NOT NULL AND k = 'reconcile' THEN
    ev := p_event->>'evidence';
    IF ev = 'committed' THEN RETURN truss_bulk._advance(j, p_result); END IF;
    IF ev = 'noncommit-admitted' THEN
      UPDATE truss_bulk.job SET status = 'stopped', stop_batch = claim_batch, stop_code = 'PAP_ABORT_DISPOSITION_UNKNOWN',
             claim_batch = NULL, claim_fence = NULL, effect_admitted = NULL
        WHERE namespace = p_ns AND job_id = p_job RETURNING * INTO j;
      RETURN jsonb_build_object('ok', true, 'state', truss_bulk._state(j));
    END IF;
    RETURN jsonb_build_object('ok', true, 'state', truss_bulk._state(j), 'basis', 'unresolved');  -- never proves rollback
  END IF;
  RETURN jsonb_build_object('ok', false);
END $$;

-- Confirmed commit: advance the contiguous prefix; completed wins over a pending cancel at the final batch.
CREATE FUNCTION truss_bulk._advance(j truss_bulk.job, p_result bytea) RETURNS jsonb
LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog, pg_temp AS $$
DECLARE nxt integer := j.committed_batches + 1; r truss_bulk.job;
BEGIN
  IF p_result IS NOT NULL THEN
    INSERT INTO truss_bulk.batch_receipt VALUES (j.namespace, j.job_id, j.claim_batch, j.claim_fence, p_result, sha256(p_result));
  END IF;
  UPDATE truss_bulk.job SET committed_batches = nxt, claim_batch = NULL, claim_fence = NULL, effect_admitted = NULL,
         status = CASE WHEN nxt = batch_count THEN 'completed' WHEN cancel_requested THEN 'cancelled' ELSE 'queued' END
    WHERE namespace = j.namespace AND job_id = j.job_id RETURNING * INTO r;
  RETURN jsonb_build_object('ok', true, 'state', truss_bulk._state(r));
END $$;

-- Worker surface: claim/execute/commit/failure/lose-custody/reconcile/expire-claim only.
CREATE FUNCTION truss_bulk.worker_event(p_ns text, p_job text, p_event jsonb, p_result bytea DEFAULT NULL) RETURNS jsonb
LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog, pg_temp AS $$
BEGIN
  IF p_event->>'kind' NOT IN ('claim', 'execute', 'commit', 'failure', 'lose-custody', 'reconcile', 'expire-claim') THEN
    RETURN jsonb_build_object('ok', false, 'code', 'AUTHORIZATION');
  END IF;
  RETURN truss_bulk._apply(p_ns, p_job, p_event, p_result);
END $$;

-- Control surface: cancel (and any future retire); not granted to the worker role.
CREATE FUNCTION truss_bulk.control_event(p_ns text, p_job text, p_event jsonb) RETURNS jsonb
LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog, pg_temp AS $$
BEGIN
  IF p_event->>'kind' <> 'cancel' THEN RETURN jsonb_build_object('ok', false, 'code', 'AUTHORIZATION'); END IF;
  RETURN truss_bulk._apply(p_ns, p_job, p_event, NULL);
END $$;

REVOKE ALL ON ALL FUNCTIONS IN SCHEMA truss_bulk FROM PUBLIC;
REVOKE ALL ON ALL TABLES IN SCHEMA truss_bulk FROM PUBLIC;
