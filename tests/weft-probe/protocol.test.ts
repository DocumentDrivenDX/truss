import {test,expect} from 'bun:test';
import {createServer,type Socket} from 'node:net';
import {LocalPgProbe} from '../../packages/weft-pg-probe/src/index';
const n32=(v:number)=>{const b=Buffer.alloc(4);b.writeInt32BE(v);return b};
const n16=(v:number)=>{const b=Buffer.alloc(2);b.writeInt16BE(v);return b};
const frame=(tag:string,body:Buffer)=>Buffer.concat([Buffer.from(tag),n32(body.length+4),body]);
const z=(v:string)=>Buffer.from(v+'\0');
async function fixture(auth:number,onQuery:(socket:Socket)=>void){
 const sockets:Socket[]=[];const server=createServer(socket=>{sockets.push(socket);let started=false,buffer=Buffer.alloc(0);
  socket.on('data',chunk=>{buffer=Buffer.concat([buffer,chunk as Buffer]);
   if(!started){if(buffer.length<4||buffer.length<buffer.readInt32BE())return;buffer=buffer.subarray(buffer.readInt32BE());started=true;socket.write(Buffer.concat([frame('R',n32(auth)),frame('Z',Buffer.from('I'))]));}
   while(buffer.length>=5){const size=buffer.readInt32BE(1);if(buffer.length<size+1)return;const tag=String.fromCharCode(buffer[0]);buffer=buffer.subarray(size+1);if(tag==='S')onQuery(socket)}
  });
 });
 await new Promise<void>(resolve=>server.listen(0,'127.0.0.1',resolve));
 return {port:(server.address() as any).port,async close(){for(const socket of sockets)socket.destroy();await new Promise<void>(resolve=>server.close(()=>resolve()))}};
}
function successful(socket:Socket,count='1'){
 const metadata=Buffer.concat([n32(0),n16(0),n32(25),n16(-1),n32(-1),n16(0)]);
 const value=Buffer.from('9007199254740993123');
 socket.write(Buffer.concat([frame('1',Buffer.alloc(0)),frame('2',Buffer.alloc(0)),frame('T',Buffer.concat([n16(1),z('exact'),metadata])),frame('D',Buffer.concat([n16(1),n32(value.length),value])),frame('C',z('SELECT '+count)),frame('Z',Buffer.from('I'))]));
}
test('exact text frames and native OID25 Bind are retained without numeric decoding',async()=>{
 const server=await fixture(0,successful);let probe:LocalPgProbe|undefined;
 try {probe=await LocalPgProbe.connect(server.port);const result=await probe.query('SELECT $1::text',['雪🙂']);
  expect(result.rows).toEqual([['9007199254740993123']]);expect(result.command).toBe('SELECT 1');
  const parse=Buffer.from(result.originalRequestFrames[0],'base64');expect(parse.readInt32BE(parse.length-4)).toBe(25);
  expect(Buffer.from(result.originalRequestFrames[1],'base64').includes(Buffer.from('雪🙂'))).toBe(true);
  expect(result.originalFrames.length).toBe(6);
 }finally{probe?.close();await server.close()}
});
test('native SELECT count mismatch closes original connection',async()=>{
 const server=await fixture(0,socket=>successful(socket,'2'));let probe:LocalPgProbe|undefined;
 try{probe=await LocalPgProbe.connect(server.port);await expect(probe.query('SELECT 1')).rejects.toThrow('Original SELECT count mismatch');await expect(probe.query('SELECT 1')).rejects.toThrow('Closed or busy')}
 finally{probe?.close();await server.close()}
});
test('password authentication refuses without credentials or fallback',async()=>{
 const server=await fixture(3,()=>{throw Error('unexpected query')});
 try{await expect(LocalPgProbe.connect(server.port)).rejects.toThrow('Only local trust-auth profile supported')}finally{await server.close()}
});
