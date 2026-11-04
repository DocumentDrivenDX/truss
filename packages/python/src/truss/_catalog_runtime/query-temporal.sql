-- SPDX-License-Identifier: MIT OR Apache-2.0
-- F7 / CONTRACT-075 strict temporal scalar primitive for the new native source.
-- Not enrolled by the ordinary ABI1.2 manifest. Enrollment belongs to the
-- complete reviewed ABI1.3/native0.76 inventory, computed from actual bytes.
CREATE FUNCTION truss.query_temporal_canonical_text(kind text, token text) RETURNS text
LANGUAGE plpgsql IMMUTABLE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE
 calendar_value date;
 year_value int;
 hour_value int;
 minute_value int;
 second_value int;
 suffix_length int := 0;
 offset_token text;
 offset_minutes int := 0;
 fraction_text text := '';
 second_of_day int;
 day_delta int;
 canonical_date text;
BEGIN
 -- Bound bytes and require ASCII before regex or calendar materialization.
 IF kind IS NULL OR kind NOT IN ('date','instant','local') OR token IS NULL
  OR octet_length(token)>32 OR octet_length(token)<>length(token) THEN
  RAISE EXCEPTION 'strict temporal kind and bounded ASCII token required' USING ERRCODE='22023';
 END IF;
 -- This character inventory also rejects line terminators independently of
 -- regex end-anchor behavior. Lowercase separators and whitespace never enter.
 IF token COLLATE "C" !~ '^[-0-9TZ:.+]+$' THEN
  RAISE EXCEPTION 'strict temporal token grammar required' USING ERRCODE='22023';
 END IF;
 IF kind='date' THEN
  IF length(token)<>10 OR token COLLATE "C" !~ '^[0-9]{4}-[0-9]{2}-[0-9]{2}$' THEN
   RAISE EXCEPTION 'strict Gregorian date token required' USING ERRCODE='22023';
  END IF;
 ELSIF kind='local' THEN
  IF token COLLATE "C" !~ '^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}([.][0-9]{1,6})?$' THEN
   RAISE EXCEPTION 'strict local timestamp token required' USING ERRCODE='22023';
  END IF;
 ELSE
  IF token COLLATE "C" !~ '^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}([.][0-9]{1,6})?(Z|[+-][0-9]{2}:[0-9]{2})$' THEN
   RAISE EXCEPTION 'strict known-offset instant token required' USING ERRCODE='22023';
  END IF;
  IF right(token,1)='Z' THEN
   suffix_length:=1;
  ELSE
   suffix_length:=6;
   offset_token:=right(token,6);
   IF offset_token='-00:00' OR substring(offset_token,2,2)::int>23
    OR substring(offset_token,5,2)::int>59 THEN
    RAISE EXCEPTION 'strict known minute offset required' USING ERRCODE='22023';
   END IF;
   offset_minutes:=(substring(offset_token,2,2)::int*60+substring(offset_token,5,2)::int)
    * CASE WHEN left(offset_token,1)='-' THEN -1 ELSE 1 END;
  END IF;
 END IF;
 year_value:=substring(token,1,4)::int;
 IF year_value=0 THEN
  RAISE EXCEPTION 'Gregorian year in selected range required' USING ERRCODE='22023';
 END IF;
 -- make_date validates the proleptic Gregorian day without a timestamp parser.
 calendar_value:=make_date(year_value,substring(token,6,2)::int,substring(token,9,2)::int);
 IF kind='date' THEN RETURN token; END IF;
 hour_value:=substring(token,12,2)::int;
 minute_value:=substring(token,15,2)::int;
 second_value:=substring(token,18,2)::int;
 IF hour_value>23 OR minute_value>59 OR second_value>59 THEN
  RAISE EXCEPTION 'strict temporal clock required' USING ERRCODE='22023';
 END IF;
 IF substring(token,20,1)='.' THEN
  fraction_text:=substring(token,21,length(token)-20-suffix_length);
 END IF;
 fraction_text:=rpad(fraction_text,6,'0');
 IF kind='local' THEN RETURN left(token,19)||'.'||fraction_text; END IF;

 -- Bounded integer calendar/clock arithmetic, including floor across the
 -- previous midnight. No timestamp casts, floating epoch, rounding or timezone.
 second_of_day:=hour_value*3600+minute_value*60+second_value-offset_minutes*60;
 day_delta:=second_of_day/86400;
 IF second_of_day<0 AND second_of_day%86400<>0 THEN day_delta:=day_delta-1; END IF;
 calendar_value:=calendar_value+day_delta;
 IF calendar_value<DATE '0001-01-01' OR calendar_value>DATE '9999-12-31' THEN
  RAISE EXCEPTION 'normalized UTC year in selected range required' USING ERRCODE='22023';
 END IF;
 second_of_day:=second_of_day-day_delta*86400;
 -- Build fixed-width text directly; DateStyle and host timezone have no input.
 canonical_date:=lpad(extract(year FROM calendar_value)::int::text,4,'0')||'-'
  ||lpad(extract(month FROM calendar_value)::int::text,2,'0')||'-'
  ||lpad(extract(day FROM calendar_value)::int::text,2,'0');
 RETURN canonical_date||'T'||lpad((second_of_day/3600)::text,2,'0')||':'
  ||lpad(((second_of_day%3600)/60)::text,2,'0')||':'
  ||lpad((second_of_day%60)::text,2,'0')||'.'||fraction_text||'Z';
EXCEPTION WHEN datetime_field_overflow OR invalid_datetime_format THEN
 RAISE EXCEPTION 'strict Gregorian temporal calendar required' USING ERRCODE='22023';
END;
$$;
REVOKE ALL ON FUNCTION truss.query_temporal_canonical_text(text,text) FROM PUBLIC;
