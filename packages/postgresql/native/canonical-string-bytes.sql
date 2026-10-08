-- Private bounded scalar component; not the complete report encoder/resource ledger.
CREATE FUNCTION truss.runtime_canonical_string_bytes(original bytea) RETURNS bytea
LANGUAGE plpgsql IMMUTABLE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE validated bytea:=original; chunk bytea:=decode('22','hex'); chunks bytea[]:=ARRAY[]::bytea[];
 output bytea; piece bytea; expected bigint:=2; n int; i int; b int;
BEGIN
 IF original IS NULL OR octet_length(original)>65536 THEN
  RAISE EXCEPTION 'bounded original string bytes required' USING ERRCODE='22023';
 END IF;
 n:=octet_length(original);
 -- PostgreSQL text excludes NUL. Replace only NUL in a validation copy; output
 -- below consumes original bytes and escapes every control, including NUL.
 IF n>0 THEN
  FOR i IN 0..n-1 LOOP
   b:=get_byte(original,i);
   expected:=expected+CASE WHEN b<32 THEN 6 WHEN b IN (34,92) THEN 2 ELSE 1 END;
   IF b=0 THEN validated:=set_byte(validated,i,32); END IF;
  END LOOP;
 END IF;
 PERFORM convert_from(validated,'UTF8');
 IF n>0 THEN
  FOR i IN 0..n-1 LOOP
   b:=get_byte(original,i);
   IF b<32 THEN piece:=convert_to(chr(92)||'u00'||lpad(to_hex(b),2,'0'),'UTF8');
   ELSIF b IN (34,92) THEN piece:=decode('5c','hex')||substr(original,i+1,1);
   ELSE piece:=substr(original,i+1,1); END IF;
   IF octet_length(chunk)+octet_length(piece)>65536 THEN
    chunks:=array_append(chunks,chunk); chunk:=decode('','hex');
   END IF;
   chunk:=chunk||piece;
  END LOOP;
 END IF;
 IF octet_length(chunk)=65536 THEN chunks:=array_append(chunks,chunk);chunk:=decode('','hex'); END IF;
 chunks:=array_append(chunks,chunk||decode('22','hex'));
 SELECT string_agg(value,decode('','hex') ORDER BY ordinal) INTO output FROM unnest(chunks) WITH ORDINALITY AS c(value,ordinal);
 IF octet_length(output)<>expected OR expected>393218 THEN
  RAISE EXCEPTION 'complete canonical string byte parity required' USING ERRCODE='55000';
 END IF;
 RETURN output;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_canonical_string_bytes(bytea) FROM PUBLIC;
