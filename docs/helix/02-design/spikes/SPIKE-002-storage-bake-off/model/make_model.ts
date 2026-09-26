// SPIKE-002 Method 1: author the sales model (UMF core 0.7.0 records + the umf.ddd view that UMF's
// CONTRACT-043 generator reads) and its five revisions, plus the umf.binding document and generator policy.
// Throwaway evidence code. Run: bun model/make_model.ts  (writes model/*.json next to this file)
import {writeFileSync} from 'node:fs';
import {dirname,join} from 'node:path';

const here=dirname(new URL(import.meta.url).pathname);
type Json=any;
const M='sales';
type F={name:string;scalar?:string;ddd?:string;nullability:'required'|'absent-allowed';cardinality:'one'|'array'|'map';
  facets?:Json;item?:{scalar:string;facets?:Json};record?:string;sql?:string;storage?:'column'|'embedded'};
type R={id:string;fields:F[];keys?:{id:string;name:string;fields:string[];primary?:boolean}[];ddd:'entity'|'value';
  carriers?:{name:string;sql:string}[];invariants?:Json[];table?:string;embeddedColumn?:string};

// DDD scalar names differ from core scalarType names (binary->bytes, timestamp->date-time).
const dddScalar:Record<string,string>={integer:'integer',string:'string',decimal:'decimal',binary:'bytes',timestamp:'date-time',boolean:'boolean'};

export function baseRecords():R[]{return [
  {id:'Customer',ddd:'entity',table:'sales.customers',embeddedColumn:'payload',
   fields:[
    {name:'id',scalar:'integer',nullability:'required',cardinality:'one',facets:{integerWidth:{bits:64,signed:true}},sql:'bigint'},
    {name:'code',scalar:'string',nullability:'required',cardinality:'one',facets:{length:{max:20,unit:'unicode-scalar'}},sql:'varchar(20)'},
    {name:'name',scalar:'string',nullability:'required',cardinality:'one',facets:{length:{max:100,unit:'unicode-scalar'}},sql:'varchar(100)'},
    {name:'email',scalar:'string',nullability:'absent-allowed',cardinality:'one',facets:{length:{max:200,unit:'unicode-scalar'}},sql:'varchar(200)'},
    {name:'createdAt',scalar:'timestamp',nullability:'required',cardinality:'one',sql:'timestamptz(6)'},
    {name:'tags',nullability:'absent-allowed',cardinality:'array',item:{scalar:'string',facets:{length:{max:30,unit:'unicode-scalar'}}},storage:'embedded'},
    {name:'attributes',nullability:'absent-allowed',cardinality:'map',item:{scalar:'string',facets:{length:{max:100,unit:'unicode-scalar'}}},storage:'embedded'},
    {name:'address',nullability:'absent-allowed',cardinality:'one',record:'Address',storage:'embedded'},
   ],
   keys:[{id:'identity',name:'Identity',fields:['id'],primary:true},{id:'account-code',name:'Account code',fields:['code']}]},
  {id:'Address',ddd:'value',
   fields:[
    {name:'street',scalar:'string',nullability:'required',cardinality:'one',facets:{length:{max:200,unit:'unicode-scalar'}}},
    {name:'city',scalar:'string',nullability:'required',cardinality:'one',facets:{length:{max:100,unit:'unicode-scalar'}}},
    {name:'postalCode',scalar:'string',nullability:'absent-allowed',cardinality:'one',facets:{length:{max:20,unit:'unicode-scalar'}}},
    {name:'country',scalar:'string',nullability:'required',cardinality:'one',facets:{length:{max:2,unit:'unicode-scalar'}}},
   ]},
  {id:'Order',ddd:'entity',table:'sales.orders',
   fields:[
    {name:'id',scalar:'integer',nullability:'required',cardinality:'one',facets:{integerWidth:{bits:64,signed:true}},sql:'bigint'},
    {name:'placedAt',scalar:'timestamp',nullability:'required',cardinality:'one',sql:'timestamptz(6)'},
    {name:'status',scalar:'string',nullability:'required',cardinality:'one',facets:{length:{max:20,unit:'unicode-scalar'}},sql:'varchar(20)'},
    {name:'channel',scalar:'string',nullability:'absent-allowed',cardinality:'one',facets:{length:{max:20,unit:'unicode-scalar'}},sql:'varchar(20)'},
    {name:'total',scalar:'decimal',nullability:'required',cardinality:'one',facets:{precision:14,scale:2},sql:'numeric(14,2)'},
   ],
   // Truss-local stand-in: the DDD view needs a scalar FK carrier field; core 0.7.0 expresses this as a relationship.
   carriers:[{name:'customerId',sql:'bigint'}],
   keys:[{id:'identity',name:'Identity',fields:['id'],primary:true}]},
  {id:'OrderLine',ddd:'entity',table:'sales.order_lines',
   fields:[
    {name:'id',scalar:'integer',nullability:'required',cardinality:'one',facets:{integerWidth:{bits:64,signed:true}},sql:'bigint'},
    {name:'lineNo',scalar:'integer',nullability:'required',cardinality:'one',facets:{integerWidth:{bits:16,signed:true}},sql:'smallint'},
    {name:'quantity',scalar:'integer',nullability:'required',cardinality:'one',facets:{integerWidth:{bits:32,signed:true}},sql:'integer'},
    {name:'unitPrice',scalar:'decimal',nullability:'required',cardinality:'one',facets:{precision:12,scale:2},sql:'numeric(12,2)'},
    {name:'lineTotal',scalar:'decimal',nullability:'required',cardinality:'one',facets:{precision:14,scale:2},sql:'numeric(14,2)'},
   ],
   carriers:[{name:'orderId',sql:'bigint'},{name:'productId',sql:'bigint'}],
   // Truss-local stand-in: core 0.7.0 has no record-level invariant (CONTRACT-048 is a proposal); DDD invariants are opaque text.
   invariants:[{id:'line-total',scope:'definition',language:'postgresql',version:'17',expression:'"lineTotal" = "quantity" * "unitPrice"',references:[{module:M,element:'OrderLine'}]}],
   keys:[{id:'identity',name:'Identity',fields:['id'],primary:true}]},
  {id:'Product',ddd:'entity',table:'sales.products',
   fields:[
    {name:'id',scalar:'integer',nullability:'required',cardinality:'one',facets:{integerWidth:{bits:64,signed:true}},sql:'bigint'},
    {name:'sku',scalar:'string',nullability:'required',cardinality:'one',facets:{length:{max:32,unit:'unicode-scalar'}},sql:'varchar(32)'},
    {name:'name',scalar:'string',nullability:'required',cardinality:'one',facets:{length:{max:200,unit:'unicode-scalar'}},sql:'varchar(200)'},
    {name:'price',scalar:'decimal',nullability:'required',cardinality:'one',facets:{precision:12,scale:2},sql:'numeric(12,2)'},
    {name:'image',scalar:'binary',nullability:'absent-allowed',cardinality:'one',facets:{length:{max:65536,unit:'byte'}},sql:'bytea'},
   ],
   keys:[{id:'identity',name:'Identity',fields:['id'],primary:true}]},
];}

export function baseRelationships():Json[]{return [
  {id:'order-customer',name:'customer',source:[{module:M,element:'Order'}],target:[{module:M,element:'Customer',key:'identity'}],
   sourceMultiplicity:{min:0,max:'*'},targetMultiplicity:{min:1,max:1},targetLifecycle:'independent',directed:true,inverse:'orders'},
  // CONTRACT-041 can only state ownership of the *target*, so "OrderLine owned by Order" is authored Order -> OrderLine.
  {id:'order-lines',name:'lines',source:[{module:M,element:'Order'}],target:[{module:M,element:'OrderLine',key:'identity'}],
   sourceMultiplicity:{min:1,max:1},targetMultiplicity:{min:1,max:'*'},targetLifecycle:'owned',directed:true,inverse:'order'},
  {id:'line-product',name:'product',source:[{module:M,element:'OrderLine'}],target:[{module:M,element:'Product',key:'identity'}],
   sourceMultiplicity:{min:0,max:'*'},targetMultiplicity:{min:1,max:1},targetLifecycle:'independent',directed:true,inverse:'orderLines'},
];}

const fid=(r:string,f:string)=>`${r}.${f}`;
export function buildDocument(records:R[],relationships:Json[],id='truss-spike-002-sales'):Json{
  const elements:Json[]=[];
  for(const r of records){
    const ddd:Json=r.ddd==='entity'
      ?{kind:'entity',fields:{} as Json,identity:{fields:r.keys!.find(k=>k.primary)!.fields,scope:'context'}}
      :{kind:'value',fields:{} as Json,equality:{fields:r.fields.map(f=>f.name)}};
    for(const f of r.fields){
      const card=f.cardinality==='one'?(f.nullability==='required'?'one':'optional'):'many';
      // Stand-in: DDD has no map cardinality; the map is exposed to DDD as a single optional string-valued slot and bound as embedded JSONB.
      if(f.cardinality==='map')ddd.fields[f.name]={type:{kind:'scalar',name:'string'},cardinality:'optional',description:'core: map<string,string>; DDD has no map cardinality (truss-local stand-in)'};
      else if(f.record)ddd.fields[f.name]={type:{kind:'concept',target:{module:M,element:f.record}},cardinality:card};
      else ddd.fields[f.name]={type:{kind:'scalar',name:dddScalar[(f.scalar??f.item!.scalar)]},cardinality:card};
    }
    for(const c of r.carriers??[])ddd.fields[c.name]={type:{kind:'scalar',name:'integer'},cardinality:'one',description:'FK carrier stand-in for a core relationship'};
    if(r.invariants)ddd.invariants=r.invariants;
    const rec:Json={id:r.id,kind:'record',members:r.fields.map(f=>({module:M,element:fid(r.id,f.name)})),extensions:{'umf.ddd':ddd}};
    if(r.keys)rec.keys=r.keys.map(k=>({id:k.id,name:k.name,fields:k.fields.map(f=>({module:M,element:fid(r.id,f)})),...(k.primary?{primary:true}:{})}));
    elements.push(rec);
    for(const f of r.fields){
      const el:Json={id:fid(r.id,f.name),kind:'field',nullability:f.nullability,cardinality:f.cardinality,extensions:{}};
      if(f.scalar)el.scalarType=f.scalar;
      if(f.facets)el.facets=f.facets;
      if(f.record)el.references=[{role:'record-type',module:M,element:f.record}];
      if(f.item){el.itemType={module:M,element:fid(r.id,f.name)+'.item'};}
      elements.push(el);
      if(f.item){const it:Json={id:fid(r.id,f.name)+'.item',kind:'field',scalarType:f.item.scalar,nullability:'required',cardinality:'one',extensions:{}};if(f.item.facets)it.facets=f.item.facets;elements.push(it);}
    }
  }
  return {umf:'0.7.0',id,vocabularies:{'umf.ddd':{version:'0.1.0'}},
    modules:[{id:M,namespace:'sales',extensions:{'umf.ddd':{kind:'bounded-context',terms:[]}},elements,relationships}],extensions:{}};
}

export function buildBinding(records:R[],doc:Json):Json{
  const elements:Json[]=[],fields:Json[]=[];
  for(const r of records){
    if(!r.table)continue;
    elements.push({module:M,element:r.id,table:r.table});
    for(const f of r.fields){
      if(f.storage==='embedded')fields.push({module:M,element:r.id,field:f.name,storage:'embedded',documentColumn:r.embeddedColumn,path:[f.name]});
      else fields.push({module:M,element:r.id,field:f.name,storage:'column',column:f.name});
    }
    for(const c of r.carriers??[])fields.push({module:M,element:r.id,field:c.name,storage:'column',column:c.name});
  }
  return {umf:'0.1.0',id:'truss-spike-002-sales-postgresql',vocabularies:{'umf.binding':{version:'0.1.0'}},modules:[],
    extensions:{'umf.binding':{profile:'umf-binding-1',logical:{documentId:doc.id,coreVersion:doc.umf},
      target:{system:'postgresql',version:'17.4',subset:'ddd-tables-jsonb-list-partition'},elements,fields,
      relationships:[{module:M,name:'customer',storage:'foreign_key'},{module:M,name:'lines',storage:'foreign_key'},{module:M,name:'product',storage:'foreign_key'}],
      indexes:[
        {name:'orders_total_btree',kind:'btree',on:[{field:{module:M,element:'Order',field:'total'}}],unique:false},
        {name:'customers_code_unique',kind:'unique',on:[{field:{module:M,element:'Customer',field:'code'}}],unique:true},
      ]}}};
}
export function buildPolicy(records:R[]):Json{
  const fieldTypes:Json[]=[];
  for(const r of records){if(!r.table)continue;
    for(const f of r.fields)if(f.sql)fieldTypes.push({module:M,element:r.id,field:f.name,sqlType:f.sql});
    for(const c of r.carriers??[])fieldTypes.push({module:M,element:r.id,field:c.name,sqlType:c.sql});}
  return {fieldTypes,partitionFamilies:[]};
}

// Revisions (cumulative). Each returns [records, relationships].
export function revisions():{id:string;title:string;records:R[];relationships:Json[]}[]{
  const out=[];let recs=baseRecords(),rels=baseRelationships();
  const clone=(x:any)=>JSON.parse(JSON.stringify(x));
  const cust=(rs:R[])=>rs.find(r=>r.id==='Customer')!;
  out.push({id:'rev0',title:'base model',records:clone(recs),relationships:clone(rels)});
  cust(recs).fields.push({name:'phone',scalar:'string',nullability:'absent-allowed',cardinality:'one',facets:{length:{max:30,unit:'unicode-scalar'}},sql:'varchar(30)'});
  out.push({id:'rev1',title:'R1 add optional Customer.phone',records:clone(recs),relationships:clone(rels)});
  cust(recs).fields.find(f=>f.name==='name')!.facets={length:{max:60,unit:'unicode-scalar'}};cust(recs).fields.find(f=>f.name==='name')!.sql='varchar(60)';
  out.push({id:'rev2',title:'R2 tighten Customer.name length 100 -> 60',records:clone(recs),relationships:clone(rels)});
  rels.push({id:'customer-referrer',name:'referredBy',source:[{module:M,element:'Customer'}],target:[{module:M,element:'Customer',key:'identity'}],
    sourceMultiplicity:{min:0,max:'*'},targetMultiplicity:{min:0,max:1},targetLifecycle:'independent',directed:true,inverse:'referrals'});
  out.push({id:'rev3',title:'R3 add Customer -> Customer referredBy',records:clone(recs),relationships:clone(rels)});
  const email=cust(recs).fields.find(f=>f.name==='email')!;
  Object.assign(email,{cardinality:'array',scalar:undefined,facets:undefined,item:{scalar:'string',facets:{length:{max:200,unit:'unicode-scalar'}}},sql:undefined,storage:'embedded'});
  out.push({id:'rev4',title:'R4 Customer.email one -> array',records:clone(recs),relationships:clone(rels)});
  recs.find(r=>r.id==='Order')!.fields.find(f=>f.name==='channel')!.nullability='required';
  out.push({id:'rev5',title:'R5 Order.channel absent-allowed -> required',records:clone(recs),relationships:clone(rels)});
  return out;
}

if(import.meta.main){
  for(const rev of revisions()){
    const doc=buildDocument(rev.records,rev.relationships);
    writeFileSync(join(here,`sales.${rev.id}.umf.json`),JSON.stringify(doc,null,1)+'\n');
    if(rev.id==='rev0'){
      writeFileSync(join(here,'sales.binding.json'),JSON.stringify(buildBinding(rev.records,doc),null,1)+'\n');
      writeFileSync(join(here,'sales.policy.json'),JSON.stringify(buildPolicy(rev.records),null,1)+'\n');
    }
  }
  console.log('wrote model files to',here);
}
