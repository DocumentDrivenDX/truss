# SPDX-License-Identifier: MIT OR Apache-2.0
"""Test selection: `slow` is nightly-only; a few modules skip with a stated reason when an optional dependency is missing."""
import os
from pathlib import Path

import pytest
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'scripts'))  # native_fixture

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

# Temporal catalog/query modules need the pinned umf-core 0.10.8 inspection owner, whose installed files
# (including the platform-specific native library) are checked against _temporal_owner/manifest.json.
TEMPORAL_OWNER_MODULES = {
    'test_local_timestamp_query_native', 'test_temporal_catalog_acceptance_native',
    'test_temporal_prepared_writer_native', 'test_temporal_source_guard_native',
    'test_temporal_source_security_native', 'test_temporal_target_release_native',
}
# Needs umf-access 0.10.11 (the typed-sdk extra), which is not published yet.
UMF_ACCESS_MODULES = {'test_temporal_engine_native'}


def _has_temporal_owner():
    try:
        from truss._temporal_owner import _inspector
        _inspector()
        return True
    except Exception:
        return False


def _has_umf_access():
    try:
        import umf_access  # noqa: F401
        return True
    except ImportError:
        return False


# Modules that expect an owned, socket-only worker cluster (TRUSS_NATIVE_WORKER): one per pytest process.
NEEDS_WORKER = {'test_managed_platform_grants_native', 'test_initialization_custody_native',
                'test_initialization_custody_derivation_native'}
_worker = None


@pytest.fixture(autouse=True, scope='module')
def _native_worker(request):
    global _worker
    if request.module.__name__ not in NEEDS_WORKER:
        yield
        return
    if _worker is None:
        from native_fixture import WorkerCluster
        _worker = WorkerCluster().__enter__()
    os.environ['TRUSS_NATIVE_WORKER'] = str(_worker.root)
    yield
    os.environ.pop('TRUSS_NATIVE_WORKER', None)


def pytest_unconfigure(config):
    global _worker
    if _worker is not None:
        _worker.close()
        _worker = None


def pytest_collection_modifyitems(config, items):
    temporal_owner = None
    umf_access = None
    for item in items:
        module = item.module.__name__.split('.')[-1]
        if module in SLOW_MODULES or any(item.nodeid.endswith(key) for key in SLOW_TESTS):
            item.add_marker(pytest.mark.slow)
        if module in TEMPORAL_OWNER_MODULES:
            if temporal_owner is None:
                temporal_owner = _has_temporal_owner()
            if not temporal_owner:
                item.add_marker(pytest.mark.skip(
                    reason='umf-core 0.10.8 inspection owner with the pinned native library not available on this platform'))
        if module in UMF_ACCESS_MODULES:
            if umf_access is None:
                umf_access = _has_umf_access()
            if not umf_access:
                item.add_marker(pytest.mark.skip(reason='needs umf-access 0.10.11 (typed-sdk extra), not published yet'))


def pytest_configure(config):
    config.addinivalue_line('markers', 'slow: long-running native module, run by the nightly job')
