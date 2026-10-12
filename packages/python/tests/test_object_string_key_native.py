from pathlib import Path
import unittest
import test_catalog_runtime_native as catalog_tests
import test_umf_key_tuples as key_tests
from truss import Ok
from truss._umf_key_tuples import KeyTupleRequest


class ObjectStringKeyNativeTests(catalog_tests.PublicCatalogRuntimeTests):
    def test_tuple_is_checked_against_actual_qualified_object_key(self):
        self.install();connection,host,assembly,tx=self.consumer()
        prepared=self.prepared(assembly)
        self.assertIsInstance(assembly.accept_in_transaction(tx,prepared,request_key='native-key-row'),Ok)
        host.detach();connection.commit()
        root=Path(__file__).resolve().parents[3]/'packages/postgresql/native'
        for name in ('verify-umf-string-key-tuple.sql','verify-object-string-key.sql'):
            self.admin.execute((root/name).read_text())
        type_id=self.admin.execute("SELECT type_id FROM truss.type_def WHERE document_id='adoc' AND element='A'").fetchone()[0]
        props=self.admin.execute('SELECT prop_id,element FROM truss.prop_def WHERE type_id=%s',(type_id,)).fetchall()
        values={str(identity):{'kind':'string','text':'value' if name.endswith('value') else 'label'} for identity,name in props}
        import json
        object_id=self.admin.execute('INSERT INTO truss.object(type_id,props,rev) VALUES(%s,%s::jsonb,1) RETURNING id',(type_id,json.dumps(values))).fetchone()[0]
        tuple_bytes=key_tests.OriginalUmfKeyTupleTests().encode((KeyTupleRequest('m','A','a-primary',('value','label')),))[0].tuple_bytes
        query='SELECT truss.verify_object_string_key(%s,%s,%s::smallint,%s)'
        self.assertTrue(self.admin.execute(query,(object_id,type_id,1,tuple_bytes)).fetchone()[0])
        self.assertFalse(self.admin.execute(query,(object_id,type_id,2,tuple_bytes)).fetchone()[0])
        other=self.admin.execute("SELECT type_id FROM truss.type_def WHERE document_id='zdoc' AND element='A'").fetchone()[0]
        self.assertFalse(self.admin.execute(query,(object_id,other,1,tuple_bytes)).fetchone()[0])
        label_id=next(str(identity) for identity,name in props if name.endswith('label'))
        for cell in ({'kind':'integer','text':'label'},{'kind':'string','text':'changed'},
                     {'kind':'string','text':'label','extra':True},None):
            changed=dict(values);changed[label_id]=cell
            self.admin.execute('UPDATE truss.object SET props=%s::jsonb WHERE id=%s',(json.dumps(changed),object_id))
            self.assertFalse(self.admin.execute(query,(object_id,type_id,1,tuple_bytes)).fetchone()[0])
        self.admin.execute('UPDATE truss.object SET props=%s::jsonb WHERE id=%s',(json.dumps(values),object_id))
        self.admin.execute('BEGIN')
        self.admin.execute('ALTER TABLE truss.type_def DISABLE TRIGGER USER')
        self.admin.execute('UPDATE truss.type_def SET retired_rev=1 WHERE type_id=%s',(type_id,))
        self.assertFalse(self.admin.execute(query,(object_id,type_id,1,tuple_bytes)).fetchone()[0])
        self.admin.rollback()
        for column,value in (('home','row'),('cardinality','many'),('nullability','absent-allowed')):
            self.admin.execute('BEGIN')
            self.admin.execute('ALTER TABLE truss.prop_def DISABLE TRIGGER USER')
            from psycopg import sql
            self.admin.execute(sql.SQL('UPDATE truss.prop_def SET {}=%s WHERE prop_id=%s').format(sql.Identifier(column)),(value,int(label_id)))
            self.assertFalse(self.admin.execute(query,(object_id,type_id,1,tuple_bytes)).fetchone()[0])
            self.admin.rollback()
        self.admin.execute('UPDATE truss.object SET props=%s::jsonb WHERE id=%s',(json.dumps({}),object_id))
        self.assertFalse(self.admin.execute(query,(object_id,type_id,1,tuple_bytes)).fetchone()[0])


for _name in tuple(vars(catalog_tests.PublicCatalogRuntimeTests)):
    if _name.startswith('test_'):setattr(ObjectStringKeyNativeTests,_name,None)

if __name__=='__main__':unittest.main()
