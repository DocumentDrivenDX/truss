# SPDX-License-Identifier: MIT OR Apache-2.0
"""Closed private executor port for the explicit PV1 facade.

Public DTOs own construction. These providers own native selection; an ordinary
method is never used as a temporal fallback. Original host custody is retained.
"""
from collections.abc import Mapping
from .execution import Error, ExecutionFailure

_ARGUMENTS = {
    'prepare_catalog': {'documents','bun_executable','source_version'},
    'accept_in_transaction': {'transaction','prepared','request_key','origin_bytes','bun_executable','expected_revision','expected_documents'},
    'group_context_in_transaction': {'transaction'},
    'apply_in_transaction': {'transaction','input','request','documents','bun_executable'},
    'dry_run_in_transaction': {'transaction','input','documents'},
    'complete_in_transaction': {'transaction'},
    'recover_group_request_in_transaction': {'transaction','frame'},
    'import_context_in_transaction': {'transaction'},
    'owned_import_context_in_transaction': {'transaction'},
    'object_import_record_in_transaction': {'transaction','document_id','module_id','record_id','values','source'},
    'owned_object_import_record_in_transaction': {'transaction','document_id','module_id','record_id','values','root','source'},
    'import_in_transaction': {'transaction','input','documents','bun_executable'},
    'get_object_in_transaction': {'transaction','document_id','module_id','record_id','object_id','maximum_bytes'},
    'page_objects_in_transaction': {'transaction','document_id','module_id','record_id','limit','cursor','maximum_bytes'},
    'lookup_key_in_transaction': {'transaction','document_id','module_id','record_id','key_id','values','original_document','maximum_bytes','bun_executable'},
    'page_history_in_transaction': {'transaction','entity','cursor','maximum_events','maximum_bytes'},
    'reconstruct_in_transaction': {'transaction','entity','version','maximum_events','maximum_bytes'},
}


def execute(assembly, operation, arguments):
    if (type(operation) is not str or operation not in _ARGUMENTS
            or not isinstance(arguments, Mapping) or set(arguments)!=_ARGUMENTS[operation]):
        raise ValueError('Closed PV1 operation and complete exact arguments required')
    args = dict(arguments)
    with assembly._lock:
        if operation=='prepare_catalog':
            assembly._available()
            from ._temporal_owner import prepare_temporal_catalog
            return prepare_temporal_catalog(args['documents'], bun_executable=args['bun_executable'], source_version=args['source_version'])
        if assembly._disposed:
            failure=ExecutionFailure('execution_obligation','Assembly disposed')
            if operation=='import_in_transaction':
                from .imports import ImportExecutionFailed
                return ImportExecutionFailed(error=failure,report=None)
            return Error(failure)
        if operation=='accept_in_transaction':
            return assembly._accept_catalog_in_transaction(args['transaction'],args['prepared'],
                request_key=args['request_key'],origin_bytes=args['origin_bytes'],bun_executable=args['bun_executable'],
                expected_revision=args['expected_revision'],expected_documents=args['expected_documents'],temporal_route=True)
        if operation in ('group_context_in_transaction','apply_in_transaction','dry_run_in_transaction',
                         'complete_in_transaction','recover_group_request_in_transaction'):
            from ._temporal_group import execute_group
            return execute_group(assembly, operation, args)
        if operation in ('import_context_in_transaction','owned_import_context_in_transaction',
                         'object_import_record_in_transaction','owned_object_import_record_in_transaction','import_in_transaction'):
            from ._temporal_import import execute_import
            return execute_import(assembly, operation, args)
        from ._temporal_read import execute_read
        return execute_read(assembly,operation,args)


def freeze_group_request(input, request, *, documents):
    from ._group_runtime import freeze_group_request as shared_freeze
    return shared_freeze(input,request,documents=documents,temporal=True)
