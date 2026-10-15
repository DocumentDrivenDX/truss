from pathlib import Path
import struct,subprocess
p=Path('/private/tmp/weft-db-compat-site/weft/weft.abi3.so')
subprocess.run(['/usr/bin/codesign','--remove-signature',str(p)],check=True)
b=bytearray(p.read_bytes());n=struct.unpack_from('<I',b,16)[0];off=32;commands=[]
for _ in range(n):
 cmd,size=struct.unpack_from('<II',b,off);commands.append((cmd,off));off+=size
sym=next(o for c,o in commands if c==2);stroff=struct.unpack_from('<I',b,sym+16)[0];pad=(-stroff)%8
if pad:
 b[stroff:stroff]=b'\0'*pad
 struct.pack_into('<I',b,sym+16,stroff+pad)
 for cmd,o in commands:
  if cmd==0x19 and b[o+8:o+24].rstrip(b'\0')==b'__LINKEDIT':
   vmsize=struct.unpack_from('<Q',b,o+32)[0];filesize=struct.unpack_from('<Q',b,o+48)[0]
   struct.pack_into('<Q',b,o+48,filesize+pad)
   if filesize+pad>vmsize:struct.pack_into('<Q',b,o+32,((filesize+pad+16383)//16384)*16384)
 p.write_bytes(b)
subprocess.run(['/usr/bin/codesign','--force','--sign','-',str(p)],check=True)
print('Aligned Mach-O string pool by',pad,'bytes')
