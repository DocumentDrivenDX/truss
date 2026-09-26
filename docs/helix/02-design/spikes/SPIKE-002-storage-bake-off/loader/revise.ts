// SPIKE-002 option C: generic schema-revision procedure (same code for every type and revision).
// 1. derive the new catalog from the new UMF revision (ids stable), 2. detect stored values that violate any new or
// changed rule using the same SQL predicate as the CHECK constraints, reject the revision if any exist,
// 3. apply declared data transforms (truss-local stand-in: UMF schema evolution, CONTRACT-046, is only a proposal),
// 4. optionally replace the database-side CHECK constraints that changed (NOT VALID, then VALIDATE).
import {catalogFromUmf,catalogSql,checkDdl,indexDdl,INVARIANTS,type Catalog} from './catalog';
export type Transform={kind:'wrap-in-array';element:string}|{kind:'fill-absent';element:string;valueJson:string}|{kind:'truncate-string';element:string;max:number};
export interface RevisionPlan {catalog:Catalog;catalogSql:string;changedRules:{name:string;rule:string;sql:string}[];droppedRules:string[];newIndexes:string[];transforms:string[]}
export function planRevision(prior:Catalog,doc:any,rev:number,transforms:Transform[]=[],binding?:any):RevisionPlan{
  const next=catalogFromUmf(doc,rev,prior);
  const before=new Map(checkDdl(prior,INVARIANTS.sql).map(c=>[c.name,c.sql])),after=checkDdl(next,INVARIANTS.sql);
  const changedRules=after.filter(c=>before.get(c.name)!==c.sql);
  const droppedRules=[...before.keys()].filter(n=>!after.some(c=>c.name===n)||changedRules.some(c=>c.name===n));
  const oldIdx=new Set(indexDdl(prior,binding)),newIndexes=indexDdl(next,binding).filter(i=>!oldIdx.has(i));
  const p=(el:string)=>next.props.find(x=>x.element===el)!;
  const tsql=transforms.map(t=>{const x=p(t.element);const k=`'${x.prop_id}'`;
    const journal=(expr:string,where:string)=>`WITH old AS (SELECT id, props->${k} AS v FROM c.object WHERE type_id = ${x.type_id} AND ${where} FOR NO KEY UPDATE),
 upd AS (UPDATE c.object o SET props = ${expr}, rev = ${rev} FROM old WHERE o.id = old.id RETURNING o.id, o.props->${k} AS v)
INSERT INTO c.journal (object_id, prop_id, op, old_value, new_value, rev, origin) SELECT old.id, ${x.prop_id}, 'migrate', old.v, upd.v, ${rev}, 'revision' FROM old JOIN upd USING (id)`;
    if(t.kind==='wrap-in-array')return journal(`jsonb_set(o.props, '{${x.prop_id}}', jsonb_build_array(o.props->${k}))`,`jsonb_typeof(props->${k}) NOT IN ('array', 'null')`);
    if(t.kind==='fill-absent')return journal(`o.props || jsonb_build_object(${k}, '${t.valueJson}'::jsonb)`,`coalesce(jsonb_typeof(props->${k}), 'null') = 'null'`);
    return journal(`jsonb_set(o.props, '{${x.prop_id}}', to_jsonb(left(o.props->>${k}, ${t.max})))`,`length(props->>${k}) > ${t.max}`);
  });
  return {catalog:next,catalogSql:catalogSql(next),changedRules,droppedRules,newIndexes,transforms:tsql};
}
/** Detection query for one rule: stored objects for which the new rule is false. */
export const violatorsSql=(r:{sql:string})=>`SELECT id FROM c.object WHERE NOT (${r.sql})`;
export const checkReplaceSql=(plan:RevisionPlan)=>[...plan.droppedRules.map(n=>`ALTER TABLE c.object DROP CONSTRAINT IF EXISTS ${n}`),
  ...plan.changedRules.map(c=>`ALTER TABLE c.object ADD CONSTRAINT ${c.name} CHECK (${c.sql}) NOT VALID`)];
export const checkValidateSql=(plan:RevisionPlan)=>plan.changedRules.map(c=>`ALTER TABLE c.object VALIDATE CONSTRAINT ${c.name}`);
