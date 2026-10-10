import {expect,test} from 'bun:test';
import corpus from './fixtures/layout-migration-planning.json';
import {planLayoutMigration} from '../packages/tooling/src/layout-migration-plan';

// Independent expected metadata only: no installed-state or execution authority.
for(const vector of corpus.cases){
 test(`shared migration planning: ${vector.id}`,()=>{
  const bytes=(text:string)=>new TextEncoder().encode(text);
  expect(planLayoutMigration(bytes(vector.manifestText),bytes(vector.observationText),vector.targetVersion)).toEqual(vector.expected);
 });
}
