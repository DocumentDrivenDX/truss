#!/usr/bin/env python3
"""Enforce the current Python source map; does not execute inspected source.

TypeScript, native SQL, reflection and runtime object visibility require separate
checks/review. Cycle checks cover lexically eager imports, not runtime call
analysis: top-level calls or decorators can execute deferred function imports.
A pass is explicitly Python-only, not architecture qualification.
"""
import argparse
import ast
import json
from pathlib import Path
import sys

# Imports are owned by the source module, including inside functions. New modules
# require a reviewed map entry; there is no directory-wide exception or baseline.
ALLOWED = {
    "access": {"hashlib","umf_access.native_program","__future__","collections.abc","contextlib","datetime","time","typing","json","decimal","pydantic","umf_access.adoption","umf_access.engine_catalog","umf_access.reviewed","umf_access.pages","umf_access.codec_support","umf_access.postgres_read","truss.execution","truss.query"},
    # Original-context/native correspondence data only; no witness admission.
    '_native_model_correspondence': {'dataclasses','hashlib','json','truss._native_source_observation','truss._owner_evidence_json','weft'},
    # Reviewed same-context association definition data; no permit or issuer.
    '_native_graph_correspondence': {'dataclasses','hashlib','json','truss._native_model_correspondence','truss._owner_evidence_json','weft'},
    # Reviewed complete population composition; original context stays held.
    '_current_disclosure_context_capture': {'dataclasses','json','truss._current_query_sources','truss._current_disclosure_originals','truss._current_disclosure_facts','truss._native_graph_correspondence','truss._current_query_evaluation','truss._owner_evidence_json','weft.weft'},
    # Reviewed stock-cursor metadata observer; no authority admission.
    '_native_source_observation': {'dataclasses','hashlib','importlib.resources','json','truss._owner_evidence_json','truss._security_catalog_assessment','truss._security_catalog_subject_installation','truss.catalog_runtime'},
    # Native source descriptor data only; no native observation or permission.
    '_native_source_descriptor': {'dataclasses','hashlib','json','re','truss._owner_evidence_json'},
    # Reviewed disclosure consumer: explicit held computation and transport edges.
    '_current_disclosure_computation': {'contextlib','hashlib','importlib.resources','json','shutil','subprocess','time','truss._current_disclosure_pipe'},
    '_current_disclosure_evaluation': {'truss._current_disclosure_context_capture','dataclasses','hashlib','time','truss._current_disclosure_computation','truss._current_disclosure_originals','truss._current_disclosure_session','truss._current_disclosure_stage','truss._current_disclosure_wire','truss._current_query_evaluation','truss._current_query_sources','truss._owner_evidence_json','weft.weft'},
    '_current_disclosure_originals': {'dataclasses','hashlib','json','pathlib','truss._current_disclosure_computation','truss._current_query_originals','truss._owner_evidence_json','weft.weft'},
    '_current_disclosure_pipe': {'truss._current_query_pipe'},
    '_current_disclosure_session': {'truss._current_disclosure_pipe','truss._current_disclosure_wire','truss._current_query_evaluation','truss._owner_evidence_json'},
    '_current_disclosure_stage': {'dataclasses','hashlib','json','psycopg','psycopg.rows','truss._current_disclosure_wire','truss._current_query_evaluation','truss._owner_evidence_json','truss._security_catalog_subject_installation','uuid'},
    '_current_disclosure_wire': {'decimal','hashlib','json','struct','truss._current_disclosure_pipe','truss._current_query_sources','truss._owner_evidence_json'},
    'current_disclosure': {'dataclasses','truss._current_disclosure_originals','truss._current_query_sources','truss.current_query','truss.execution','truss.psycopg_host','typing'},

    # Current-policy query composition: explicit orchestration and installer edges.
    '_current_query_computation': {'contextlib','hashlib','importlib.resources','json','shutil','subprocess','time','truss._current_query_pipe'},
    '_current_query_evaluation': {'hashlib','json','time','truss._current_query_computation','truss._current_query_pipe','truss._owner_evidence_json','weft.weft'},
    '_current_disclosure_facts': {'base64','dataclasses','json','truss._current_query_originals','truss._current_query_pipe','truss._current_query_sources','truss._owner_evidence_json','truss._security_catalog_subject_installation','truss._umf_key_tuples'},
    '_current_query_facts': {'base64','dataclasses','json','truss._current_query_originals','truss._current_query_pipe','truss._current_query_sources','truss._owner_evidence_json','truss._security_catalog_subject_installation','truss._umf_key_tuples'},
    '_current_query_originals': {'dataclasses','hashlib','json','pathlib','re','truss._current_query_computation','truss._owner_evidence_json','truss._umf_key_tuples','weft.weft'},
    '_current_query_pipe': {'decimal','json','os','pathlib','selectors','struct','subprocess','threading','time'},
    '_current_query_protection': {'json','psycopg','re','truss._current_query_sources','truss._current_query_subjects','truss._installation_privileges','truss.catalog_runtime','truss.current_query','truss.execution','truss.psycopg_host'},
    '_current_query_runtime': {'subprocess','truss._current_query_evaluation','truss._current_query_facts','truss._current_query_pipe','truss._current_query_protection','truss._current_query_sources','truss._current_query_stage','truss._current_query_subjects','truss._installation_privileges','truss._owner_evidence_json','truss._security_catalog_subject_installation','truss.catalog_runtime','truss.execution','truss.psycopg_host','truss.query','truss._current_disclosure_evaluation','truss._current_disclosure_originals','truss._current_query_originals','truss.current_disclosure'},
    '_current_query_sources': {'dataclasses','hashlib','importlib.resources','json','struct','truss._current_query_originals','truss._current_query_pipe','truss._installation_privileges','truss._security_catalog_assessment','truss._security_catalog_subject_installation','truss._security_graph_source','truss.catalog_runtime','truss.execution','truss.psycopg_host','truss._current_disclosure_originals'},
    '_current_query_stage': {'hashlib','json','psycopg','psycopg.rows','re','truss._current_query_evaluation','truss._owner_evidence_json','truss.catalog_runtime','truss.query','uuid'},
    '_current_query_subjects': {'dataclasses','hashlib','json','psycopg','truss._current_query_pipe','truss._current_query_protection','truss._current_query_sources','truss._installation_privileges','truss._security_catalog_subject_installation','truss._umf_key_tuples','truss.catalog_runtime','truss.current_query','truss.execution','truss.psycopg_host'},
    'current_query': {'dataclasses','truss._current_query_originals','truss._current_query_protection','truss._current_query_sources','truss._current_query_subjects','truss.execution','truss.psycopg_host'},
    '_preparation_bridge_inventory': {'importlib.resources','truss._security_source_epoch_installation'},
    '_preparation_compiler_replay': {'dataclasses','hashlib','json','os','pathlib','subprocess','sys','truss._preparation_program','truss.weft'},
    '_preparation_selection': {'dataclasses','psycopg','psycopg.rows','psycopg.types.string','truss._preparation_compiler_replay','truss._preparation_program','uuid'},
    '_preparation_sources': {'dataclasses','hashlib','importlib.resources','json','pathlib','psycopg','shutil','subprocess','tempfile','time','truss._action_identity_codec','truss._preparation_compiler_replay','truss._preparation_program','truss._preparation_source_epoch','truss._preparation_sources_release','truss.execution','truss.psycopg_host','truss.weft'},
    '_preparation_sources_release': {},

    '_action_authority_observation': {'json','truss._action_store','dataclasses','truss.bulk_action_gateway','truss._action_identity_codec','truss._security_preparation_authority','truss._security_catalog_subject_installation'},
    '_action_role_installation': {'hashlib','importlib.resources','json','truss._action_store','dataclasses','psycopg','truss.bulk_action_gateway','truss._action_identity_codec','truss.psycopg_host','truss.execution','truss.catalog_runtime','truss._installation_privileges','truss._security_catalog_subject_installation'},
    'bulk_action_gateway': {'dataclasses','hashlib','inspect','threading','truss.weft','truss._bulk_set_values','truss._action_identity_codec'},
    '_bulk_set_values': {'decimal','re'},
    '_action_store': {'dataclasses','hashlib','importlib.resources','json','psycopg','truss.execution','truss.psycopg_host','truss.catalog_runtime','truss._preparation_source_epoch','truss._action_identity_codec','truss._security_catalog_subject_installation','truss._current_query_protection'},
    '_preparation_program': {'dataclasses','hashlib','json','re','importlib.resources','psycopg','truss.weft','truss._action_store','truss._preparation_source_epoch','truss.psycopg_host','truss.execution'},
    '_preparation_data_claim': {'dataclasses','uuid','truss._engine_preparation','truss._security_catalog_subject_installation','truss.catalog_runtime','truss.execution','truss.psycopg_host'},
    '_action_identity_codec': {'json'},
    '_action_subject_installation': {'dataclasses','hashlib','importlib.resources','psycopg','truss.psycopg_host','truss.execution','truss.catalog_runtime','truss._installation_privileges','truss._security_catalog_subject_installation','truss._current_query_protection'},
    '_scram_preparation_login': {'dataclasses','psycopg'},
    'catalog_preparation': {'hashlib','importlib.resources','json','truss.preparation','truss._catalog_source_reference','truss._catalog_support','truss._catalog_report_semantics'},
    'catalog_report_sources': {'base64','dataclasses','decimal','hashlib','json'},
    '_catalog_source_reference': set(),
    '_security_preparation_authority': {'dataclasses','hashlib','importlib.resources','uuid','psycopg','truss.execution','truss.psycopg_host','truss.catalog_runtime','truss._installation_privileges','truss._security_catalog_subject_installation','truss._current_query_protection'},
    '_security_catalog_read_cut_installation': {'dataclasses','hashlib','importlib.resources','psycopg','truss.execution','truss.psycopg_host','truss.catalog_runtime','truss._installation_privileges','truss._security_catalog_subject_installation','truss._current_query_protection'},
    '_security_catalog_subject_helpers': {'json'},
    '_security_catalog_subject_installation': {'dataclasses','hashlib','importlib.resources','json','psycopg','truss.execution','truss.psycopg_host','truss.catalog_runtime','truss._installation_privileges','truss._security_catalog_source_installation','truss._security_catalog_assessment','truss._security_catalog_subject_helpers','truss._current_query_protection'},
    '_security_graph_subject_installation': {'truss._security_relationship_source','dataclasses','hashlib','importlib.resources','json','psycopg','truss.execution','truss.psycopg_host','truss.catalog_runtime','truss._installation_privileges','truss._security_catalog_subject_installation','truss._security_catalog_assessment','truss._security_graph_source','truss._owner_evidence_json','truss._current_query_protection'},
    '_security_graph_epoch_read': {'truss._security_guarded_source','dataclasses','hashlib','importlib.resources','psycopg','truss.execution','truss.psycopg_host','truss.catalog_runtime','truss._installation_privileges','truss._security_catalog_subject_installation','truss._security_graph_source','truss._security_catalog_assessment','truss._psycopg_epoch_cut','truss._owner_evidence_json','truss._current_query_protection'},
    '_security_relationship_epoch_read': {'truss._security_guarded_source','dataclasses','hashlib','importlib.resources','psycopg','truss.execution','truss.psycopg_host','truss.catalog_runtime','truss._installation_privileges','truss._security_catalog_subject_installation','truss._security_relationship_source','truss._security_catalog_assessment','truss._psycopg_epoch_cut','truss._owner_evidence_json','truss._current_query_protection'},
    '_security_relational_source': {'truss._security_guarded_source','truss._owner_evidence_json'},
    '_security_relationship_source': {'dataclasses','hashlib','truss._owner_evidence_json','truss._security_guarded_source'},
    '_security_guarded_source': {'dataclasses','hashlib','truss._owner_evidence_json'},
    '_security_graph_source': {'truss._security_guarded_source','dataclasses','hashlib','json','psycopg','truss._owner_evidence_json','truss._security_catalog_assessment'},
    '_security_catalog_source_binding': {'truss._security_relationship_source','truss._security_guarded_source','truss._security_graph_source','dataclasses','hashlib','json','truss._security_mapping','truss._security_source_epoch_installation','truss._psycopg_fact_cut','truss._psycopg_epoch_cut'},
    '_security_catalog_source_epoch': {'truss._security_relationship_source','truss._security_graph_source','dataclasses','hashlib','json','truss.execution','truss.psycopg_host','truss.catalog_runtime','truss._installation_privileges','truss._security_catalog_source_installation','truss._security_catalog_assessment','truss._security_source_epoch_installation','truss._security_catalog_source_binding','truss._psycopg_epoch_cut','truss._psycopg_fact_cut'},
    '_security_source_epoch_installation': {'dataclasses','hashlib','importlib.resources','json','truss.execution','truss.psycopg_host','truss.catalog_runtime','truss._installation_privileges','truss._psycopg_epoch_cut'},
    '_psycopg_subject_observation': {'dataclasses','hashlib','inspect','json','truss._owner_evidence_json','truss.psycopg_host','psycopg','truss._umf_key_tuples','truss._psycopg_fact_cut'},
    'query': {'datetime','truss.contracts','decimal','dataclasses','typing'},
    '_query_runtime': {'base64','datetime','truss.contracts','hashlib','json','types','typing','decimal','re','weft','psycopg','psycopg.rows','truss.psycopg_host','truss.execution','truss.query'},
    '_umf_keys_release': set(),
    '_umf_keys08_release': set(),
    '_umf_key_tuples': {'base64','truss.contracts','decimal','dataclasses','hashlib','importlib.resources','json','shutil','truss.preparation','truss._owner_evidence_json','truss._umf_keys_release','truss._umf_keys08_release','subprocess','time'},
    '_catalog_definition_source': {'json','decimal','truss._owner_evidence_json'},
    # Group preparation decodes the shared catalog reference contract; no catalog runtime dependency.
    '_group_runtime': {'truss.catalog_view','truss._receipt_position','typing','dataclasses','hashlib','base64','json','truss.contracts','truss.execution','truss.groups','truss.preparation','truss._umf_key_tuples'},
    '_preparation_seal_installation': {'dataclasses','hashlib','importlib.resources','psycopg','truss.execution','truss.psycopg_host','truss.catalog_runtime','truss._preparation_source_epoch'},
    '_preparation_source_epoch': {'dataclasses','hashlib','importlib.resources','json','re','truss.catalog_runtime','truss.execution','truss.psycopg_host','truss._installation_privileges','truss._security_catalog_assessment','truss._security_source_epoch_installation','truss._psycopg_epoch_cut'},
    '_preparation_catalog_cut': {'dataclasses','hashlib','importlib.resources','psycopg','truss.execution','truss.psycopg_host','truss.catalog_runtime','truss._installation_privileges','truss._security_catalog_assessment','truss._security_catalog_subject_installation','truss._current_query_protection'},
    '_engine_preparation': {'truss._scram_preparation_login','dataclasses','threading','inspect','psycopg','psycopg.rows','psycopg.types.string','truss.psycopg_host','truss._security_catalog_subject_installation','truss.engine_import','truss.execution'},
    'engine_import': {'dataclasses','truss._owned_import_runtime','__future__','typing','hashlib','truss.execution','truss.imports','truss.preparation','truss.catalog_runtime','truss._import_runtime','truss._group_runtime','truss.psycopg_host','psycopg'},
    '_owned_import_runtime': {'base64','json','hashlib','uuid','truss.contracts','truss.execution','truss.imports','truss.groups','truss._group_runtime','truss._import_runtime','truss._acceptance_json','truss._catalog_report_semantics','truss.psycopg_host','truss.preparation'},
    '_import_runtime': {'contextlib','base64','json','hashlib','uuid','truss.contracts','truss.execution','truss.imports','truss.groups','truss._group_runtime','truss._acceptance_json','truss._umf_key_tuples','truss.psycopg_host','truss.preparation','truss._catalog_report_semantics'},
    'import_runtime': {'truss.groups','truss.contracts','truss.imports','truss._group_runtime','dataclasses'},
    'catalog_results': {'dataclasses','typing'},
    'capability_contracts': {'truss.traversal','decimal','truss.query','truss.import_source','truss.history','typing','truss.contracts','truss.execution','truss.preparation','truss.catalog_view','truss.reader_catalog','truss.object_read','truss.edge_read','truss.imports','truss.import_runtime','truss.groups','truss.feed','truss.receipt_visibility','truss.catalog_results'},
    'capabilities': {'truss.traversal','decimal','truss.query','truss.import_source','truss.history','__future__','dataclasses','typing','truss.contracts','truss.execution','truss.preparation','truss.catalog_view','truss.reader_catalog','truss.object_read','truss.edge_read','truss.imports','truss.import_runtime','truss.groups','truss.feed','truss.receipt_visibility','truss.catalog_results','truss.capability_contracts'},
    'import_source': {'dataclasses','typing'},
    'history': {'dataclasses','typing'},
    'feed': {'dataclasses','typing'},
    'receipt_visibility': {'truss.contracts','dataclasses','typing'},
    'traversal': {'dataclasses','typing','truss.catalog_view','truss.object_read'},
    'edge_read': {'truss.contracts','dataclasses','typing'},
    'object_read': {'truss.contracts','truss.groups','dataclasses','typing'},
    'catalog_view': {'dataclasses','typing','truss.contracts'},
    '_catalog_view_build': {'base64','dataclasses','hashlib','json','truss.contracts','truss.catalog_view','truss._catalog_definition_source','truss._owner_evidence_json'},
    'reader_catalog': {'dataclasses','typing'},
    'catalog_runtime': {'truss._owned_import_runtime','truss._ownership_migration','truss.catalog_preparation','truss._catalog_source_reference','truss.traversal','decimal','truss.query','truss._query_runtime','truss.import_source','truss.history','truss.catalog_results','truss.capabilities','truss.feed','truss._import_runtime','truss.imports','truss.import_runtime','truss.receipt_visibility','truss._receipt_position','truss.edge_read','truss._umf_key_tuples','base64','truss.reader_catalog','typing','truss.groups','truss._group_runtime','truss.object_read','truss.catalog_view','truss.contracts','truss._catalog_view_build','__future__','dataclasses','hashlib','importlib.resources','json','re','uuid','threading','functools','psycopg','psycopg.types.string','psycopg.types.bool','psycopg.types.numeric','truss.assembly_contracts','truss.execution','truss.psycopg_host','truss.preparation','truss._catalog_support','truss._catalog_report_semantics','truss._installation_privileges','truss._acceptance_json','truss._owner_evidence_json','truss._current_query_protection','truss._current_query_runtime','truss.current_query','truss.current_disclosure'},
    '_ownership_migration': {'psycopg'},
    '_installation_privileges': {'dataclasses','psycopg','truss.execution','truss.psycopg_host'},
    '_runtime_profile': {'json', 'importlib.resources'},
    'psycopg_host': {'inspect', 'truss._operation_ordinal', 'truss._runtime_profile', 'dataclasses', 'threading', 'time', 'uuid', 'weakref', 're', 'psycopg', 'psycopg.rows', 'psycopg.types.string', 'truss.execution'},
    '_psycopg_census_cut': {'inspect','truss._psycopg_epoch_cut','truss._psycopg_source_census'},
    '_psycopg_source_census': {'dataclasses','hashlib','importlib.resources','re','truss.execution','truss.psycopg_host','truss.catalog_runtime'},
    '_psycopg_epoch_cut': {'dataclasses', 'hashlib', 'truss.psycopg_host', 'psycopg.types.string'},
    '_psycopg_dependency_fact_cut': {'dataclasses', 'json', 'psycopg', 'truss._psycopg_epoch_cut', 'truss._security_fact_coverage', 'truss._psycopg_fact_cut'},
    '_security_publication_registration': {'dataclasses','hashlib','importlib.resources','truss.execution','truss.psycopg_host','truss.catalog_runtime','truss._installation_privileges'},
    '_security_publication_settlement': {'dataclasses','hashlib','importlib.resources','truss.execution','truss.psycopg_host','truss.catalog_runtime','truss._installation_privileges'},
    '_security_data_writer_binding': {'hashlib'},
    '_core08_catalog_release': set(),
    '_core08_catalog_source': {'dataclasses','hashlib','importlib.resources','json','shutil','subprocess','truss._core08_catalog_release','truss.preparation','truss.weft'},
    '_security_catalog_mapping': {'json','hashlib'},
    '_security_catalog_assessment': {'json','hashlib','truss.catalog_runtime','truss.weft'},
    '_security_mapping': {'truss._security_catalog_mapping','truss._security_catalog_assessment','dataclasses','hashlib','inspect','truss.weft','truss.execution','truss.psycopg_host','truss.catalog_runtime','truss._installation_privileges'},
    '_security_data_writer': {'dataclasses','inspect','truss.execution','truss.psycopg_host','truss.catalog_runtime','truss._installation_privileges','truss._security_data_writer_binding'},
    '_security_authority_change': {'dataclasses','hashlib','importlib.resources','inspect','truss.execution','truss.psycopg_host','truss.catalog_runtime','truss._installation_privileges'},
    '_security_catalog_source_installation': {'truss._security_relationship_source','truss._security_graph_source','truss._security_catalog_mapping','dataclasses','hashlib','importlib.resources','json','truss.execution','truss.psycopg_host','truss._security_mapping','truss._security_catalog_assessment','truss._installation_privileges','truss.catalog_runtime'},
    '_security_home_installation': {'dataclasses','hashlib','importlib.resources','psycopg','truss.execution','truss.psycopg_host','truss._installation_privileges','truss.catalog_runtime'},
    '_security_fact_coverage': {'dataclasses', 'hashlib', 'json'},
    '_psycopg_graph_scope': {'dataclasses', 'json', 'truss._psycopg_epoch_cut', 'psycopg.types.numeric', 'psycopg.types.string', 'psycopg.types.array'},
    '_psycopg_fact_cut': {'dataclasses', 'truss._psycopg_epoch_cut', 'psycopg'},
    '_native_attachment': set(),
    '_borrowed_host': {'io','socket','importlib.metadata','pg8000.native','pg8000.core','pg8000.converters','truss.host','truss._native_attachment','truss._native_pg8000','truss._native_driver_profile','truss._host_execution','truss._native_transactions','truss._native_arbitration','truss._host_control_custody','truss._host_session'},
    '_native_catalog_metadata': {'json','re','hashlib','importlib.resources','truss._acceptance_json'},
    '_native_epoch_acquisitions': {'dataclasses','truss._native_pg8000'},
    '_native_fresh_epoch_capture': {'dataclasses','truss._native_epoch_acquisitions','hashlib','re','struct','truss._native_admission_capture','truss._native_result_custody','truss._native_pg8000','truss._native_arbitration','truss._native_driver_profile','truss._native_deadline'},
    '_native_source_census': {'dataclasses','hashlib','re','struct','truss._native_pg8000','truss._native_arbitration','truss._native_result_custody','truss._native_driver_profile','truss._native_deadline'},
    '_native_operation_ordinals': {'truss._native_catalog_request','truss._native_catalog_capture','truss.preparation','truss._native_string_request','dataclasses','truss._operation_ordinal','truss._native_pg8000','truss._native_adoption','truss._native_admission_request','truss._native_admission_capture','truss._native_result_custody','truss._native_deadline','truss._native_driver_profile','pg8000.core'},
    '_startup_custody': {'dataclasses','threading','importlib.metadata','io','socket','pg8000','truss._native_driver_profile','truss._native_deadline'},
    '_native_bootstrap': {'dataclasses', 'threading', 'importlib.metadata', 'io', 'socket', 'pg8000', 'truss._native_pg8000', 'truss._host_control_custody', 'truss._native_result_custody', 'truss._native_deadline', 'truss._startup_custody','truss._native_driver_profile'},
    '_adoption_cancellation': {'threading'},
    'contracts': {'dataclasses', 'enum', 'types', 'typing'},
    'groups': {'dataclasses', 'typing', 'truss.contracts', 'truss.execution'},
    'imports': {'dataclasses', 'typing', 'truss.contracts', 'truss.execution'},
    '_installed_admission_inventory': {'dataclasses', 'hashlib', 'json', 'importlib.resources', 'typing'},
    '_host_call_recovery': {'dataclasses', 'threading', 'truss.execution'},
    '_host_control_custody': {'truss._native_ingress_deadline', 'truss._native_outbound', 'dataclasses', 'threading', 'pg8000.core', 'truss._native_pg8000', 'truss._native_transactions', 'truss._native_result_custody', 'truss._native_driver_profile', 'truss._host_execution', 'truss.execution'},
    '_host_session': {'truss._native_deadline', 'truss._host_call_recovery', 'dataclasses', 'threading', 'truss._host_execution', 'truss._native_transactions', 'truss._native_arbitration', 'truss._native_pg8000', 'truss._host_control_custody', 'truss.execution'},
    '_host_contracts': {'dataclasses', 'truss.execution'},
    '_host_execution': {'truss._adoption_cancellation', 'truss._host_call_recovery', 'dataclasses', 'threading', 'truss._host_contracts', 'truss._native_adoption', 'truss._native_transactions', 'truss.execution', 'uuid'},
    '_native_adoption': {'contextlib', 'dataclasses', 'truss._host_contracts', 'truss._native_pg8000', 'truss.execution', 'uuid'},
    '_native_arbitration': {'truss._native_operation_ordinals', 'dataclasses', 'threading', 'truss._host_execution', 'truss._native_adoption', 'truss._native_pg8000', 'truss._native_transactions', 'truss._operation_arbitration', 'uuid'},
    '_native_driver_profile': {'pg8000.converters', 'pg8000.core', 'pg8000.native', 'hashlib', 'types', 'importlib.metadata'},
    '_native_outbound': {'truss._startup_custody','truss._native_driver_profile', 'dataclasses', 'truss._native_pg8000'},
    '_native_ingress_deadline': {'io', 'socket', 'truss._native_pg8000', 'truss._native_deadline'},
    '_native_deadline': {'time'},
    '_native_cancellation': {'socket', 'struct', 'threading', 'time'},
    '_native_operation': {'truss._native_ingress_deadline', 'truss._native_deadline', 'truss._native_cancellation', 'truss._host_control_custody', 'dataclasses', 'pg8000.converters', 'pg8000.core', 'pg8000.native', 'threading', 'truss._native_arbitration', 'truss._native_pg8000', 'truss._native_result_custody', 'truss._native_driver_profile', 'truss._native_transactions', 'truss._operation_arbitration', 'truss.execution', 'uuid'},
    '_native_pg8000': {'truss._native_attachment','truss._startup_custody','truss._native_driver_profile', 'dataclasses', 'importlib.metadata', 'pg8000.native', 'threading'},
    '_native_result_custody': {'truss._native_outbound', 'truss._native_ingress_deadline', 'io', 'dataclasses', 'pg8000.converters', 're', 'struct', 'truss._bounded_receive', 'truss._native_pg8000'},
    '_native_transactions': {'truss._native_epoch_acquisitions', 'truss._native_operation_ordinals', 'dataclasses', 're', 'truss._native_adoption', 'truss._native_pg8000', 'truss.execution', 'uuid'},
    '_operation_arbitration': {'dataclasses', 'threading', 'truss._host_execution', 'uuid'},
    'execution': {'dataclasses', 'typing'},
    '_installation_archive': {'dataclasses', 'hashlib'},
    '__init__': {'truss.catalog_preparation','truss.catalog_report_sources','truss.engine_import','truss.traversal','truss.query','truss.import_source','truss.history','truss.capabilities','truss.feed','truss.import_runtime','truss.receipt_visibility','truss.edge_read','truss.reader_catalog','truss._group_runtime','truss.object_read','truss.catalog_view','truss.catalog_runtime','truss.psycopg_host','truss._borrowed_host','truss.installation', 'truss.host', 'truss.assembly', 'truss.assembly_contracts', 'truss.local_runtime', 'truss.execution', 'truss.preparation','truss.current_query','truss.current_disclosure'},
    'installation': {'dataclasses','typing','truss.host','truss.execution','truss.psycopg_host'},
    'host': {'typing', 'truss.execution', 'truss._host_call_recovery', 'dataclasses', 'truss._native_bootstrap', 'truss._host_execution', 'truss._native_transactions', 'truss._native_arbitration', 'truss._host_control_custody', 'truss._host_session'},
    'assembly': {'truss.catalog_runtime','__future__', 'typing', 'dataclasses', 'threading', 'truss.contracts', 'truss.assembly_contracts', 'truss.execution', 'truss.psycopg_host', 'truss.installation'},
    'assembly_contracts': {'dataclasses', 'typing', 'truss.contracts'},
    '_umf_release': set(),
    'preparation': {'weakref', 'dataclasses', 'hashlib', 'pathlib', 'base64', 'json', 'shutil', 'subprocess', 'selectors', 'tempfile', 'time', 'truss._umf_release', 'truss._core08_catalog_release', 'truss._acceptance_json'},
    '_acceptance_json': {'json'},
    '_catalog_completion': {'dataclasses','json','weakref','truss._catalog_report','truss.preparation'},
    '_catalog_support': {'truss._catalog_source_reference','base64','hashlib','importlib.resources','json','truss.preparation','truss._catalog_owner_evidence','truss._owner_evidence_json'},
    '_catalog_owner_evidence': {'truss._catalog_source_reference','base64','hashlib','json','truss.preparation','truss._owner_evidence_json'},
    '_owner_evidence_json': {'json','decimal'},
    '_catalog_report': {'truss._catalog_report_semantics','truss._catalog_support','truss._catalog_owner_evidence','dataclasses', 'json', 'weakref', 'truss.preparation', 'truss._catalog_index_declarations','truss._catalog_lifecycle'},
    '_catalog_report_semantics': {'base64','hashlib','importlib.resources','json','truss.preparation','truss._catalog_support'},
    '_construction_recovery': {'dataclasses','threading'},
    '_installation_metadata': {'hashlib','importlib.resources','json','uuid','truss._installation_archive'},
    '_catalog_installation': {'truss._installation_metadata','types','truss._construction_recovery','dataclasses','hashlib','importlib.resources','json','truss._installation_statement_release','truss._installation_definition_release'},
    '_installation_statement_release': set(),
    '_installation_definition_release': set(),
    '_catalog_lifecycle': {'dataclasses','hashlib','importlib.resources','json','weakref','truss.preparation'},
    '_catalog_index_declarations': {'dataclasses','hashlib','importlib.resources','json','weakref','truss.preparation'},
    '_catalog_staging': {'truss._catalog_support','truss._catalog_report', 'dataclasses', 'json', 'uuid', 'truss.preparation', 'truss._acceptance_json'},
    '_security_association_binding': {'base64', 'dataclasses', 'hashlib', 'json'},
    '_directory_resources': {'os', 'stat', 'threading', 'truss._installation_resources'},
    '_installation_resources': {'dataclasses', 'hashlib', 'json'},
    '_native_admission_capture': {'dataclasses', 'struct', 're', 'truss._native_result_custody', 'truss._native_pg8000'},
    '_catalog_candidate': {'json','dataclasses','truss.preparation','truss._acceptance_json','truss._catalog_support','truss._catalog_owner_evidence','truss._catalog_report_semantics','truss._canonical_wire_tree','truss._owner_evidence_json'},
    '_native_catalog_request': {'truss._catalog_candidate','truss._catalog_report_semantics','truss._catalog_lifecycle','truss._catalog_index_declarations','dataclasses','re','truss.preparation','truss._acceptance_json','truss._catalog_support','truss._native_pg8000'},
    '_canonical_wire_tree': {'dataclasses','json','truss._acceptance_json'},
    '_report_schema_pins': set(),
    '_report_schema': {'hashlib','importlib.resources','json','jsonschema','jsonschema.exceptions','referencing','truss._report_schema_pins'},
    '_catalog_report_assembly': {'truss._native_catalog_metadata','truss._acceptance_json','truss._report_schema','truss._catalog_support','truss._catalog_report_semantics','truss._canonical_wire_tree','hashlib','importlib.resources','json','truss.preparation'},
    '_native_catalog_report_sources': {'truss._native_catalog_metadata','dataclasses','hashlib','truss._catalog_report_assembly','json','truss.preparation','truss._acceptance_json','truss._catalog_lifecycle','truss._catalog_index_declarations','truss._catalog_owner_evidence','truss._catalog_support','truss._catalog_report_semantics'},
    '_native_catalog_capture': {'truss._native_catalog_report_sources','dataclasses','re','truss._native_admission_capture','truss._native_result_custody','truss._native_pg8000','truss._acceptance_json'},
    '_native_string_request': {'dataclasses', 're', 'truss._native_pg8000'},
    '_native_admission_request': {'dataclasses', 're', 'truss._operation_admission'},
    '_operation_admission': {'dataclasses', 'inspect', 'threading'},
    '_operation_registry': set(),
    '_row_image': {'dataclasses', 'struct'},
    '_row_image_capture': {'dataclasses', 'truss._row_image', 'truss._row_event_attribution'},
    '_row_image_scalar_shape': {'truss._row_image'},
    '_row_image_tree': {'truss._row_image_capture', 'truss._row_event_attribution'},
    '_row_event_attribution': {'dataclasses', 'struct', 'truss._row_image'},
    '_row_operation_custody': {'base64', 'dataclasses', 'hashlib', 're', 'truss._acceptance_json'},
    '_row_operation_address': {'dataclasses', 'json', 'truss._acceptance_json', 'truss._row_operation_custody'},
    '_row_group_custody': {'dataclasses', 'truss._acceptance_json', 'truss._row_operation_custody', 'truss._row_operation_address'},
    '_row_operation_context': {'dataclasses', 'truss._acceptance_json', 'truss._row_operation_address', 'truss._row_operation_custody', 'truss._row_group_custody'},
    '_row_touch_registry': {'dataclasses', 'truss._operation_registry', 'truss._row_operation_address', 'truss._row_operation_custody'},
    '_row_registry_correspondence': {'dataclasses', 'truss._row_touch_registry', 'truss._operation_registry', 'truss._row_operation_address', 'truss._row_operation_context', 'truss._row_group_custody', 'truss._row_operation_custody'},
    '_bounded_receive': {'struct', 'threading'},
    '_operation_ordinal': {'dataclasses', 'threading'},
    '_query_execution': {'dataclasses', 'inspect', 'threading', 'types', 'weakref', 'truss.weft'},
    '_receipt_position': {'base64', 'binascii', 'dataclasses', 'json', 're', 'truss._acceptance_json'},
    'cli': {'argparse', 'json', 'pathlib', 'signal', 'threading', 'truss', 'psycopg'},
    'local_runtime': {'truss._runtime_profile', 'dataclasses', 'importlib.metadata', 'importlib.resources', 'pathlib',
                      'subprocess', 'threading', 'pgserver', 'fasteners'},
    'migration_planning': {'dataclasses', 're', 'typing', 'truss._acceptance_json'},
    'numeric': {'dataclasses', 'decimal'},
    'timestamp': {'dataclasses', 'datetime', 're', 'truss.numeric'},
    'weft': {'dataclasses', 'decimal', 'hashlib', 'inspect', 'json', 'threading', 'types', 'typing'},
}


def inspect_sources(source: Path):
    errors, edges = [], []
    modules = {}
    for path in sorted(source.rglob('*.py')):
        relative = path.relative_to(source)
        name = '.'.join(relative.with_suffix('').parts)
        modules[name] = path
    if not modules:
        return ['Python source directory has no modules'], []
    for missing in sorted(set(ALLOWED) - set(modules)):
        errors.append(f'Mapped Python module missing: {missing}')
    for name, path in modules.items():
        if name not in ALLOWED:
            errors.append(f'{path.name}: unmapped module {name}')
            continue
        try:
            tree = ast.parse(path.read_text(), filename=str(path))
        except (SyntaxError, UnicodeError) as error:
            errors.append(f'{path.name}: parse failure {error}')
            continue
        # Function bodies are lexically deferred; class bodies inherit their
        # surrounding scope. Import permissions still apply at every scope.
        deferred_imports = {
            id(child)
            for function in ast.walk(tree)
            if isinstance(function, (ast.FunctionDef, ast.AsyncFunctionDef))
            for statement in function.body
            for child in ast.walk(statement)
            if isinstance(child, (ast.Import, ast.ImportFrom))
        }
        # Resolve aliases for direct import mechanisms; computed/reflection
        # indirection remains a semantic review obligation, not a static proof.
        dynamic_names = {'__import__', 'eval', 'exec'}
        module_aliases = {'importlib'}
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name == 'importlib':
                        module_aliases.add(alias.asname or alias.name)
            if isinstance(node, ast.ImportFrom) and node.module == 'importlib':
                for alias in node.names:
                    if alias.name == 'import_module':
                        dynamic_names.add(alias.asname or alias.name)
        for node in ast.walk(tree):
            targets = []
            if isinstance(node, ast.Import):
                targets = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                if node.level:
                    if node.level != 1:
                        errors.append(f'{path.name}:{node.lineno}: import escapes package')
                        continue
                    targets = ['truss.' + node.module] if node.module else [
                        'truss.' + alias.name for alias in node.names]
                else:
                    targets = ([('truss.' + alias.name) if alias.name in modules or alias.name.startswith('_')
                                else 'truss' for alias in node.names]
                               if node.module == 'truss' else [node.module or ''])
                if any(alias.name == '*' for alias in node.names):
                    errors.append(f'{path.name}:{node.lineno}: wildcard import')
            elif isinstance(node, ast.Call):
                function = node.func
                if (isinstance(function, ast.Name) and function.id in dynamic_names) or (
                    isinstance(function, ast.Attribute) and function.attr == 'import_module'
                    and isinstance(function.value, ast.Name) and function.value.id in module_aliases):
                    errors.append(f'{path.name}:{node.lineno}: dynamic source/import execution requires review')
            for target in targets:
                edges.append({'source': name, 'target': target, 'line': node.lineno,
                              'deferred': id(node) in deferred_imports})
                if target not in ALLOWED[name]:
                    errors.append(f'{path.name}:{node.lineno}: forbidden import {target}')
                if target.startswith('truss.') and target[6:] not in modules:
                    errors.append(f'{path.name}:{node.lineno}: missing local target {target}')
    graph = {name: set() for name in modules}
    for edge in edges:
        target = edge['target']
        local = '__init__' if target == 'truss' else target[6:] if target.startswith('truss.') else None
        if local in graph and not edge['deferred']:
            graph[edge['source']].add(local)
    visited, active = set(), []
    def visit(name):
        if name in active:
            errors.append('Python import cycle: ' + ' -> '.join(active[active.index(name):] + [name]))
            return
        if name in visited:
            return
        active.append(name)
        for target in sorted(graph[name]):
            visit(target)
        active.pop()
        visited.add(name)
    for name in sorted(graph):
        visit(name)
    return errors, edges


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=Path(__file__).resolve().parents[1] / 'packages/python/src/truss')
    parser.add_argument('--json', action='store_true')
    args = parser.parse_args()
    errors, edges = inspect_sources(args.source)
    result = {'scope': 'python-only', 'passed': not errors, 'edgeCount': len(edges),
              'errors': errors, 'edges': edges,
              'unqualified': ['TypeScript imports', 'native SQL dependencies',
                              'reflection/indirect dynamic execution', 'runtime private-object visibility']}
    if args.json:
        print(json.dumps(result, sort_keys=True))
    elif errors:
        print('\n'.join(errors), file=sys.stderr)
    else:
        print(f'Python module boundaries passed ({len(edges)} imports); TypeScript/native gates remain open')
    return 1 if errors else 0


if __name__ == '__main__':
    sys.exit(main())
