import {describe,expect,test} from 'bun:test';
import {planLayoutMigration} from '../packages/tooling/src/layout-migration-plan';
const bytes=(value:unknown)=>new TextEncoder().encode(JSON.stringify(value));
const layout=(version:string,hash:string)=>({version,bundleSha256:hash.repeat(64),inventorySha256:'f'.repeat(64)});
const a=layout('1.0.0','a'),b=layout('1.1.0','b'),c=layout('2.0.0','c');
const step=(id:string,from:string,to:string)=>({id,from,to,recipe:{identity:id,sha256:'d'.repeat(64)},procedure:{identity:'transactional-layout-migration',version:'0.1.0',sha256:'e'.repeat(64)},transactional:true});
function manifest(){return {interfaceVersion:'truss-layout-migrations/0.1.0',family:'truss-postgresql',layouts:[a,b,c],steps:[step('one','1.0.0','1.1.0'),step('two','1.1.0','2.0.0')],routes:[{id:'upgrade',from:'1.0.0',to:'2.0.0',direction:'upgrade',steps:['one','two']}]};}
const observation=(current=a)=>({interfaceVersion:'truss-layout-observation/0.1.0',family:'truss-postgresql',layout:current});
describe('explicit inert layout migration plans',()=>{
 test('preserves original declared recipe order and exact source/target',()=>{
  const input=manifest(),original=bytes(input),result=planLayoutMigration(original,bytes(observation()),'2.0.0');
  expect(result.outcome).toBe('plan');if(result.outcome!=='plan')throw Error('expected plan');
  expect(result.steps.map(s=>s.id)).toEqual(['one','two']);expect(result.source).toEqual(a);expect(result.target).toEqual(c);
  input.steps[0]!.recipe.identity='changed';original.fill(0);
  expect(result.steps[0]!.recipe.identity).toBe('one');expect(Object.isFrozen(result.steps)).toBe(true);expect(Object.isFrozen(result.steps[0]!.recipe)).toBe(true);
 });
 test('does not synthesize a route from compatible intermediate steps',()=>{
  expect(planLayoutMigration(bytes(manifest()),bytes(observation()),'1.1.0')).toMatchObject({outcome:'refused',reason:'route'});
 });
 test('at-target metadata issues no steps and claims no installation authority',()=>{
  expect(planLayoutMigration(bytes(manifest()),bytes(observation(c)),'2.0.0')).toEqual({outcome:'no_steps',scope:'declared_metadata_only',family:'truss-postgresql',source:c,target:c});
 });
 test('refuses changed source fingerprints and foreign layout family',()=>{
  expect(planLayoutMigration(bytes(manifest()),bytes(observation({...a,bundleSha256:'0'.repeat(64)})),'2.0.0')).toMatchObject({reason:'source_pin'});
  expect(planLayoutMigration(bytes(manifest()),bytes({...observation(),family:'foreign'}),'2.0.0')).toMatchObject({reason:'family'});
 });
 test('refuses duplicate routes and broken ordered chains',()=>{
  const duplicate=manifest();duplicate.routes.push({...duplicate.routes[0]!,id:'other'});
  expect(planLayoutMigration(bytes(duplicate),bytes(observation()),'2.0.0')).toMatchObject({reason:'invalid_input'});
  const broken=manifest();broken.routes[0]!.steps.reverse();
  expect(planLayoutMigration(bytes(broken),bytes(observation()),'2.0.0')).toMatchObject({reason:'invalid_input'});
 });
 test('downgrades require an explicit complete reverse route',()=>{
  const m=manifest();expect(planLayoutMigration(bytes(m),bytes(observation(c)),'1.0.0')).toMatchObject({reason:'route'});
  m.steps.push(step('back-two','2.0.0','1.1.0'),step('back-one','1.1.0','1.0.0'));
  m.routes.push({id:'reverse',from:'2.0.0',to:'1.0.0',direction:'downgrade',steps:['back-two','back-one']});
  expect(planLayoutMigration(bytes(m),bytes(observation(c)),'1.0.0')).toMatchObject({outcome:'plan',direction:'downgrade'});
 });
 test('refuses nontransactional routes in the default planner profile',()=>{
  const m=manifest();m.steps[0]!.transactional=false;
  expect(planLayoutMigration(bytes(m),bytes(observation()),'2.0.0')).toMatchObject({reason:'nontransactional_profile'});
 });
 test('version components never round through JavaScript numbers',()=>{
  const m=manifest();m.layouts=[layout('9007199254740992.0.0','a'),layout('9007199254740993.0.0','b')];m.steps=[step('exact',m.layouts[0]!.version,m.layouts[1]!.version)];m.routes=[{id:'exact',from:m.layouts[0]!.version,to:m.layouts[1]!.version,direction:'upgrade',steps:['exact']}];
  expect(planLayoutMigration(bytes(m),bytes(observation(m.layouts[0]!)),m.layouts[1]!.version)).toMatchObject({outcome:'plan'});
 });
 test('closed wire rejects duplicate members, numbers, extras and unbounded bytes',()=>{
  const m=manifest();expect(planLayoutMigration(new TextEncoder().encode('{"family":"a","family":"b"}'),bytes(observation()),'2.0.0')).toMatchObject({reason:'invalid_input'});
  expect(planLayoutMigration(bytes({...m,unknown:true}),bytes(observation()),'2.0.0')).toMatchObject({reason:'invalid_input'});
  expect(planLayoutMigration(bytes({...m,layouts:[{...a,version:1}]}),bytes(observation()),'2.0.0')).toMatchObject({reason:'invalid_input'});
  expect(planLayoutMigration(new Uint8Array(1048577),bytes(observation()),'2.0.0')).toMatchObject({reason:'invalid_input'});
 });
 test('route direction must be an exact string even for unselected or at-target routes',()=>{
  const m=manifest();
  m.steps.push(step('reverse','2.0.0','1.0.0'));
  for(const direction of [['downgrade'],['upgrade'],{value:'downgrade'},null,true]){
   const malformed={...m,routes:[...m.routes,{id:'reverse',from:'2.0.0',to:'1.0.0',direction,steps:['reverse']}]};
   for(const [source,target] of [[c,'1.0.0'],[a,'2.0.0'],[c,'2.0.0']] as const){
    expect(planLayoutMigration(bytes(malformed),bytes(observation(source)),target)).toMatchObject({outcome:'refused',reason:'invalid_input'});
   }
  }
 });
 test('direct target text observes the finite byte bound before version selection',()=>{
  for(const target of ['1'.repeat(1048577),'é'.repeat(129),'\0','\ud800'])
   expect(planLayoutMigration(bytes(manifest()),bytes(observation()),target)).toMatchObject({outcome:'refused',reason:'invalid_input'});
 });
});
