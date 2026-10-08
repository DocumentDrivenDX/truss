-- Private bounded scalar component; not the complete report encoder/resource ledger.
CREATE FUNCTION truss.runtime_canonical_string_bytes(original bytea) RETURNS bytea
LANGUAGE plpgsql IMMUTABLE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE validated bytea:=original; output bytea:=decode('22','hex'); n int; i int; b int;
BEGIN
 IF original IS NULL OR octet_length(original)>65536 THEN
  RAISE EXCEPTION 'bounded original string bytes required' USING ERRCODE='22023';
 END IF;
 n:=octet_length(original);
 -- PostgreSQL text excludes NUL. Replace only NUL in a validation copy; output
 -- below consumes original bytes and escapes every control, including NUL.
 IF n>0 THEN
  FOR i IN 0..n-1 LOOP
   IF get_byte(original,i)=0 THEN validated:=set_byte(validated,i,32); END IF;
  END LOOP;
 END IF;
 PERFORM convert_from(validated,'UTF8');
 IF n>0 THEN
  FOR i IN 0..n-1 LOOP
   b:=get_byte(original,i);
   IF b<32 THEN output:=output||convert_to(chr(92)||'u00'||lpad(to_hex(b),2,'0'),'UTF8');
   ELSIF b IN (34,92) THEN output:=output||decode('5c','hex')||substr(original,i+1,1);
   ELSE output:=output||substr(original,i+1,1); END IF;
  END LOOP;
 END IF;
 RETURN output||decode('22','hex');
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_canonical_string_bytes(bytea) FROM PUBLIC;
