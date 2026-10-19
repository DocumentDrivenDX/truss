# SPDX-License-Identifier: MIT OR Apache-2.0
"""Private original source comparison inside the selected epoch-state fence.

Expected image and epoch comparison are independently selected premises, not
issuer authentication. Six-tag administrative fencing does not cover all source
writers. No retained authority lease, SQL emitter or policy activation.
"""
import inspect
from ._psycopg_epoch_cut import _run_fenced_epoch_operation
from ._psycopg_source_census import _capture_census


def _run_census_compared_epoch_operation(host, transaction, comparison, original_image, callback):
    if type(original_image) is not bytes or not 1<=len(original_image)<=16777216:
        raise ValueError('Exact bounded original source image required')
    if not callable(callback) or any(check(candidate)
            for candidate in (callback,getattr(callback,'__call__',None))
            for check in (inspect.iscoroutinefunction,inspect.isasyncgenfunction,inspect.isgeneratorfunction)):
        raise ValueError('Original synchronous compared-source callback required')
    def compared(cursor):
        observation=_capture_census(cursor)
        if observation.original_image!=original_image:
            raise ValueError('Original source image changed before callback')
        result=callback(cursor)
        if inspect.isgenerator(result) or inspect.iscoroutine(result):
            result.close()
            raise ValueError('Completed synchronous compared-source callback required')
        if inspect.isasyncgen(result) or inspect.isawaitable(result):
            raise ValueError('Completed synchronous compared-source callback required')
        return result
    return _run_fenced_epoch_operation(host,transaction,comparison,compared)
