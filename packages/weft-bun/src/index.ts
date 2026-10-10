/** Bun-only pinned compiler process adapter. Content never chooses executable code. */
import type {Compiler} from '../../weft/src/index';
import {WEFT_SOURCE} from '../../weft/src/index';
export async function loadCompiler(directory: string): Promise<Compiler> {
  const manifest=await Bun.file(directory+'/truss-weft-build.json').json();
  const executable=directory+'/target/debug/weft-runtime';
  if(manifest.revision!==WEFT_SOURCE||manifest.feature!=='truss-postgresql-qualified'||
     manifest.executableSha256!==new Bun.CryptoHasher('sha256').update(await Bun.file(executable).arrayBuffer()).digest('hex'))
       throw Error('Pinned compiler build evidence mismatch');
  return Object.freeze({async compileJson(request:string):Promise<string>{
    const process=Bun.spawn([executable],{stdin:'pipe',stdout:'pipe',stderr:'pipe'});
    const timer=setTimeout(()=>process.kill(),10_000);
    try {
      process.stdin.write(request);process.stdin.end();
      const bounded=async(stream:ReadableStream<Uint8Array>,limit:number)=>{
        const reader=stream.getReader();const chunks:Uint8Array[]=[];let size=0;
        for(;;){const item=await reader.read();if(item.done)break;size+=item.value.byteLength;
          if(size>limit){process.kill();throw Error('Compiler output budget exceeded')}chunks.push(item.value)}
        const bytes=new Uint8Array(size);let offset=0;for(const chunk of chunks){bytes.set(chunk,offset);offset+=chunk.length}
        return new TextDecoder('utf-8',{fatal:true}).decode(bytes);
      };
      const [output]=await Promise.all([bounded(process.stdout,8_388_608),bounded(process.stderr,262_144)]);
      if(await process.exited!==0)throw Error('Compiler process failed or exceeded deadline');
      return output.trimEnd();
    } finally {clearTimeout(timer);process.kill()}
  }});
}
