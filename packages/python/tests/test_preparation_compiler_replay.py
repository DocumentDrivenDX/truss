"""Basic replay of original actual native compiler artifacts, no database."""
from dataclasses import replace
import json
from pathlib import Path
import tempfile
import unittest
from truss._preparation_program import OriginalPreparationProgram
from truss._preparation_compiler_replay import replay_preparation_program

_ROOT = Path(__file__).resolve().parents[3]
_BINARY = Path('/private/tmp/weft-mutation-wheel-installed/weft/weft.abi3.so')


@unittest.skipUnless(_BINARY.is_file(), 'Requires retained exact Weft native build')
class PreparationCompilerReplayTests(unittest.TestCase):
    def test_original_producer_replays_and_changed_sql_or_binary_refuses(self):
        root = _ROOT/'docs/helix/04-build/evidence/preparation-program-20261015'
        program = OriginalPreparationProgram('c0c6449481a87eed38d3f7a6ebebc1f4ab4beeb4',
            *((root/name).read_bytes() for name in ('program-configuration.json','program-request.json',
               'program-compile-response.json','program-binding.json','program-lowering-invocation.json')))
        receipt = replay_preparation_program(program, native_module_path=str(_BINARY))
        self.assertFalse(receipt.authority)
        self.assertEqual(len(receipt.original_packet_sha256), 5)
        invocation = json.loads(program.lowering)
        lowered = json.loads(invocation['response'])
        lowered['sql'] += ' /* changed */'
        invocation['response'] = json.dumps(lowered, separators=(',', ':'))
        changed = replace(program, lowering=json.dumps(invocation, separators=(',', ':')).encode())
        with self.assertRaisesRegex(ValueError, 'byte correspondence differs'):
            replay_preparation_program(changed, native_module_path=str(_BINARY))
        with tempfile.TemporaryDirectory() as directory:
            binary = Path(directory)/'weft.abi3.so';binary.write_bytes(b'not the admitted producer')
            with self.assertRaisesRegex(ValueError, 'pinned Weft binary required'):
                replay_preparation_program(program, native_module_path=str(binary))
