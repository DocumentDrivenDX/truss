import {createRequire} from 'node:module';
const {chromium}=createRequire('/Users/erik/Projects/umf/package.json')('playwright');
const server=Bun.serve({hostname:'127.0.0.1',port:0,async fetch(req){let path=new URL(req.url).pathname;if(!path.startsWith('/truss/'))return new Response('Not found',{status:404});path=path.slice(7);if(!path||path.endsWith('/'))path+='index.html';const file=Bun.file('website/public/'+path);return await file.exists()?new Response(file):new Response('Not found',{status:404});}});
const browser=await chromium.launch({headless:true});
try{
 const page=await browser.newPage();const errors:string[]=[];page.on('pageerror',e=>errors.push(String(e)));
 const base=`http://127.0.0.1:${server.port}/truss/`;
 await page.goto(base+'model/');const frame=page.frameLocator('iframe[title="Truss storage schema — UMF browser"]');
 await frame.locator('.definition-list').waitFor();
 if(!(await frame.locator('#inspector').innerText()).includes('Core structure valid'))throw Error('Core model did not validate');
 const definitions=await frame.locator('.definition-list a').count();
 await page.goto(base+'schema/#'+new URLSearchParams({schema:'truss-layout',definition:JSON.stringify(['truss-layout','prop_def'])}));
 await page.locator('.definition-heading').waitFor();
 if(!(await page.locator('table').innerText()).includes('declaration_module'))throw Error('Current layout field missing');
 await page.locator('table a').filter({hasText:'declaration_module'}).click();
 await page.locator('.definition-heading').filter({hasText:'declaration_module'}).waitFor();
 const downloadEvent=page.waitForEvent('download');await page.getByText('Download source',{exact:true}).click();const download=await downloadEvent;
 const downloaded=await Bun.file((await download.path())!).text();const original=await Bun.file('website/static/schema/truss-layout.umf.json').text();if(downloaded!==original)throw Error('Download changed source');
 await page.setViewportSize({width:390,height:844});await page.goto(base+'schema/');await page.locator('.definition-list').waitFor();
 const overflow=await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth);if(overflow)throw Error('Mobile page overflow');if(errors.length)throw Error(errors.join('\n'));
 const receipt={browser:browser.version(),ownerRevision:'44bbd8922ba4a3c7be2afa1a5ec2e6fecd473e64',definitions,checks:['Hugo Model page embeds working owner browser','current structural model validates','prop_def deep link and declaration_module field navigation','download is byte-identical UTF-8 source','390px mobile browser has no horizontal page overflow','no browser errors'],scope:'Actual generated site under /truss/ in Chromium; structural inspection only, no deployment or native runtime qualification.'};
 await Bun.write('docs/helix/04-build/evidence/design-audit/schema-browser-site.json',JSON.stringify(receipt,null,2)+'\n');console.log(JSON.stringify(receipt));
}finally{await browser.close();server.stop(true)}
