"""One bounded native ownership image; graph setup is an uninstalled fixture."""
import copy
import json
from pathlib import Path
import psycopg
from truss.groups import GroupSuccess
import test_group_create_native as groups


class OwnedScopeTests(groups.PublicCreateGroupTests):
    for name in tuple(n for n in dir(groups.PublicCreateGroupTests) if n.startswith('test_')):
        locals()[name]=None

    def fields(self,source):
        module=source['modules'][0]
        relation=module['relationships'][0]
        relation['target']=[{'module':'m','element':'A','key':'a-primary'}]
        relation['sourceMultiplicity']={'min':0,'max':1}
        relation['targetMultiplicity']={'min':0,'max':2}
        owned=copy.deepcopy(relation)
        owned['id']=owned['name']='owns'
        owned['targetLifecycle']='owned'
        module['relationships'].append(owned)

    def test_component_and_independent_boundary_use_one_complete_image(self):
        connection,host,assembly,tx=self.ready(self.fields)
        semantic,request=self.input(assembly,tx,tuple(self.create(str(i),alias=str(i)) for i in range(5)))
        result=self.apply(assembly,tx,semantic,request)
        self.assertIsInstance(result,GroupSuccess,repr(result))
        identities=[r.identity for r in result.response.semantic.results]
        host.detach();connection.commit()
        for source in ('forest.sql','scope.sql'):
            self.admin.execute(Path(__file__).with_name(source).read_text())
        type_id=int(identities[0].type_id)
        ids=[int(i.id) for i in identities]
        relations=dict(self.admin.execute("SELECT rel_id,rel_type_id FROM truss.rel_def WHERE document_id='adoc'").fetchall())
        # Simulate an owned graph only inside a transaction that is always rolled back.
        # No public owned-provider claim follows from these administrative fixture rows.
        self.admin.execute('BEGIN')
        self.addCleanup(self.admin.rollback)
        for child in (ids[1],ids[2]):
            self.admin.execute('UPDATE truss.object SET root_id=%s,root_type=%s WHERE id=%s AND type_id=%s',
                               (ids[0],type_id,child,type_id))
        self.admin.execute('UPDATE truss.object SET root_id=%s,root_type=%s WHERE id=%s AND type_id=%s',
                           (ids[4],type_id,ids[3],type_id))
        revision=self.admin.execute('SELECT rev FROM truss.schema_head').fetchone()[0]
        for relation,source,target in (('owns',ids[0],ids[1]),('owns',ids[1],ids[2]),('A-B',ids[1],ids[3]),('owns',ids[4],ids[3])):
            self.admin.execute('INSERT INTO truss.edge(rel_type_id,source_id,source_type,target_id,target_type,rev) VALUES(%s,%s,%s,%s,%s,%s)',
                               (relations[relation],source,type_id,target,type_id,revision))
        def observe():
            return self.admin.execute('SELECT truss.owned_graph_scope(%s::jsonb)',
                (json.dumps([{'typeId':str(type_id),'id':str(ids[1])}]),)).fetchone()[0]
        first=observe()
        key=lambda i:f'{type_id}:{ids[i]}'
        self.assertEqual(set(first['nodes']),{key(0),key(1),key(2)})
        self.assertEqual(len(first['edges']),3)
        self.assertEqual(len(first['ownedEdgeOrder']),2)
        for node in first['forest']:
            native=first['nodes'][first['nodeOrder'][node['node']]]
            for local_edge in node['incomingEdges']:
                edge=first['edges'][first['ownedEdgeOrder'][local_edge]]
                self.assertEqual((edge['target_type'],edge['target_id']),(native['type_id'],native['id']))
        self.assertEqual(set(first['boundary']),{key(3),key(4)})
        self.assertEqual(first['boundary'][key(3)]['object']['root_id'],ids[4])
        self.assertEqual(first,observe())
        self.admin.execute('SAVEPOINT orphan_membership')
        self.admin.execute('UPDATE truss.object SET root_id=%s,root_type=%s WHERE id=%s AND type_id=%s',
                           (ids[0],type_id,ids[4],type_id))
        with self.assertRaises(psycopg.Error) as orphan:
            observe()
        self.assertEqual(orphan.exception.sqlstate,'55000')
        self.admin.execute('ROLLBACK TO SAVEPOINT orphan_membership')
        self.admin.execute('SAVEPOINT unsupported_lifecycle')
        # The fixture changes catalog semantics only in a rolled-back subtransaction.
        self.admin.execute('ALTER TABLE truss.rel_def DISABLE TRIGGER USER')
        self.admin.execute("UPDATE truss.rel_def SET lifecycle='unspecified' WHERE rel_type_id=%s",(relations['A-B'],))
        with self.assertRaises(psycopg.Error) as refused:
            observe()
        self.assertEqual(refused.exception.sqlstate,'0A000')
        self.admin.execute('ROLLBACK TO SAVEPOINT unsupported_lifecycle')
        self.assertEqual(first,observe())
