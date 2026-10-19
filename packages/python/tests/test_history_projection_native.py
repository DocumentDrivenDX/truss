# SPDX-License-Identifier: MIT OR Apache-2.0
"""History projection preserves ordering, absence, explicit null, and pin checks."""
import json
import psycopg
import test_group_create_native as base


class HistoryProjectionTests(base.PublicCreateGroupTests):
    for name in tuple(n for n in dir(base.PublicCreateGroupTests) if n.startswith('test_')):
        locals()[name]=None

    def test_wide_ordered_projection_and_missing_pin_refusal(self):
        c,h,a,t=self.ready(document_ids=('adoc',))
        self.apply(a,t,*self.input(a,t));h.detach();c.commit()
        image=self.admin.execute('SELECT to_jsonb(o) FROM truss.object o LIMIT 1').fetchone()[0]
        for width in (0,1,128,512):
            image['props']={str(i):{'kind':'string','text':str(i)} if i%2 else None for i in range(width)}
            order=list(reversed(image['props']))+['missing',None,'0','0']
            metadata={'typeId':str(image['type_id']),'revision':str(image['rev']),
                'typePin':'type-pin','propertyOrder':order,
                'propertyPins':{str(i):'pin-'+str(i) for i in range(width)}}
            parameters=(json.dumps(image),'{}',json.dumps(metadata))
            result=self.admin.execute('SELECT truss.runtime_owned_history_record_in_metadata(%s::jsonb,%s::jsonb,%s::jsonb)',parameters).fetchone()[0]
            self.assertEqual(result['properties'],[{'propertyId':p,'definitionPin':'pin-'+p,
                'value':image['props'][p]} for p in order if p in image['props']])
            self.assertEqual(result['identity']['definitionPin'],'type-pin')
            if width:
                del metadata['propertyPins']['0']
                with self.assertRaises(psycopg.errors.ObjectNotInPrerequisiteState):
                    with self.admin.transaction():
                        self.admin.execute('SELECT truss.runtime_owned_history_record_in_metadata(%s::jsonb,%s::jsonb,%s::jsonb)',
                            (json.dumps(image),'{}',json.dumps(metadata)))
