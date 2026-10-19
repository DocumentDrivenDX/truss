#!/usr/bin/env python3
# SPDX-License-Identifier: MIT OR Apache-2.0
"""Run unittest and drain registered fixture cleanup even after interruption."""
from pathlib import Path
import os
import runpy
import shutil
import subprocess
import sys
import unittest

sys.argv = ['unittest', *sys.argv[1:]]
try:
    runpy.run_module('unittest', run_name='__main__')
finally:
    classes = {value for module in tuple(sys.modules.values())
               if module is not None and module.__name__.startswith('test_')
               for value in tuple(vars(module).values())
               if isinstance(value, type) and value is not unittest.TestCase and issubclass(value, unittest.TestCase)}
    errors = []
    for cls in classes:
        cls.doClassCleanups()
        errors.extend(str(error[1]) for error in cls.tearDown_exceptions)
        data = getattr(cls, 'data', None)
        socket = getattr(cls, 'socket', None)
        binary = getattr(cls, 'pgbin', None)
        if not (isinstance(data, Path) and isinstance(socket, Path) and isinstance(binary, Path)
                and data.parent == socket.parent
                and data.parent.name.startswith(('truss-psy-', 'truss-prerequisite-'))
                and (data/'postmaster.pid').exists()):
            continue
        # These paths came from this process's original owned fixture classes.
        # Borrowed sockets and other servers are never stopped.
        selected = os.environ.get('TRUSS_CENSUS_POSTGRES_BIN')
        if not selected or binary.resolve() != Path(selected).resolve():
            errors.append('Unselected owned fixture binary; directory retained')
            continue
        try:
            stopped = subprocess.run([str(binary/'pg_ctl'), '-D', str(data), '-w', '-m', 'immediate', 'stop'], capture_output=True, timeout=30)
            status = subprocess.run([str(binary/'pg_ctl'), '-D', str(data), 'status'], capture_output=True, timeout=10)
            if stopped.returncode or status.returncode != 3 or (socket/'.s.PGSQL.5432').exists():
                raise RuntimeError('Owned raw fixture stop unconfirmed; directory retained')
            directory = getattr(cls, 'directory', None)
            if directory is not None:
                directory.cleanup()
            else:
                shutil.rmtree(data.parent)
        except Exception as error:
            directory = getattr(cls, 'directory', None)
            if directory is not None and hasattr(directory, '_finalizer'):
                directory._finalizer.detach()  # Retain an unconfirmed live directory.
            errors.append(str(error))
    if errors:
        raise RuntimeError('Module fixture cleanup failed: ' + '; '.join(errors))
