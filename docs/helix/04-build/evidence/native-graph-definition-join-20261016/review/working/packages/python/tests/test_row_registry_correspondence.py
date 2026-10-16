import copy
import json
import unittest
from dataclasses import FrozenInstanceError
from truss._row_operation_address import encode_row_operation_address
from truss._row_operation_custody import decode_row_operation_custody
from truss._row_registry_correspondence import check_registry_correspondence, resolve_unfinished_operation
from test_row_operation_context import fixtures


def fixture():
    context,group,body=fixtures()
    rows=[]
    original_entry=copy.deepcopy(body['operations'][0])
    for ordinal,phase in (('7','admitted'),('11','effects_ready'),('20','application_finalized')):
        c,g=copy.deepcopy(context),copy.deepcopy(group)
        c['operationOrdinal']=ordinal
        address=encode_row_operation_address('fixture','123',ordinal).decode()
        g['operationIdentity']=address
        entry=copy.deepcopy(original_entry)
        entry.update(ordinal=str(len(body['operations'])),operationIdentity=address,nativeGroupCustodyIdentity=address)
        if ordinal=='11':body['operations'].append(entry)
        artifacts=[entry[k] for k in ('originalOperationDefinition','originalInput','originalPrestate','admittedCandidate','effectObligationDefinition')]
        import base64
        a,b,d,result={'admitted':(None,None,None,None),'effects_ready':('0',None,None,None),
                     'application_finalized':('0','0','0','ff')}[phase]
        rows.append(['123',ordinal,'mutation',phase,'0',a,b,d,json.dumps(c).encode().hex(),
            *[base64.b64decode(v['bytesBase64']).hex() for v in artifacts],json.dumps(g).encode().hex(),result])
    return body,[rows[2],rows[0],rows[1]]


def check(body,rows,**options):
    args=dict(maximum_rows=10,maximum_bytes=100000);args.update(options)
    return check_registry_correspondence(decode_row_operation_custody(json.dumps(body).encode()),'fixture','123',rows,**args)


class RegistryCorrespondenceTests(unittest.TestCase):
    def test_complete_unordered_cohort_and_ordered_contributors(self):
        body,rows=fixture();result=check(body,rows)
        self.assertEqual([r.cells[1] for r in result.cohort],['20','7','11'])
        self.assertEqual([r.cells[1] for r in result.contributors],['7','11'])
        self.assertEqual(result.cohort[0].cells[3],'application_finalized')
        self.assertIs(result.contributors[0],result.cohort[1])
        rows[1][10]='ff'
        self.assertNotEqual(result.contributors[0].cells[10],'ff')
        with self.assertRaises(FrozenInstanceError):result.cohort[0].group.kind='replacement'

    def test_each_original_contributor_carrier_substitution(self):
        for column in range(8,15):
            body,rows=fixture();rows[1][column]='ff'
            with self.subTest(column=column),self.assertRaises(ValueError):check(body,rows)
        body,rows=fixture()
        with self.assertRaises(ValueError):check(body,[rows[0],rows[2]])

    def test_noncontributor_scope_and_family_are_checked(self):
        for field,value in (('installationIdentity','foreign'),('originalWriterXid','124'),('operationOrdinal','21')):
            body,rows=fixture();c=json.loads(bytes.fromhex(rows[0][8]));c[field]=value;rows[0][8]=json.dumps(c).encode().hex()
            with self.subTest(field=field),self.assertRaises(ValueError):check(body,rows)
        body,rows=fixture();g=json.loads(bytes.fromhex(rows[0][14]));g['operationKind']='import';rows[0][14]=json.dumps(g).encode().hex()
        with self.assertRaises(ValueError):check(body,rows)

    def test_unique_unfinished_selection_without_latest_fallback(self):
        body,rows=fixture()
        with self.assertRaisesRegex(ValueError,'ambiguous'):
            resolve_unfinished_operation(check(body,rows))
        # A finalized later ordinal must never replace the unfinished ordinal7.
        rows[2][3]='application_finalized'
        rows[2][5:8]=['0','0','0'];rows[2][15]='ff'
        result=check(body,rows)
        self.assertIs(resolve_unfinished_operation(result),result.contributors[0])
        self.assertEqual(resolve_unfinished_operation(result).cells[1],'7')
        rows[1][3]='application_finalized'
        rows[1][5:8]=['0','0','0'];rows[1][15]='ff'
        with self.assertRaisesRegex(ValueError,'missing'):
            resolve_unfinished_operation(check(body,rows))
        with self.assertRaises(ValueError):resolve_unfinished_operation(None)

    def test_duplicate_foreign_and_complete_capture_bounds(self):
        body,rows=fixture()
        for options in ({'maximum_rows':2},{'maximum_bytes':1}):
            with self.assertRaises(ValueError):check(body,rows,**options)
        with self.assertRaises(ValueError):check(body,rows+[rows[0]])
        rows[0][0]='124'
        with self.assertRaises(ValueError):check(body,rows)


if __name__=='__main__':unittest.main()
