"""Derive versioned private capture from the original epoch admission source."""
from pathlib import Path
import sys
root=Path(__file__).resolve().parents[1]
source=(root/'packages/postgresql/native/operation-epoch-context-admission.sql').read_text()
source=source.replace('runtime_admit_operation_with_epoch_context','runtime_admit_operation_with_configuration_context')
source=source.replace('expected_incarnation text\n','expected_incarnation text, configuration_profile_bytes bytea\n')
source=source.replace('  epoch_capture record;','  epoch_capture record;\n  configuration_sizes record;\n  captured_configuration truss.installation_admission%ROWTYPE;')
anchor='  native_xid := pg_current_xact_id();'
capture="""  IF configuration_profile_bytes IS NULL OR octet_length(configuration_profile_bytes) NOT BETWEEN 1 AND 65536 THEN
    RAISE EXCEPTION 'original configuration profile bounds' USING ERRCODE='22023';
  END IF;
  SELECT octet_length(a.configuration_bytes)::bigint AS configuration,
    octet_length(a.selected_binding_bytes)::bigint AS binding,
    octet_length(a.installed_inventory_bytes)::bigint AS inventory
    INTO configuration_sizes FROM truss.installation_admission a WHERE a.head_id=1;
  IF NOT FOUND OR configuration_sizes.configuration<1 OR configuration_sizes.binding<1
    OR configuration_sizes.inventory<1 OR configuration_sizes.configuration+configuration_sizes.binding+configuration_sizes.inventory>16777216 THEN
    RAISE EXCEPTION 'original pre-effect configuration bounds' USING ERRCODE='55000';
  END IF;
  total_bytes:=total_bytes+configuration_sizes.configuration+configuration_sizes.binding+configuration_sizes.inventory+octet_length(configuration_profile_bytes);
  IF total_bytes>20971520 THEN
    RAISE EXCEPTION 'configuration operation aggregate bounds' USING ERRCODE='54000';
  END IF;
  SELECT a.* INTO STRICT captured_configuration FROM truss.installation_admission a WHERE a.head_id=1;
  IF captured_configuration.installation_id_utf8 IS DISTINCT FROM convert_to(epoch_capture.installation_id,'UTF8')
    OR captured_configuration.source_epoch_utf8 IS DISTINCT FROM convert_to(epoch_capture.source_epoch,'UTF8')
    OR captured_configuration.configuration_generation<0
    OR captured_configuration.key_reuse NOT IN ('forbid','allow')
    OR captured_configuration.journal_mode NOT IN ('engine','trigger') THEN
    RAISE EXCEPTION 'original pre-effect configuration correspondence' USING ERRCODE='55000';
  END IF;
"""
assert source.count(anchor)==1
source=source.replace(anchor,capture+anchor)
source=source.replace('  INSERT INTO truss.row_home_operation(',"  IF total_bytes+octet_length(native_context)>20971520 THEN\n    RAISE EXCEPTION 'configuration encoded operation aggregate bounds' USING ERRCODE='54000';\n  END IF;\n  INSERT INTO truss.row_home_operation(")
anchor='  RETURN QUERY SELECT native_xid::text,next_ordinal::text,encode(native_context,\'hex\');'
insert="""  INSERT INTO truss.operation_configuration(original_writer_xid,operation_ordinal,
    installation_id,source_epoch,target_incarnation,configuration_generation,
    key_reuse,journal_mode,original_context_sha256,admission_profile_bytes,
    configuration_bytes,selected_binding_bytes,installed_inventory_bytes)
  VALUES(native_xid,next_ordinal,epoch_capture.installation_id,epoch_capture.source_epoch,
    epoch_capture.target_incarnation,captured_configuration.configuration_generation,
    captured_configuration.key_reuse,captured_configuration.journal_mode,sha256(native_context),
    configuration_profile_bytes,captured_configuration.configuration_bytes,
    captured_configuration.selected_binding_bytes,captured_configuration.installed_inventory_bytes);
"""
assert source.count(anchor)==1
source=source.replace(anchor,insert+anchor)
source=source.replace('bytea,text,text,text) FROM PUBLIC','bytea,text,text,text,bytea) FROM PUBLIC')
source='-- Private pre-effect configuration capture; registered meaning/installed authority remain unqualified.\n'+source
path=root/'packages/postgresql/native/operation-configuration-context-admission.sql'
if '--check' in sys.argv:
    assert path.read_text()==source,'stale derived admission source'
else:
    path.write_text(source)
print('Original lock/order/actor context preserved; pre-effect capsule added.')
