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

    def test_batched_pair_projection_matches_single_image_oracle(self):
        c,h,a,t=self.ready(document_ids=('adoc',))
        self.apply(a,t,*self.input(a,t));h.detach();c.commit()
        source=self.admin.execute('SELECT to_jsonb(o) FROM truss.object o LIMIT 1').fetchone()[0]
        identity={}
        for width in (0,1,128,512):
            before=dict(source)
            before['props']={str(i):{'kind':'string','text':str(i)} if i%2 else None for i in range(width)}
            before['retained']=None
            order=list(reversed(before['props']))+['missing',None,'0','0']
            batch_count=64 if width==128 else 1
            batch=[]
            dictionary={}
            basis_by_index={}
            representative_by_basis={}
            for i in range(batch_count):
                before_i=dict(before)
                after_i=dict(before)
                after_i['props']=dict(before['props'])
                if width:
                    after_i['props']['0']={'kind':'string','text':'updated'}
                after_i['retained']={'extension':{'kind':'string','text':'kept'}}
                after_i['ver']=str(int(before_i['ver'])+1)
                if width==128 and i%2:
                    before_i['type_id']=int(before_i['type_id'])+1
                    after_i['type_id']=int(after_i['type_id'])+1
                    before_i['rev']=str(int(before_i['rev'])+1)
                    after_i['rev']=str(int(after_i['rev'])+1)
                metadata={'typeId':str(before_i['type_id']),'revision':str(before_i['rev']),
                    'typePin':'type-pin','propertyOrder':order,
                    'propertyPins':{str(i):'pin-'+str(i) for i in range(width)}}
                basis_key=json.dumps([int(before_i['rev']),int(before_i['type_id'])])
                dictionary[basis_key]=metadata
                basis_by_index[str(7+i)]=basis_key
                representative_by_basis.setdefault(basis_key,(before_i,after_i,metadata))
                batch.append({'index':7+i,'changed':True,'identity':identity,
                    'before':before_i,'after':after_i})
            if width!=128:
                batch.append({'index':7+batch_count,'changed':False,'identity':identity,
                    'before':before,'after':before})
            projected=self.admin.execute('''SELECT truss.runtime_owned_history_records_in_metadata(%s::jsonb,%s::jsonb)''',
                (json.dumps(batch),json.dumps(dictionary))).fetchone()[0]
            expected_indices={str(7+i) for i in range(batch_count)}
            self.assertEqual(set(projected),expected_indices)
            expected_pairs={}
            for basis_key,(before_i,after_i,metadata) in representative_by_basis.items():
                expected_pair={}
                for side,image in (('before',before_i),('after',after_i)):
                    expected_pair[side]=self.admin.execute('''SELECT truss.runtime_owned_history_record_in_metadata(%s::jsonb,%s::jsonb,%s::jsonb)''',
                        (json.dumps(image),json.dumps(identity),json.dumps(metadata))).fetchone()[0]
                expected_pairs[basis_key]=expected_pair
            for index in expected_indices:
                self.assertEqual(projected[index],expected_pairs[basis_by_index[index]])

            if width:
                broken=dict(next(iter(dictionary.values())))
                broken['propertyPins']=dict(broken['propertyPins'])
                del broken['propertyPins']['0']
                with self.assertRaises(psycopg.errors.ObjectNotInPrerequisiteState):
                    with self.admin.transaction():
                        self.admin.execute('''SELECT truss.runtime_owned_history_records_in_metadata(%s::jsonb,%s::jsonb)''',
                            (json.dumps(batch),json.dumps({next(iter(dictionary)):broken})))

        first=batch[0]
        rev=int(first['before']['rev']);type_id=int(first['before']['type_id'])
        basis_key=json.dumps([rev,type_id])
        for invalid_dictionary in ({}, {basis_key:{'typeId':str(type_id),'revision':str(rev),
                'typePin':'type-pin','propertyOrder':'not-an-array','propertyPins':{}}}):
            with self.assertRaises(psycopg.errors.ObjectNotInPrerequisiteState):
                with self.admin.transaction():
                    self.admin.execute('''SELECT truss.runtime_owned_history_records_in_metadata(%s::jsonb,%s::jsonb)''',
                        (json.dumps([first]),json.dumps(invalid_dictionary)))
