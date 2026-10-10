"""Private selected original pg8000 profile; no capability or closure claim.

Pure inspection only. The selected resource-free subset refuses preexisting
prepared statements rather than asserting release or borrowing their custody.
"""
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
            for name in ('handle_messages', 'send_BIND', 'send_EXECUTE', 'send_DESCRIBE_STATEMENT',
                'execute_unnamed', 'execute_named', 'prepare_statement'))
        if (not exact_handlers or not exact_dispatch or not exact_methods
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
                or getattr(con.send_BIND, '__func__', None) is not CoreConnection.send_BIND):
            return False
        return True
