import copy,json,unittest
from truss._row_operation_custody import decode_row_operation_custody
from truss._row_touch_registry import COLUMNS,decode_touch_registry
from truss._row_registry_correspondence import check_touch_operation_correspondence
from test_row_registry_correspondence import fixture


def prepared():
    body,rows=fixture();body=decode_row_operation_custody(json.dumps(body).encode())
    raw=['123','object','100','1','1','101','2','1',body.layout.original.hex(),body.home.original.hex(),body.owner_property.original.hex(),body.original.hex()]
    touches=decode_touch_registry('fixture','123',COLUMNS,[raw],'SELECT','1',1,100000)
    return body,rows,touches


def check(body,rows,touches,**options):
    args=dict(maximum_touches=10,maximum_rows=10,maximum_bytes=100000);args.update(options)
    return check_touch_operation_correspondence(touches,'fixture','123',body.profile,body.layout,rows,**args)

class TouchOperationCorrespondenceTests(unittest.TestCase):
    def test_shared_complete_cohort_and_original_contributor_membership(self):
        body,rows,touches=prepared();result=check(body,rows,touches)
        self.assertEqual([o.cells[1] for o in result.cohort],['20','7','11'])
        self.assertIs(result.touches[0][0],touches[0])
        self.assertIs(result.touches[0][1].cohort,result.cohort)
        self.assertIs(result.touches[0][1].contributors[0],result.cohort[1])
        self.assertEqual([o.cells[1] for o in result.touches[0][1].contributors],['7','11'])
        self.assertEqual(result.cohort[0].cells[3],'application_finalized')
    def test_empty_touch_cohort_does_not_skip_complete_operation_validation(self):
        body,rows,_=prepared();result=check(body,rows,())
        self.assertEqual(len(result.cohort),3);self.assertEqual(result.touches,())
        for column in (8,14):
            bad=copy.deepcopy(rows);bad[0][column]='ff'
            with self.subTest(column=column),self.assertRaises(ValueError):check(body,bad,())
    def test_missing_substituted_duplicate_and_foreign_originals_refuse(self):
        body,rows,touches=prepared()
        with self.assertRaises(ValueError):check(body,[rows[0],rows[2]],touches)
        for column in range(9,14):
            bad=copy.deepcopy(rows);bad[1][column]='ff'
            with self.subTest(column=column),self.assertRaises(ValueError):check(body,bad,touches)
        with self.assertRaises(ValueError):check(body,rows,(*touches,*touches))
        from dataclasses import replace
        for changed in [replace(touches[0],cells=(*touches[0].cells[:11],'ff')),replace(touches[0],cells=('124',*touches[0].cells[1:])),replace(touches[0],custody=replace(body,profile=replace(body.profile,identity='foreign')))]:
            with self.assertRaises(ValueError):check(body,rows,(changed,))
    def test_touch_bounds_and_no_readiness_inference(self):
        body,rows,touches=prepared()
        self.assertEqual(len(check(body,rows,touches,maximum_touches=1).touches),1)
        for limit in (0,True,1.0,-1):
            with self.subTest(limit=limit),self.assertRaises(ValueError):check(body,rows,touches,maximum_touches=limit)
        # Two unfinished operations and an older seal remain structural data.
        result=check(body,rows,touches)
        self.assertEqual(result.touches[0][0].cells[7],'1')
        self.assertEqual(len([o for o in result.cohort if o.cells[3]!='application_finalized']),2)
