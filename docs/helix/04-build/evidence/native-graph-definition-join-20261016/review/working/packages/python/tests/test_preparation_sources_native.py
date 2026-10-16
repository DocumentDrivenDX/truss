"""Actual original source compiler and Weft replay, immutable native association."""
from importlib.resources import files
import json
from pathlib import Path
import subprocess
from hashlib import sha256
from psycopg import sql
from truss import Error
from truss._preparation_program import OriginalPreparationProgram
from truss._preparation_sources import compile_preparation_sources, register_preparation_sources_in_transaction
import test_preparation_bridge_inventory_native as original

_PIN = '98ee88f193f5d70ccf21bd78ef6c37fffddc5eab'
_BINARY = '/private/tmp/weft-mutation-wheel-installed/weft/weft.abi3.so'


class PreparationSourcesNativeTests(original.PreparationBridgeInventoryNativeTests):
    expected_home_count = 8
    def prepare_component(self, admin, owner):
        from adopter_workflow import transaction, success
        row = admin.execute('SELECT program_id,compiler_source_pin,original_configuration,original_request,original_plan_artifact,original_binding_artifact,original_lowering FROM truss.preparation_program_registration').fetchone()
        program_id = row[0]; program = OriginalPreparationProgram(*row[1:])
        raw = subprocess.check_output(['git','show',_PIN+':docs/helix/04-build/evidence/security/preparation-sources-20261015/input.json'],cwd='/Users/erik/Projects/umf')
        inputs = json.loads(raw)
        for field,name in {'configuration':'configuration','request':'request','compileResponse':'compile_response',
                           'bindingEnvelope':'binding_artifact','loweringInvocation':'lowering'}.items():
            value = getattr(program,name)
            inputs[field] = {'mediaType':'application/json','utf8':value.decode(),'sha256':sha256(value).hexdigest()}
        inputs['binding'] = json.loads(program.binding_artifact)
        raw = json.dumps(inputs,separators=(',',':'),ensure_ascii=False).encode()
        def register(source=raw):
            with transaction(admin) as (assembly,tx):
                return register_preparation_sources_in_transaction(assembly._host,tx,program_id=program_id,
                    program=program,source_inputs=source,native_module_path=_BINARY)
        first = success(register());self.assertEqual(first.program_id,program_id);self.assertFalse(first.authority)
        self.assertEqual(success(register()),first)
        stored = admin.execute('SELECT original_source_packet,producer_identity FROM truss.preparation_program_sources WHERE program_id=%s',(program_id,)).fetchone()
        packet = json.loads(stored[0]);self.assertEqual(packet['original'],inputs)
        self.assertFalse(packet['complete']);self.assertFalse(packet['authority'])
        # A later source spelling is a different immutable association even if
        # its logical policy still passes the original source compiler.
        altered = json.loads(raw);policy = altered['policy'];policy['utf8'] += ' '
        policy['sha256'] = sha256(policy['utf8'].encode()).hexdigest()
        changed = json.dumps(altered,separators=(',',':')).encode()
        self.assertFalse(compile_preparation_sources(program,changed,native_module_path=_BINARY).authority)
        self.assertIsInstance(register(changed),Error)
        self.assertEqual(admin.execute('SELECT count(*) FROM truss.preparation_program_sources').fetchone(),(1,))
        # The shared diagnostic adjunct now includes this explicit attachment
        # home and original program packet in both D and fresh C observations.
        super().prepare_component(admin,owner)
