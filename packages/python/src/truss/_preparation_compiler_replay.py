# SPDX-License-Identifier: MIT OR Apache-2.0
"""Private exact-producer replay; no database, SQL execution or permission.

The engine's Python executable, Truss sources, installed native binary and their
filesystem custody are trusted deployment inputs. A hash alone does not prove
where a binary came from. The pinned binary below is the retained reviewed
Weft build; this API accepts no alternate compiler callable or claimed profile.
"""
from dataclasses import dataclass
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import sys
from ._preparation_program import OriginalPreparationProgram, _json
from .weft import _decode

_SOURCE = 'c0c6449481a87eed38d3f7a6ebebc1f4ab4beeb4'
_NATIVE_SHA256 = '2f91cbd5de07f04492d6fdbd964bf86cce84245adc18cd6debe3c17f61ef6843'
_FIELDS = ('configuration', 'request', 'compile_response', 'binding_artifact', 'lowering')
_WORKER = r'''
import importlib.util, json, pathlib, sys
from hashlib import sha256
binary, expected, library = sys.argv[1:]
if sha256(pathlib.Path(binary).read_bytes()).hexdigest() != expected:
    raise ValueError('Original pinned Weft binary required')
spec = importlib.util.spec_from_file_location('weft', binary)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
sys.path.insert(0, library)
from truss._preparation_program import compile_preparation_program
packet = json.loads(sys.stdin.buffer.read())
result = compile_preparation_program(module.MutationCompiler,
    compiler_source_pin=packet['source'],
    configuration=packet['configuration'].encode('utf8'),
    request=packet['request'].encode('utf8'),
    binding_artifact=packet['binding_artifact'].encode('utf8'),
    evidence=tuple(packet['evidence']))
fields = ('configuration','request','compile_response','binding_artifact','lowering')
sys.stdout.write(json.dumps({name:getattr(result,name).decode('utf8') for name in fields},ensure_ascii=True))
'''


@dataclass(frozen=True, slots=True)
class PreparationCompilerReplay:
    source_commit: str
    native_sha256: str
    original_packet_sha256: tuple[str, ...]
    authority: bool = False


def replay_preparation_program(program, *, native_module_path):
    """Reproduce all original bytes with the one pinned actual native producer.

    A fresh isolated process loads the verified extension directly rather than
    trusting a supplied factory, imported Python wrapper or precomputed SQL.
    The trusted installation must exclude replacement during load/use. This
    private receipt is not authenticated by serializing it and admits no guard.
    """
    if (type(program) is not OriginalPreparationProgram or program.compiler_source_pin != _SOURCE
            or type(native_module_path) is not str or not Path(native_module_path).is_absolute()):
        raise ValueError('Original program and pinned native producer required')
    packet = tuple(getattr(program, name) for name in _FIELDS)
    for raw in packet:
        _json(raw)
    if sum(map(len, packet)) > 16777216:
        raise ValueError('Bounded original compiler packet required')
    invocation = _json(program.lowering)
    if set(invocation) != {'registrationRequest', 'loweringRequest', 'response'}:
        raise ValueError('Original closed lowering invocation required')
    registration = _json(invocation['registrationRequest'].encode('utf8'))
    evidence = registration['evidence']
    binary = Path(native_module_path).resolve(strict=True)
    if not binary.is_file() or sha256(binary.read_bytes()).hexdigest() != _NATIVE_SHA256:
        raise ValueError('Original pinned Weft binary required')
    request = dict(source=_SOURCE, evidence=evidence,
                   **{name:getattr(program,name).decode('utf8') for name in ('configuration','request','binding_artifact')})
    try:
        result = subprocess.run([sys.executable, '-I', '-c', _WORKER, str(binary), _NATIVE_SHA256,
                                 str(Path(__file__).resolve().parents[1])],
                                input=json.dumps(request, ensure_ascii=True).encode('utf8'),
                                capture_output=True, timeout=30, check=True,
                                env={'PATH':os.defpath,'LANG':'C.UTF-8'})
    except (subprocess.SubprocessError, OSError) as error:
        raise ValueError('Original native producer replay refused') from error
    if len(result.stdout) > 67108864:
        raise ValueError('Bounded native replay result required')
    replayed = _decode(result.stdout, 67108864, 'preparation_compiler_replay')[1]
    if (type(replayed) is not dict or set(replayed) != set(_FIELDS)
            or any(type(replayed[name]) is not str or replayed[name].encode('utf8') != raw
                   for name, raw in zip(_FIELDS, packet))):
        raise ValueError('Original native compiler/lowering byte correspondence differs')
    return PreparationCompilerReplay(_SOURCE, _NATIVE_SHA256, tuple(sha256(raw).hexdigest() for raw in packet))
