"""Projection refuses incomplete or mistyped graph endpoints before UMF evaluation."""
import json,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[3]/'scripts'))
from security_graph_read import _project_graph_cells

class GraphProjectionTests(unittest.TestCase):
    def test_endpoint_business_keys_replace_native_ids(self):
        nodes=[('900','100',json.dumps({'1':{'kind':'string','text':'s1'}}),'false'),('800','101',json.dumps({'2':{'kind':'string','text':'p1'}}),'false')]
        edges=[('700','100','900','100','800','101',json.dumps({'4':{'kind':'string','text':'a1'},'5':{'kind':'boolean','value':True}}))]
        result=_project_graph_cells(nodes,edges)
        assignment=next(g for g in result if g['associations']==[['domain','m','Assignment']])
        self.assertEqual(assignment['rows'],[['a1','s1','p1','true']])
        for changed_nodes,changed_edges in ((nodes[:1],edges),(nodes,[tuple(edges[0][:3])+('101',)+tuple(edges[0][4:])]),([tuple(nodes[0][:3])+('true',),nodes[1]],edges)):
            with self.assertRaises(ValueError):_project_graph_cells(changed_nodes,changed_edges)
