// SPDX-License-Identifier: MIT OR Apache-2.0
/** Current-format browser mutation owners are not yet available. */
export async function buildBrowserAssets(_directory:string):Promise<{directory:string;manifestSha256:string;providerSha256:string}>{
 throw Error('Unsupported browser distribution: current UMF 0.10 action and compiler owners are unavailable');
}
if(import.meta.main){
 if(!Bun.argv[2])throw Error('Output directory required');
 await buildBrowserAssets(Bun.argv[2]);
}
