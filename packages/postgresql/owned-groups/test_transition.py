"""Owner-generated unified transition DDL preserves a real legacy mutation."""
from pathlib import Path
from truss.contracts import TextValue
from truss.groups import AuthoredValue,GroupSuccess,StoredObjectReference,UpdateObject
import test_group_create_native as groups


class UnifiedTransitionTests(groups.PublicCreateGroupTests):
    for name in tuple(n for n in dir(groups.PublicCreateGroupTests) if n.startswith('test_')):
        locals()[name]=None

    def test_generated_before_image_change_preserves_legacy_transition(self):
        connection,host,assembly,tx=self.ready()
        semantic,request=self.input(assembly,tx)
        created=self.apply(assembly,tx,semantic,request)
        self.assertIsInstance(created,GroupSuccess)
        identity=created.response.semantic.results[0].identity
        host.detach();connection.commit()
        connection,host,assembly,tx=self.consumer()
        context=assembly.group_context_in_transaction(tx).value
        operation=UpdateObject(target=StoredObjectReference(identity=identity),
            set=(AuthoredValue(name='A-value',value=TextValue(kind='string',text='changed')),),
            unset=(),expected_version='1')
        result=self.apply(assembly,tx,context.input((operation,),semantic.asserted_origin),
                          context.request('unified-transition-baseline'))
        self.assertIsInstance(result,GroupSuccess,repr(result))
        host.detach();connection.commit()
        original=self.admin.execute('SELECT to_jsonb(t) FROM truss.runtime_object_transition t').fetchone()[0]
        self.assertIsNotNone(original['before_object'])
        def required():
            return self.admin.execute("SELECT attnotnull FROM pg_attribute WHERE attrelid='truss.runtime_object_transition'::regclass AND attname='before_object'").fetchone()[0]
        self.assertTrue(required())
        self.admin.execute('BEGIN')
        try:
            self.admin.execute(Path(__file__).with_name('transition-upgrade.generated.sql').read_text())
            self.assertFalse(required())
            self.assertEqual(self.admin.execute('SELECT to_jsonb(t) FROM truss.runtime_object_transition t').fetchone()[0],original)
        finally:
            self.admin.rollback()
        self.assertTrue(required())
