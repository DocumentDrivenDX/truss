/** Private comparison over bounded, original-source/profile-admitted projections.
 * Does not issue source identity, validate pointers or admit diagnostic artifacts. */
export interface AdmittedDiagnosticComparison {
 readonly sourceIdentity:string;
 readonly diagnosticProfile:string;
 readonly classification:string;
 readonly severity:'error'|'warning';
 readonly code:string;
 readonly path:string;
}
export function equalAdmittedDiagnosticMultisets(expected:readonly AdmittedDiagnosticComparison[],observed:readonly AdmittedDiagnosticComparison[]):boolean {
 if(expected.length!==observed.length)return false;
 const key=(d:AdmittedDiagnosticComparison)=>JSON.stringify([d.sourceIdentity,d.diagnosticProfile,d.classification,d.severity,d.code,d.path]);
 const counts=new Map<string,number>();
 for(const entry of expected){const k=key(entry);counts.set(k,(counts.get(k)??0)+1);}
 for(const entry of observed){const k=key(entry),count=counts.get(k);if(!count)return false;if(count===1)counts.delete(k);else counts.set(k,count-1);}
 return counts.size===0;
}
