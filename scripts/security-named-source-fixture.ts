// SPDX-License-Identifier: MIT OR Apache-2.0
/** Separately authored source profile. Legacy fixture bytes are not modified. */
import {securityFixture} from '/Users/erik/.codex/worktrees/security-main-integration/umf/tests/security/fixture';

const names:Record<string,string>={
 Staff:'Staff',staffId:'staffId',Project:'Project',projectId:'projectId',
 Resource:'Resource',resourceId:'resourceId',salary:'salary',
 Ownership:'Ownership',ownerId:'ownerId',ownerResource:'ownerResource',ownerProject:'ownerProject',
 Assignment:'Assignment',assignmentId:'assignmentId',assignmentStaff:'assignmentStaff',assignmentProject:'assignmentProject',active:'active',
};
export function namedSecurityFixture(){
 const f=securityFixture();
 const documents=f.resolution.documents.map(entry=>({revision:'named-schema-1',document:{...entry.document,
  modules:entry.document.modules.map(module=>({...module,elements:module.elements.map(element=>{
   if(!Object.hasOwn(names,element.id))throw Error('Explicit named fixture declaration required');
   return {...element,name:names[element.id]!};
  })}))}}));
 const ontology={...f.resolution.ontology,revision:'named-ontology-1',documents:f.resolution.ontology.documents.map(pin=>({...pin,revision:'named-schema-1'}))};
 return {resolution:{ontology,documents},policy:{...f.policy,id:'project-access-named',revision:'named-policy-1',ontology:{...f.policy.ontology,revision:'named-ontology-1'}}};
}
