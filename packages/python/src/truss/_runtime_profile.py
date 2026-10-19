# SPDX-License-Identifier: MIT OR Apache-2.0
"""Selected embedded runtime tuple; wheel builds belong to the pgserver repository."""
import json
from importlib.resources import files

RUNTIME_PROFILE = json.loads(files('truss').joinpath('_profiles/local-postgres-runtime.json').read_text())
RUNTIME_DISTRIBUTION = RUNTIME_PROFILE['distribution']
RUNTIME_VERSION = RUNTIME_PROFILE['distributionVersion']
SERVER_VERSION = RUNTIME_PROFILE['serverVersion']
_major, _minor = map(int, SERVER_VERSION.split('.'))
SERVER_VERSION_NUM = _major * 10000 + _minor
