"""Build a committed Weft source tree without reading its working-tree edits."""
import pathlib,subprocess,tarfile,io,hashlib,json,os,sys
revision='f05f2df09e9c2494ac8c6d703dfe38413dbc4181'
if len(sys.argv)!=4:raise SystemExit('usage: build-weft-source.py REPOSITORY OUTPUT TOOLCHAIN_ROOT')
repository,output,toolchain=map(pathlib.Path,sys.argv[1:]);output=output.resolve()
if output.exists() and any(output.iterdir()):raise SystemExit('Output must be empty to prevent source substitution')
output.mkdir(parents=True,exist_ok=True)
archive=subprocess.check_output(['git','-C',str(repository),'archive',revision])
with tarfile.open(fileobj=io.BytesIO(archive)) as tree:
 for member in tree.getmembers():
  if member.name.startswith('/') or '..' in pathlib.PurePosixPath(member.name).parts or member.issym() or member.islnk():raise SystemExit('Unsafe archive member')
 tree.extractall(output)
env=dict(os.environ,CARGO_HOME=str(toolchain/'cargo'),RUSTUP_HOME=str(toolchain/'rustup'))
env['PATH']=str(toolchain/'cargo/bin')+os.pathsep+env.get('PATH','')
subprocess.run([str(toolchain/'cargo/bin/cargo'),'build','--locked','--offline','-p','weft-runtime','--features','truss-postgresql-qualified'],cwd=output,env=env,check=True)
exe=output/'target/debug/weft-runtime'
manifest={'revision':revision,'feature':'truss-postgresql-qualified','archiveSha256':hashlib.sha256(archive).hexdigest(),'cargoLockSha256':hashlib.sha256((output/'Cargo.lock').read_bytes()).hexdigest(),'executableSha256':hashlib.sha256(exe.read_bytes()).hexdigest(),'qualification':'Pinned compiler build; not installed Truss/native host qualification'}
(output/'truss-weft-build.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps(manifest,indent=2))
