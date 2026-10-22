from pathlib import Path
import json,hashlib
root=Path('/Users/erik/Projects/truss');src=root/'packages/python/src/truss';tests=root/'packages/python/tests'
def edit(p,a,b):
 s=p.read_text();assert a in s,(p,a);p.write_text(s.replace(a,b))
edit(root/'scripts/build-person-entrypoints.py',"'group_context':'read'","'reached':'read','group_context':'read'")
p=Path('/private/tmp/truss-hf05-native-volatility-declarations.json');v=json.loads(p.read_bytes());v['functions'].append({'set':False,'name':'reached','modes':None,'names':['original_position','maximum_evidence_bytes','expected_release','expected_digest'],'result':'bytea','arguments':'original_position bytea, maximum_evidence_bytes integer, expected_release text, expected_digest text','signature':'truss.reached(bytea,integer,text,text)','inputCount':4,'volatility':'v'});Path('/private/tmp/truss-048-person-declarations.json').write_text(json.dumps(v,indent=2)+'\n')
edit(src/'catalog_runtime.py','SELECT truss.reached(%s,%s,%s,%s)','SELECT truss.person_reached(%s,%s,%s,%s)')
edit(tests/'test_catalog_admission_outcomes.py',"sql_state='42501'))\n        assembly = self.assembly(denied)","sql_state='P1403'))\n        assembly = self.assembly(denied)")
edit(tests/'test_catalog_admission_outcomes.py',"self.assertEqual(result.error.sql_state, '42501')","self.assertIsNone(result.error.sql_state)")
edit(tests/'test_catalog_admission_outcomes.py',"for failure in (\n", "for failure in (\n            Error(ExecutionFailure('execution_obligation', 'actual damaged grant', sql_state='42501')),\n")
edit(tests/'test_group_preview_native.py',"'truss.preview_group_conditions(' in query", "'truss.person_preview_group_conditions(' in query")
edit(tests/'test_relationship_evolution_native.py',"['code'],'dependencies'","['code'],'multiplicity'")
edit(tests/'test_rootless_preparation_native.py',"['nativeState'], 'P1005'","['nativeState'], 'P1405'")
edit(tests/'test_schema_cache_native.py',"with self.assertRaises(psycopg.errors.InsufficientPrivilege):\n            with c.transaction():c.execute(query,(*parameters,first['validator']))", "with self.assertRaises(psycopg.ProgrammingError) as denied:\n            with c.transaction():c.execute(query,(*parameters,first['validator']))\n        self.assertEqual(denied.exception.sqlstate,'P1403')")
edit(tests/'test_catalog_unchanged_native.py',"with self.assertRaises(psycopg.errors.InsufficientPrivilege):connection.commit()", "with self.assertRaises(psycopg.ProgrammingError) as denied:connection.commit()\n        self.assertEqual(denied.exception.sqlstate,'P1403')")
edit(tests/'test_edge_authority_native.py',"except psycopg.errors.InsufficientPrivilege:\n            connection.rollback()", "except psycopg.ProgrammingError as denied:\n            self.assertEqual(denied.sqlstate,'P1403')\n            connection.rollback()")
p=tests/'test_object_mutations_native.py';s=p.read_text();a="with self.assertRaises(psycopg.errors.InsufficientPrivilege):\n            connection.commit()";b="with self.assertRaises(psycopg.ProgrammingError) as denied:\n            connection.commit()\n        self.assertEqual(denied.exception.sqlstate,'P1403')";assert s.count(a)==2;s=s.replace(a,b);p.write_text(s)
# Administrative recovery deliberately has no public person invocation shim.
p=tests/'test_lifecycle_native.py';s=p.read_text();a="denied = assembly.admin_install_recovery_in_transaction(tx)\n        self.assertEqual(denied, Ok(LifecycleRefused(reason='unauthorized')))";b="denied = assembly.admin_install_recovery_in_transaction(tx)\n        from truss import Error\n        self.assertIsInstance(denied,Error)\n        self.assertEqual(denied.error.sql_state,'42501')\n        self.assertNotIn('runtime_owner',denied.error.message)";assert a in s;s=s.replace(a,b);p.write_text(s)
# Correct original grant absence remains an execution error, independently of no membership.
p=tests/'test_receipt_visibility_native.py';s=p.read_text();a="self.assertTrue(reached_original.value.included)\n";b="""self.assertTrue(reached_original.value.included)
        self.admin.execute('REVOKE EXECUTE ON FUNCTION truss.reached(bytea,integer,text,text) FROM group_reader,group_writer')
        try:
            from truss import Error
            damaged=reader_assembly.reached_in_transaction(reader_tx,token)
            self.assertIsInstance(damaged,Error)
            self.assertEqual(damaged.error.sql_state,'42501')
        finally:self.admin.execute('GRANT EXECUTE ON FUNCTION truss.reached(bytea,integer,text,text) TO group_reader,group_writer')
""";assert a in s;s=s.replace(a,b);p.write_text(s)
