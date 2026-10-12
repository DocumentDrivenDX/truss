"""Private synchronous query coordination; no native/security service factory.

Only original admitted host services may supply this boundary. Unit callbacks
do not qualify native authority, snapshot, result decoding or cleanup semantics.
"""
from dataclasses import dataclass
import inspect
from threading import Lock
from types import MappingProxyType
from weakref import WeakValueDictionary
from .weft import CompilerBoundary, CompiledQuery, CompileRefusal


@dataclass(frozen=True, slots=True, weakref_slot=True, eq=False)
class QueryPlan:
    compiled: CompiledQuery


def _synchronous(value):
    if inspect.isgenerator(value):
        value.close()
        raise CompileRefusal('execution_obligation', 'Deferred original callback body is unavailable')
    if inspect.isasyncgen(value):
        raise CompileRefusal('execution_obligation', 'Synchronous original host callback required')
    if inspect.isawaitable(value):
        if inspect.iscoroutine(value):
            value.close()
        raise CompileRefusal('execution_obligation', 'Synchronous original host callback required')
    return value


def _deferred_callable(callback):
    return any(check(candidate)
               for candidate in (callback, getattr(callback, '__call__', None))
               for check in (inspect.iscoroutinefunction, inspect.isasyncgenfunction,
                             inspect.isgeneratorfunction))


def _completed_check(value):
    if _synchronous(value) is not None:
        raise CompileRefusal('execution_obligation', 'Original check must complete or raise')


class _SynchronousContext:
    def __init__(self, manager):
        self._enter = manager.__enter__
        self._exit = manager.__exit__
        if any(not callable(f) or _deferred_callable(f)
               for f in (self._enter,self._exit)):
            raise CompileRefusal('execution_obligation', 'Synchronous original context lifecycle required')

    def __enter__(self):
        return _synchronous(self._enter())

    def __exit__(self, error_type, error, traceback):
        result = _synchronous(self._exit(error_type,error,traceback))
        if result is not None and type(result) is not bool:
            raise CompileRefusal('execution_obligation', 'Original context exit must complete')
        return result


def _freeze_result(value):
    if type(value) is str:
        try: value.encode('utf-8', errors='strict')
        except UnicodeError as error:
            raise CompileRefusal('decoder', 'Lossless Unicode required') from error
        return value
    if value is None or type(value) is bool:
        return value
    if type(value) in (tuple, list):
        return tuple(_freeze_result(child) for child in value)
    if type(value) in (dict, MappingProxyType):
        if any(type(key) is not str for key in value):
            raise CompileRefusal('decoder', 'Exact string member names required')
        for key in value:
            _freeze_result(key)
        return MappingProxyType({key:_freeze_result(child) for key,child in value.items()})
    raise CompileRefusal('decoder', 'Stored values require admitted exact carriers')


class QueryCoordinator:
    """Implementation seam for the existing host/handler/read-scope contract.

    host.read_context() must return the original admitted context manager.
    The host owns connections, transactions, authority, cleanup and settlement.
    This coordinator neither commits nor retries. No public ready-engine export.
    """
    def __init__(self, compiler: CompilerBoundary, host=None):
        self._compile = compiler.compile_request
        self._context = host.read_context if host is not None else None
        self._decode = host.decode if host is not None else None
        self._handlers = MappingProxyType({
            key:(handler.accepts,handler.check) for key,handler in host.handlers.items()
        }) if host is not None else MappingProxyType({})
        callbacks = [self._context,self._decode] + [f for pair in self._handlers.values() for f in pair]
        if any(not callable(f) or _deferred_callable(f) for f in callbacks if f is not None):
            raise CompileRefusal('execution_obligation', 'Synchronous original host functions required')
        self._plans = WeakValueDictionary()
        self._disposed = False
        self._executing = False
        self._lock = Lock()

    def _admitting(self):
        with self._lock:
            if self._disposed:
                raise CompileRefusal('disposed', 'Query coordinator disposed')

    def dispose(self):
        with self._lock:
            self._disposed = True

    def compile_request(self, original: bytes) -> QueryPlan:
        self._admitting()
        compiled = self._compile(original)
        with self._lock:
            if self._disposed:
                raise CompileRefusal('disposed', 'Query coordinator disposed')
            plan = QueryPlan(compiled)
            self._plans[id(plan)] = plan
            return plan

    def execute(self, plan: QueryPlan):
        with self._lock:
            if self._disposed:
                raise CompileRefusal('disposed', 'Query coordinator disposed')
            if self._plans.get(id(plan)) is not plan:
                raise CompileRefusal('plan', 'Foreign or substituted query plan')
            if self._executing:
                raise CompileRefusal('busy', 'Original read invocation already active')
            self._executing = True
        try:
            if self._context is None:
                raise CompileRefusal('runtime_unavailable', 'Original native host not installed')
            artifact = plan.compiled.artifact
            selected = []
            for obligation in artifact['obligations']:
                if not isinstance(obligation, MappingProxyType) or obligation.get('owner') != 'host' or type(obligation.get('id')) is not str:
                    raise CompileRefusal('obligation', 'Unsupported original obligation')
                handler = self._handlers.get(obligation['id'])
                if handler is None or _synchronous(handler[0](obligation,artifact)) is not True:
                    raise CompileRefusal('obligation', 'Unknown original obligation meaning')
                self._admitting()
                selected.append((obligation,handler[1]))
            missing = object()
            result = missing
            self._admitting()
            with _SynchronousContext(_synchronous(self._context())) as scope:
                verify_context = scope.verify_context
                query = scope.query
                self._admitting()
                _completed_check(verify_context(artifact))
                self._admitting()
                for obligation,check in selected:
                    _completed_check(check(scope,obligation,artifact))
                    self._admitting()
                rows = _synchronous(query(artifact['sql'],tuple(p['value'] for p in artifact['parameters'])))
                if type(rows) not in (tuple,list) or any(
                    type(row) not in (tuple,list) or len(row) != len(artifact['columns'])
                    or any(cell is not None and type(cell) is not str for cell in row) for row in rows
                ):
                    raise CompileRefusal('transport', 'Complete exact text/null rows required')
                self._admitting()
                decoded = _synchronous(self._decode(artifact,rows))
                _completed_check(verify_context(artifact))
                self._admitting()
                if type(decoded) not in (tuple,list):
                    raise CompileRefusal('decoder', 'Complete decoded result sequence required')
                frozen = _freeze_result(decoded)
                result = frozen
            self._admitting()
            if result is missing:
                raise CompileRefusal('context', 'Host suppressed incomplete read failure')
            return result
        finally:
            with self._lock:
                self._executing = False
