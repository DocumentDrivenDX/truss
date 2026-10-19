# SPDX-License-Identifier: MIT OR Apache-2.0
"""Private selected original pg8000 profile; no capability or closure claim.

Pure inspection only. The selected resource-free subset refuses preexisting
prepared statements rather than asserting release or borrowing their custody.
"""
def original_admission_symbols():
    """Selected cooperative pg8000 profile, independently checked before use.

    Compile bounded, hash-qualified source without executing it. This is driver
    compatibility evidence, not protection against arbitrary Python tampering.
    """
    import hashlib
    import types
    from importlib.metadata import version
    import pg8000.core as core
    try:
        if version('pg8000') != '1.31.5':
            return None
        with open(core.__file__, 'rb') as source_file:
            source = source_file.read(131073)
        if (len(source) > 131072 or hashlib.sha256(source).hexdigest()
                != 'cac1e50502901bcea3ddab588e0350149dd8fd771156ae1c531a2a04b3925e26'):
            return None
        compiled = compile(source, core.__file__, 'exec', dont_inherit=True, optimize=0)
        codes = {item.co_name:item for item in compiled.co_consts if type(item) is types.CodeType}
        context_code = codes['Context']
        init_code = next(item for item in context_code.co_consts
                         if type(item) is types.CodeType and item.co_name == '__init__')
        context, flush = core.Context, core._flush
        if (type(context) is not type or context.__bases__ != (object,)
                or set(context.__dict__) != {'__module__','__init__','__dict__','__weakref__','__doc__'}
                or type(context.__module__) is not str or context.__module__ != core.__name__
                or context.__new__ is not object.__new__
                or context.__getattribute__ is not object.__getattribute__):
            return None
        for function, code, defaults in ((context.__init__, init_code, (None,None,None)),
                                         (flush, codes['_flush'], None)):
            if (type(function) is not types.FunctionType or function.__code__ != code
                    or function.__globals__ is not core.__dict__
                    or (defaults is None and function.__defaults__ is not None)
                    or (defaults is not None and (type(function.__defaults__) is not tuple
                        or len(function.__defaults__) != 3
                        or any(value is not None for value in function.__defaults__)))
                    or function.__kwdefaults__ is not None
                    or function.__closure__ is not None):
                return None
        return context, flush
    except (OSError, ValueError, KeyError, StopIteration, AttributeError):
        return None

def original_admission_snapshot():
    symbols = original_admission_symbols()
    if symbols is None:
        return None
    import pg8000.core as core
    context, flush = symbols
    return (core, context, context.__init__, context.__init__.__code__, flush, flush.__code__)

def admission_snapshot_unchanged(snapshot):
    """Pure in-memory recheck of the already source-qualified snapshot."""
    core, context, init, init_code, flush, flush_code = snapshot
    defaults = init.__defaults__
    return (core.Context is context and core._flush is flush
            and context.__new__ is object.__new__
            and context.__getattribute__ is object.__getattribute__
            and context.__bases__ == (object,)
            and set(context.__dict__) == {'__module__','__init__','__dict__','__weakref__','__doc__'}
            and type(context.__module__) is str and context.__module__ == core.__name__
            and context.__init__ is init and init.__code__ is init_code
            and flush.__code__ is flush_code
            and init.__globals__ is core.__dict__ and flush.__globals__ is core.__dict__
            and type(defaults) is tuple and len(defaults) == 3
            and all(value is None for value in defaults)
            and flush.__defaults__ is None and init.__kwdefaults__ is None
            and flush.__kwdefaults__ is None and init.__closure__ is None
            and flush.__closure__ is None)

def original_driver_profile(boundary):
    from pg8000.converters import string_in, string_out, null_out
    from pg8000.core import CoreConnection
    from pg8000.native import Connection
    with boundary._lock:
        con = boundary._connection
        handlers = boundary._original_driver_handlers
        methods = ('handle_ROW_DESCRIPTION', 'handle_DATA_ROW', 'handle_PARAMETER_DESCRIPTION',
            'handle_COMMAND_COMPLETE', 'handle_ERROR_RESPONSE', 'handle_READY_FOR_QUERY',
            'handle_PARAMETER_STATUS', 'handle_NOTICE_RESPONSE', 'handle_NOTIFICATION_RESPONSE')
        exact_handlers = all(any(getattr(h, '__func__', None) is getattr(CoreConnection, name)
            and getattr(h, '__self__', None) is con for h in handlers.values()) for name in methods)
        exact_dispatch = all(con.message_types.get(k) is v for k,v in boundary._original_handlers.items())
        exact_methods = all(getattr(getattr(con, name), '__func__', None) is getattr(CoreConnection, name)
            and getattr(getattr(con,name),'__self__',None) is con
            for name in ('handle_messages', 'send_EXECUTE', 'send_DESCRIBE_STATEMENT',
                'execute_unnamed', 'execute_named', 'prepare_statement'))
        exact_native_owners = all(getattr(getattr(con,name),'__self__',None) is con for name in ('run','prepare'))
        exact_original_owners = all(getattr(method,'__self__',None) is con for method in
            (boundary._original_parse,boundary._original_close,boundary._original_bind))
        if (not exact_handlers or not exact_dispatch or not exact_methods or not exact_native_owners or not exact_original_owners
                or getattr(con.run, '__func__', None) is not Connection.run
                or getattr(con.prepare, '__func__', None) is not Connection.prepare
                or con.send_PARSE is not boundary._parse_entry
                or con.close_prepared_statement is not boundary._close_entry
                or getattr(boundary._original_parse, '__func__', None) is not CoreConnection.send_PARSE
                or getattr(boundary._original_close, '__func__', None) is not CoreConnection.close_prepared_statement
                or con._statement_nums or any(p._resource.phase != 'closed' for p in boundary._resources)
                or con._client_encoding != 'utf8'
                or con.pg_types[25] is not string_in or con.py_types[str] is not string_out
                or con.py_types[type(None)] is not null_out
                or con.send_BIND is not boundary._bind_entry
                or getattr(boundary._original_bind, '__func__', None) is not CoreConnection.send_BIND):
            return False
        return True

def original_control_profile(boundary):
    from pg8000.core import CoreConnection
    return original_driver_profile(boundary) and all(
        getattr(getattr(boundary._connection, name), '__func__', None) is getattr(CoreConnection, name)
        and getattr(getattr(boundary._connection,name),'__self__',None) is boundary._connection
        for name in ('execute_simple', 'send_QUERY', '_send_message'))

def original_simple_source_profile(boundary):
    """Nonlocking source predicate; caller holds the original native guard."""
    from pg8000.core import CoreConnection
    from pg8000.native import Connection
    con = boundary._connection
    if con._sock is not boundary._original_stream or con._usock is not boundary._original_socket:
        return False
    methods = (("run", Connection.run), *( (name, getattr(CoreConnection,name))
        for name in ('execute_simple','send_QUERY','_send_message','handle_messages')))
    if not all(getattr(getattr(con,name),'__func__',None) is original
               and getattr(getattr(con,name),'__self__',None) is con for name,original in methods):
        return False
    canonical = {b'C':CoreConnection.handle_COMMAND_COMPLETE,
                 b'E':CoreConnection.handle_ERROR_RESPONSE,b'Z':CoreConnection.handle_READY_FOR_QUERY}
    return (all(getattr(boundary._original_driver_handlers[code],'__func__',None) is fn
                and getattr(boundary._original_driver_handlers[code],'__self__',None) is con
                for code,fn in canonical.items())
            and all(con.message_types.get(code) is handler
                    for code,handler in boundary._original_handlers.items()))
