# SPDX-License-Identifier: MIT OR Apache-2.0
"""Test selection: `slow` is nightly-only, `quarantined` (known failing, with a reason) is excluded everywhere."""
import os
from pathlib import Path

import pytest

# Native tests start their own PostgreSQL clusters from these binaries (Unix sockets only).
if not os.environ.get('TRUSS_CENSUS_POSTGRES_BIN'):
    try:
        import pgserver
        os.environ['TRUSS_CENSUS_POSTGRES_BIN'] = str(Path(pgserver.__file__).parent / 'pginstall' / 'bin')
    except ImportError:
        pass

# Modules too slow for the pull-request job (add from `--durations` output); nightly runs `-m slow`.
SLOW_MODULES: set[str] = {
    'test_stress_registration_native',
    'test_catalog_view_capacity_native',
    'test_bulk_create_sql_native',
}

# Timing-sensitive tests that flake on a shared 4-vCPU runner under xdist; nightly runs them.
SLOW_TESTS: set[str] = {
    'test_group_preview_native.py::GroupPreviewNativeTests::test_preview_accepts_3072_conditions',
    'test_group_preconditions_native.py::GroupPreconditionTests::test_owned_3072_mixed_preconditions_succeed',
    'test_group_preconditions_native.py::GroupPreconditionTests::test_owned_3072_preconditions_succeed',
    'test_embedded_owner.py::EmbeddedOwnerTests::test_isolate_deadline_interrupts_nonterminating_code',
}

# Known-failing tests, excluded from CI by `-m "not quarantined"` and listed in the PR description.
# Each entry needs a reason constant; remove the entry when the cause is fixed.
STALE_LAYOUT = 'fixtures install the layout 0.16 DDL, which no longer defines row_home_* tables/types (dropped by fdd249e7); native row-image fixtures need rewriting'
STALE_BASELINE = 'migrations/manifest.json target is stale for the 0.76 runtime; needs a new fresh baseline incl. native initialization-custody policy'
ORIGINAL_INPUT = 'needs an original UMF/Weft producer, compiler or mapping input that is not installable in CI'
ORIGINAL_ADMISSION = 'fails with "Original transaction/profile admission refused" on Linux CI; needs investigation with the owner'
CAMPAIGN_WORKER = 'needs the campaign-owned native worker runner (scripts/qualify-pgserver-pg17.py, removed in the reset)'
OPTIONAL_DEP = 'needs umf-core metadata, umf_access or pydantic, which the CI install does not provide'
OTHER = 'fails on Linux CI for a reason not yet triaged; see the nightly log'
QUARANTINED_MODULES: dict[str, str] = {
    'test_action_role_installation_native': STALE_BASELINE,
    'test_action_store_native': ORIGINAL_ADMISSION,
    'test_current_baseline_native': STALE_BASELINE,
    'test_current_query_full_sources_native': ORIGINAL_INPUT,
    'test_current_query_runtime_native': ORIGINAL_INPUT,
    'test_edge_event_frame_native': STALE_LAYOUT,
    'test_edge_writer_hotfix_native': OTHER,
    'test_embedder_workflows_native': OTHER,
    'test_epoch_state_fence_native': STALE_LAYOUT,
    'test_exact_scalar_values_native': OTHER,
    'test_fenced_subject_key_native': STALE_LAYOUT,
    'test_initialization_custody_derivation_native': CAMPAIGN_WORKER,
    'test_initialization_custody_native': CAMPAIGN_WORKER,
    'test_key_footprint_capacity_native': OTHER,
    'test_local_timestamp_query_native': ORIGINAL_INPUT,
    'test_managed_grants_migration_native': STALE_BASELINE,
    'test_managed_platform_grants_native': CAMPAIGN_WORKER,
    'test_native_admission_dispatch': STALE_LAYOUT,
    'test_native_connected_string_writer': STALE_LAYOUT,
    'test_native_dependent_owner': STALE_LAYOUT,
    'test_native_state_owner': STALE_LAYOUT,
    'test_native_string_candidate': STALE_LAYOUT,
    'test_native_string_dispatch': STALE_LAYOUT,
    'test_numeric_row_image_native': STALE_LAYOUT,
    'test_ordinary_subject_cut_privileges_native': STALE_LAYOUT,
    'test_pg_principal_runtime_native': OTHER,
    'test_preparation_attempt_anchor_native': STALE_BASELINE,
    'test_preparation_seal_storage_native': ORIGINAL_ADMISSION,
    'test_preparation_source_inventory_native': STALE_BASELINE,
    'test_psycopg_epoch_cut_native': STALE_LAYOUT,
    'test_psycopg_graph_projection_native': STALE_LAYOUT,
    'test_psycopg_literal_subject_key_native': OTHER,
    'test_psycopg_subject_observation_native': OTHER,
    'test_published48_migration_receipts_native': STALE_BASELINE,
    'test_reference_decimal_native': STALE_LAYOUT,
    'test_routine_ddl_barrier_native': STALE_LAYOUT,
    'test_row_touch_observer_native': STALE_LAYOUT,
    'test_runtime_migrations_native': STALE_BASELINE,
    'test_runtime_migrations_subsequent_native': STALE_BASELINE,
    'test_temporal_catalog_acceptance_native': ORIGINAL_INPUT,
    'test_temporal_catalog_transport_native': ORIGINAL_INPUT,
    'test_temporal_engine_native': OPTIONAL_DEP,
    'test_temporal_prepared_writer_native': ORIGINAL_INPUT,
    'test_temporal_public055_refusal_native': ORIGINAL_INPUT,
    'test_temporal_source_guard_native': ORIGINAL_INPUT,
    'test_temporal_source_security_native': ORIGINAL_INPUT,
    'test_temporal_target_release_native': OPTIONAL_DEP,
}
QUARANTINED_TESTS: dict[str, str] = {
    'test_catalog_additions_native.py::CatalogAdditionTests::test_readonly_head_advance_refuses_buffered_observation': OTHER,
    'test_group_preconditions_native.py::GroupPreconditionTests::test_owned_3072_mixed_preconditions_succeed': OTHER,
    'test_group_preview_native.py::GroupPreviewNativeTests::test_preview_data_uses_one_snapshot_across_concurrent_update': OTHER,
}

def pytest_collection_modifyitems(config, items):
    for item in items:
        module = item.module.__name__.split('.')[-1]
        if module in SLOW_MODULES or any(item.nodeid.endswith(key) for key in SLOW_TESTS):
            item.add_marker(pytest.mark.slow)
        if module in QUARANTINED_MODULES or any(item.nodeid.endswith(key) for key in QUARANTINED_TESTS):
            item.add_marker(pytest.mark.quarantined)


def pytest_configure(config):
    config.addinivalue_line('markers', 'slow: long-running native module, run by the nightly job')
    config.addinivalue_line('markers', 'quarantined: known failing, excluded from CI; see conftest.py for the reason')
