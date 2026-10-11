#!/usr/bin/env python3
"""Compatibility entrypoint; selected runtime is defined by the Truss profile."""
import runpy
from pathlib import Path
runpy.run_path(str(Path(__file__).with_name("qualify-pgserver.py")), run_name="__main__")
