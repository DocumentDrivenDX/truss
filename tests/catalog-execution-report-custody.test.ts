import {test,expect} from 'bun:test';
import {requireOriginalCatalogExecutionReportCandidate,recheckOriginalCatalogExecutionReportCandidate} from '../packages/umf-bun/src/catalog-execution-report-candidate';
test('unissued execution report candidates refuse before any native query',async()=>{
 let calls=0;const connection={unsafe:async()=>{calls++;return []}};
 for(const candidate of [{},Object.freeze({candidate:{installationId:'invented',sourceEpoch:'invented'},scope:'original_execution_report_candidate_only'})]){
  expect(()=>requireOriginalCatalogExecutionReportCandidate(candidate,connection,{} as any,{} as any)).toThrow('candidate custody');
  await expect(recheckOriginalCatalogExecutionReportCandidate(candidate,connection,{} as any,{} as any)).rejects.toThrow('candidate custody');
 }
 expect(calls).toBe(0);
});
