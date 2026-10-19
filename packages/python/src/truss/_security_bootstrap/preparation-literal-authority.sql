-- SPDX-License-Identifier: MIT OR Apache-2.0
-- Private literal-only current-check component; not a permit or production gate.
-- Trusted original source/installer/executable custody remains a premise.
-- Install this helper under the existing excluded runtime owner. Never SET ROLE.
CREATE FUNCTION truss.check_preparation_module_authority(packet pg_catalog.jsonb)
RETURNS pg_catalog.oid LANGUAGE plpgsql SECURITY DEFINER
SET search_path=pg_catalog,pg_temp SET lock_timeout='1ms' AS $$
DECLARE person pg_catalog.oid; requirement pg_catalog.jsonb; target pg_catalog.jsonb;
BEGIN
 person:=truss.runtime_person(false);target:=packet->'target';
 -- Record mutation retains the existing qualified record-owner writer rule.
 PERFORM truss.runtime_module_writer(target->>'documentId',target->>'moduleId');
 -- Interpreting a Field requires its declaration owner's reader rule. Changing
 -- its value does not invent a writer grant on that declaration module.
 FOR requirement IN SELECT value FROM jsonb_array_elements(packet->'readRequirements') LOOP
  IF NOT truss.runtime_can_read(requirement->'field'->>'documentId',requirement->'field'->>'moduleId') THEN
   RAISE EXCEPTION 'current Field declaration reader required' USING ERRCODE='42501';END IF;
 END LOOP;
 IF NOT truss.runtime_can_read(target->>'documentId',packet->'actionRoles'->'pin'->'identity'->>'module') THEN
  RAISE EXCEPTION 'current action declaration reader required' USING ERRCODE='42501';END IF;
 RETURN person;
END;
$$;
REVOKE ALL ON FUNCTION truss.check_preparation_module_authority(jsonb) FROM PUBLIC;

-- Install under the excluded privileged owner to acquire native catalog locks.
-- It invokes the exact runtime-owner helper above, preserving session_user.
CREATE FUNCTION truss.check_preparation_literal_authority(original_anchor pg_catalog.int4,original_nonce pg_catalog.uuid)
RETURNS pg_catalog.jsonb LANGUAGE plpgsql SECURITY DEFINER
SET search_path=pg_catalog,pg_temp SET lock_timeout='1ms' SET bytea_output='hex' AS $$
DECLARE observation pg_catalog.jsonb; packet pg_catalog.jsonb; producer pg_catalog.jsonb;
 claim record; program truss.preparation_program_registration%ROWTYPE;
 family truss.action_family_registration%ROWTYPE; subject truss.action_subject_binding%ROWTYPE;
 requirement pg_catalog.jsonb; field pg_catalog.jsonb; rule pg_catalog.jsonb; configured pg_catalog.jsonb;
 selected_role record; person pg_catalog.oid; relation_name pg_catalog.text;
 expected_roles pg_catalog.bytea[]; role_index pg_catalog.int4; role_match pg_catalog.bool:=false;
 needed_actions pg_catalog.text[]:='{}'; action pg_catalog.text; witness pg_catalog.jsonb; subject_mapping pg_catalog.jsonb;
BEGIN
 -- Home prelocks precede private claim/source reads and policy/role cuts.
 LOCK TABLE ONLY truss.action_family_registration,truss.action_subject_binding,
  truss.action_role_binding IN ACCESS SHARE MODE NOWAIT;
 observation:=truss.observe_preparation_bridge(original_anchor,original_nonce);
 IF observation->'sourceAttachment' IS NULL OR observation->'sourceAttachment'='null'::jsonb THEN
  RAISE EXCEPTION 'source-aware original program required' USING ERRCODE='55000';END IF;
 SELECT * INTO STRICT claim FROM umf_security.require_preparation_data_claim(original_anchor,original_nonce);
 FOR relation_name IN SELECT unnest(ARRAY['truss.action_family_registration','truss.action_subject_binding','truss.action_role_binding']) LOOP
  IF NOT EXISTS(SELECT 1 FROM pg_catalog.pg_locks l WHERE l.locktype='relation' AND l.pid=claim.data_pid
   AND l.database=(SELECT oid FROM pg_database WHERE datname=current_database())
   AND l.relation=to_regclass(relation_name) AND l.mode='ShareLock' AND l.granted) THEN
   RAISE EXCEPTION 'original D action mapping cuts required' USING ERRCODE='55000';END IF;
 END LOOP;
 PERFORM truss.acquire_preparation_authority_lock();
 packet:=convert_from(decode(observation->'sourceAttachment'->>'packetHex','hex'),'UTF8')::jsonb;
 producer:=convert_from(decode(observation->'sourceAttachment'->>'producerHex','hex'),'UTF8')::jsonb;
 IF packet->>'protocol' IS DISTINCT FROM 'truss.preparation-source-obligations/0.1-candidate'
  OR packet->>'nativeProfile' IS DISTINCT FROM 'truss.preparation.literal-rbac/0.1-candidate'
  OR packet->'authority' IS DISTINCT FROM 'false'::jsonb OR packet->'complete' IS DISTINCT FROM 'false'::jsonb
  OR producer->>'umfSource' IS DISTINCT FROM '98ee88f193f5d70ccf21bd78ef6c37fffddc5eab'
  OR producer->>'manifestSha256' IS DISTINCT FROM '968267dd04f8ee05e439ec9d94580813b73f3eca50d8762d6999f9ed8441f7ab'
  OR producer->>'weftNativeSha256' IS DISTINCT FROM '2f91cbd5de07f04492d6fdbd964bf86cce84245adc18cd6debe3c17f61ef6843'
  OR packet->'actionRoles'->'personRequired' IS DISTINCT FROM 'true'::jsonb
  OR packet->'actionRoles'->'profile' IS DISTINCT FROM '{"id":"umf.actions.roles","version":"1"}'::jsonb
  OR packet->'nativeObligations'->0->>'kind' IS DISTINCT FROM 'literal-policy'
  OR packet->'nativeObligations'->0->>'status' IS DISTINCT FROM 'lowered-source'
  OR packet->'nativeObligations'->1->>'status' IS DISTINCT FROM 'required' THEN
  RAISE EXCEPTION 'original selected literal source profile required' USING ERRCODE='0A000';END IF;
 SELECT * INTO STRICT program FROM ONLY truss.preparation_program_registration WHERE program_id=claim.program_id;
 SELECT value INTO STRICT configured FROM jsonb_array_elements(
  (convert_from(program.original_configuration,'UTF8')::jsonb)->'actions')
  WHERE value->'pin'=packet->'actionRoles'->'pin';
 SELECT b.* INTO subject FROM ONLY truss.action_subject_binding b
  JOIN pg_catalog.pg_roles r ON r.oid=b.role_oid
  WHERE r.rolname=session_user AND b.subject_kind='human'
   AND b.authentication_profile='truss.local-scram/0.1'
   AND b.installation_id=(SELECT installation_id FROM truss.catalog_runtime_installation WHERE singleton);
 IF NOT FOUND THEN RAISE EXCEPTION 'current enrolled human required' USING ERRCODE='42501';END IF;
 -- Native human identity and the original issued UMF codec witness are
 -- checked separately. This is correspondence, not logical Subject existence.
 person:=truss.check_preparation_module_authority(packet);
 IF person IS DISTINCT FROM subject.role_oid OR person IS DISTINCT FROM
  (SELECT data_role_oid FROM truss.preparation_attempt_anchor WHERE anchor_id=original_anchor AND anchor_nonce=original_nonce) THEN
  RAISE EXCEPTION 'original native authenticated person required' USING ERRCODE='42501';END IF;
 IF producer->'subjectWitness'->>'version' IS DISTINCT FROM 'truss.preparation-native-subject-key/0.1-candidate' THEN
  RAISE EXCEPTION 'original native Subject codec witness required' USING ERRCODE='55000';END IF;
 SELECT value INTO STRICT witness FROM jsonb_array_elements(
  (producer->'subjectWitness'->>'originalOwnerResultUtf8')::jsonb)
  WHERE value->'native'->>'actorOid'=person::text;
 subject_mapping:=(packet->'original'->'subjectMapping'->>'utf8')::jsonb;
 IF witness->'native' IS DISTINCT FROM jsonb_build_object('actorOid',person::text,
   'installationId',subject.installation_id::text,'principalHex',encode(subject.principal_identity,'hex'),
   'kind',subject.subject_kind,'authenticationProfile',subject.authentication_profile)
  OR witness->'sourcePins' IS DISTINCT FROM jsonb_build_object(
   'subjectMapping',packet->'original'->'subjectMapping'->>'sha256','coreClosure',packet->'original'->'coreClosure'->>'sha256')
  OR witness->'original'->'authority' IS DISTINCT FROM 'false'::jsonb
  OR witness->'original'->'receipt'->>'operation' IS DISTINCT FROM 'encode-core-key-tuple'
  OR witness->'original'->'receipt'->>'version' IS DISTINCT FROM '3.0.0'
  OR witness->'original'->'receipt'->>'profile' IS DISTINCT FROM 'umf-key-tuple-v1'
  OR witness->'original'->'receipt'->'values' IS DISTINCT FROM witness->'original'->'key'
  OR witness->'original'->'receipt'->'identity' IS DISTINCT FROM jsonb_build_object(
   'module',subject_mapping->'type'->>'moduleId','element',subject_mapping->'type'->>'elementId','key',subject_mapping->>'keyId')
  OR witness->'original'->'receipt'->'source'->>'id' IS DISTINCT FROM subject_mapping->'type'->>'documentId' THEN
  RAISE EXCEPTION 'exact current native Subject and original codec correspondence required' USING ERRCODE='55000';END IF;

 SELECT * INTO STRICT family FROM ONLY truss.action_family_registration f
  WHERE f.family_identity=decode(producer->>'nativeFamilyHex','hex')
   AND f.store_control_id=program.store_control_id
   AND f.store_identity=(SELECT store_identity FROM truss.action_store_registration WHERE control_id=program.store_control_id)
   AND f.installation_id=subject.installation_id;
 IF convert_from(family.original_action_pin,'UTF8')::jsonb IS DISTINCT FROM packet->'actionRoles'->'pin'
  OR convert_from(family.original_model_artifact,'UTF8')::jsonb IS DISTINCT FROM configured->'snapshot'
  OR convert_from(family.original_preparation_artifact,'UTF8')::jsonb IS DISTINCT FROM configured->'preparation'
  OR family.person_required IS NOT TRUE OR family.profile_id<>'umf.actions.roles' OR family.profile_version<>'1' THEN
  RAISE EXCEPTION 'exact original action declaration correspondence required' USING ERRCODE='55000';END IF;
 SELECT array_agg(decode(value,'hex') ORDER BY ord) INTO expected_roles
  FROM jsonb_array_elements_text(producer->'nativeRoleHex') WITH ORDINALITY AS x(value,ord);
 IF family.declared_roles IS DISTINCT FROM expected_roles OR cardinality(expected_roles) NOT BETWEEN 1 AND 64
  OR jsonb_array_length(packet->'actionRoles'->'roles') IS DISTINCT FROM cardinality(expected_roles) THEN
  RAISE EXCEPTION 'complete original declared role correspondence required' USING ERRCODE='55000';END IF;
 IF (SELECT count(*) FROM ONLY truss.action_role_binding WHERE family_registration_id=family.family_registration_id)
   IS DISTINCT FROM cardinality(expected_roles)::bigint THEN
  RAISE EXCEPTION 'complete original role binding population required' USING ERRCODE='55000';END IF;
 FOR role_index IN 1..cardinality(expected_roles) LOOP
  SELECT b.*,r.rolcanlogin,r.rolsuper,r.rolcreaterole,r.rolcreatedb,r.rolreplication,r.rolbypassrls,r.oid AS resolved
   INTO STRICT selected_role FROM ONLY truss.action_role_binding b LEFT JOIN pg_catalog.pg_roles r ON r.oid=b.native_role_oid
   WHERE b.family_registration_id=family.family_registration_id AND b.role_identity=expected_roles[role_index];
  IF selected_role.resolved IS NULL OR selected_role.rolcanlogin OR selected_role.rolsuper OR selected_role.rolcreaterole
   OR selected_role.rolcreatedb OR selected_role.rolreplication OR selected_role.rolbypassrls
   OR selected_role.original_action_pin IS DISTINCT FROM family.original_action_pin
   OR selected_role.store_identity IS DISTINCT FROM family.store_identity OR selected_role.family_identity IS DISTINCT FROM family.family_identity
   OR selected_role.installation_id IS DISTINCT FROM family.installation_id
   OR selected_role.profile_id<>'umf.actions.roles' OR selected_role.profile_version<>'1'
   OR pg_has_role(selected_role.native_role_oid,(SELECT owner_oid FROM truss.catalog_runtime_installation WHERE singleton),'MEMBER') THEN
   RAISE EXCEPTION 'every original native role mapping must resolve safely' USING ERRCODE='55000';END IF;
  role_match:=role_match OR EXISTS(WITH RECURSIVE memberships(oid) AS (
   SELECT person UNION SELECT m.roleid FROM pg_catalog.pg_auth_members m JOIN memberships p ON m.member=p.oid)
   SELECT 1 FROM memberships WHERE oid=selected_role.native_role_oid);
 END LOOP;
 IF NOT role_match THEN RAISE EXCEPTION 'current original action role required' USING ERRCODE='42501';END IF;
 FOR field IN SELECT value FROM jsonb_array_elements(packet->'nativeFields') LOOP
  IF NOT EXISTS(SELECT 1 FROM truss.prop_def p JOIN truss.type_def t ON t.type_id=p.type_id
   WHERE p.prop_id=(field->>'propertyId')::int AND t.type_id=(field->>'typeId')::int
    AND t.document_id=packet->'target'->>'documentId' AND t.module=packet->'target'->>'moduleId'
    AND t.element=packet->'target'->>'elementId' AND p.element=field->'field'->>'elementId'
    AND p.declaration_module=field->'field'->>'moduleId'
    AND field->'field'->>'documentId'=packet->'target'->>'documentId'
    AND p.retired_rev IS NULL AND t.retired_rev IS NULL) THEN
   RAISE EXCEPTION 'original native typed Field correspondence required' USING ERRCODE='55000';END IF;
 END LOOP;
 FOR requirement IN SELECT value FROM jsonb_array_elements(packet->'readRequirements') LOOP
  IF requirement->>'disposition' IS DISTINCT FROM 'original' THEN
   RAISE EXCEPTION 'original Field disclosure required' USING ERRCODE='0A000';END IF;
  needed_actions:=array_append(needed_actions,requirement->>'action');
 END LOOP;
 FOR requirement IN SELECT value FROM jsonb_array_elements(packet->'writeRequirements') LOOP
  needed_actions:=needed_actions||ARRAY[requirement->>'objectAction',requirement->>'fieldAction',requirement->>'originalReadAction'];
 END LOOP;
 FOR rule IN SELECT value FROM jsonb_array_elements(packet->'nativeObligations'->0->'rules') LOOP
  IF rule->>'effect' IS DISTINCT FROM 'permit' OR rule->'condition' IS DISTINCT FROM '{"op":"literal","value":true}'::jsonb
   OR rule->'target' IS DISTINCT FROM jsonb_build_array(packet->'target') THEN
   RAISE EXCEPTION 'exact original literal permit rules required' USING ERRCODE='0A000';END IF;
 END LOOP;
 FOREACH action IN ARRAY needed_actions LOOP
  IF action IS NULL OR NOT EXISTS(SELECT 1 FROM jsonb_array_elements(packet->'nativeObligations'->0->'rules') r
   WHERE r->'actions' ? action) THEN
   RAISE EXCEPTION 'separate original read/object/Field literal action required' USING ERRCODE='42501';END IF;
 END LOOP;
 IF truss.observe_preparation_bridge(original_anchor,original_nonce) IS DISTINCT FROM observation THEN
  RAISE EXCEPTION 'original source/claim/cut correspondence changed' USING ERRCODE='55000';END IF;
 FOR relation_name IN SELECT unnest(ARRAY['truss.action_family_registration','truss.action_subject_binding','truss.action_role_binding']) LOOP
  IF NOT EXISTS(SELECT 1 FROM pg_catalog.pg_locks l WHERE l.locktype='relation' AND l.pid=claim.data_pid
   AND l.database=(SELECT oid FROM pg_database WHERE datname=current_database())
   AND l.relation=to_regclass(relation_name) AND l.mode='ShareLock' AND l.granted) THEN
   RAISE EXCEPTION 'original D mapping cut ended' USING ERRCODE='55000';END IF;
 END LOOP;
 RETURN jsonb_build_object('currentChecksPassed',true,'personOid',person::text,'programId',claim.program_id::text,
  'authority',false,'securityReady',false,'subjectKeyCorrespondence',witness->'original',
  'remainingNativeObligations',packet->'nativeObligations'->1);
END;
$$;
REVOKE ALL ON FUNCTION truss.check_preparation_literal_authority(int4,uuid) FROM PUBLIC;
