-- Fixed native fixture helper. Not a generic subject mapping or installer.
CREATE FUNCTION truss.named_subject_current(actor text)
RETURNS TABLE(staff_id text)
LANGUAGE sql SET search_path=pg_catalog AS $$ SELECT s.staff_id FROM truss.sec_staff s WHERE actor=SESSION_USER::text AND actor='fact_cut_actor' AND s.staff_id='s1' $$;
