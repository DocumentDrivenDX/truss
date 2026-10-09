/** Private comparison of already observed owner outputs; no validation authority. */
export function requireUnchangedCatalogTransition(
 originalSourceJson:string,
 source:unknown,
 transition:{source:unknown;target:unknown},
 verified:{source:unknown;target:unknown},
 rollback:{source:unknown;target:unknown},
):void{
 const originalCandidates=[source,transition.source,verified.source,rollback.target];
 if(originalCandidates.some(value=>JSON.stringify(value)!==originalSourceJson))
  throw Error('Original transition source correspondence mismatch');
 const target=JSON.stringify(verified.target);
 if(target===undefined||JSON.stringify(transition.target)!==target||JSON.stringify(rollback.source)!==target)
  throw Error('Original transition target correspondence mismatch');
}
