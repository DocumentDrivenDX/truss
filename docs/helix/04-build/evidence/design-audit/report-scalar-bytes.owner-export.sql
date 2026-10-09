CREATE FUNCTION truss.runtime_report_scalar_bytes_v0_2(original bytea) RETURNS bytea LANGUAGE plpgsql IMMUTABLE SECURITY INVOKER SET search_path TO pg_catalog, pg_temp AS $$
DECLARE n integer; i integer:=0; b integer; c integer; width integer; j integer;
 expected bigint:=2; chunk bytea:=decode('22','hex'); chunks bytea[]:=ARRAY[]::bytea[];
 piece bytea; output bytea;
BEGIN
 IF original IS NULL THEN RAISE EXCEPTION 'original scalar bytes required' USING ERRCODE='22023'; END IF;
 n:=octet_length(original);
 IF n>1048576 THEN RAISE EXCEPTION 'scalar source capacity' USING ERRCODE='54000'; END IF;
 -- Validate complete UTF-8 and check the candidate output ceiling before emission.
 WHILE i<n LOOP
  b:=get_byte(original,i);
  IF b<128 THEN width:=1;
  ELSIF b BETWEEN 194 AND 223 THEN width:=2;
  ELSIF b BETWEEN 224 AND 239 THEN width:=3;
  ELSIF b BETWEEN 240 AND 244 THEN width:=4;
  ELSE RAISE EXCEPTION 'invalid scalar UTF8' USING ERRCODE='22021'; END IF;
  IF i+width>n THEN RAISE EXCEPTION 'unfinished scalar UTF8' USING ERRCODE='22021'; END IF;
  IF width>1 THEN
   FOR j IN 1..width-1 LOOP
    c:=get_byte(original,i+j);
    IF c NOT BETWEEN 128 AND 191 OR
     (j=1 AND ((b=224 AND c<160) OR (b=237 AND c>159) OR
                (b=240 AND c<144) OR (b=244 AND c>143))) THEN
     RAISE EXCEPTION 'invalid scalar UTF8 continuation' USING ERRCODE='22021';
    END IF;
   END LOOP;
  END IF;
  expected:=expected+CASE WHEN b<32 THEN 6 WHEN b IN (34,92) THEN 2 ELSE width END;
  IF expected>1048576 THEN RAISE EXCEPTION 'scalar output capacity' USING ERRCODE='54000'; END IF;
  i:=i+width;
 END LOOP;
 i:=0;
 WHILE i<n LOOP
  b:=get_byte(original,i);
  width:=CASE WHEN b<128 THEN 1 WHEN b<224 THEN 2 WHEN b<240 THEN 3 ELSE 4 END;
  IF b<32 THEN piece:=convert_to(chr(92)||'u00'||lpad(to_hex(b),2,'0'),'UTF8');
  ELSIF b IN (34,92) THEN piece:=decode('5c','hex')||substr(original,i+1,1);
  ELSE piece:=substr(original,i+1,width); END IF;
  IF octet_length(chunk)+octet_length(piece)>65536 THEN
   chunks:=array_append(chunks,chunk);chunk:=decode('','hex');
  END IF;
  chunk:=chunk||piece;i:=i+width;
 END LOOP;
 IF octet_length(chunk)+1>65536 THEN chunks:=array_append(chunks,chunk);chunk:=decode('','hex'); END IF;
 chunks:=array_append(chunks,chunk||decode('22','hex'));
 SELECT string_agg(value,decode('','hex') ORDER BY ordinal) INTO output
  FROM unnest(chunks) WITH ORDINALITY AS c(value,ordinal);
 IF octet_length(output)<>expected THEN RAISE EXCEPTION 'complete scalar byte parity required' USING ERRCODE='55000'; END IF;
 RETURN output;
END;
$$; REVOKE ALL ON FUNCTION truss.runtime_report_scalar_bytes_v0_2(bytea) FROM public