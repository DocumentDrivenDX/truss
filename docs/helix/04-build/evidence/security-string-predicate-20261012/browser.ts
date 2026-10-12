import {chromium} from '/Users/erik/.codex/worktrees/security-main-integration/umf/node_modules/playwright/index.mjs';
const root=import.meta.dir;const browser=await chromium.launch({headless:true});
try{
 const page=await browser.newPage();const output:string[]=[];const errors:string[]=[];
 page.on('console',m=>output.push(m.text()));page.on('pageerror',e=>errors.push(String(e)));
 await page.addScriptTag({content:await Bun.file(root+'/browser.js').text()});
 if(errors.length||output.length!==1)throw Error('Browser execution failed: '+JSON.stringify(errors));
 const results=JSON.parse(output[0]);if(JSON.stringify(results)!==JSON.stringify(await Bun.file(root+'/after.json').json()))throw Error('Browser/Bun correspondence failed');
 await Bun.write(root+'/browser.json',JSON.stringify({browser:browser.version(),results,invalid_native_text_controls:3,scope:'Browser candidate computation only; no policy/backend admission'},null,2)+'\n');
}finally{await browser.close();}
