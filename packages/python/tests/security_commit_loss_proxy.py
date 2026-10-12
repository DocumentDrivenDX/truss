"""Owned local fixture relay: drop native COMMIT response, never forge SQLSTATE.
Stock psycopg/libpq runs unchanged. Not a production transport or recovery service.
"""
import select,socket,struct,threading

class CommitResponseDropProxy:
 def __init__(self,parameters):
  host=parameters.get('host','');port=int(parameters.get('port',5432))
  if not host.startswith('/'):
   raise ValueError('Owned local Unix-socket server required')
  self.path=host+'/.s.PGSQL.'+str(port)
  self.listener=socket.socket();self.listener.bind(('127.0.0.1',0));self.listener.listen(1);self.listener.settimeout(10)
  self.port=self.listener.getsockname()[1];self.client=None;self.backend=None
  self.armed=threading.Event();self.dropped=threading.Event();self.stop=threading.Event();self.errors=[]
  self.thread=threading.Thread(target=self._run);self.thread.start()
 def _run(self):
  try:
   self.client,_=self.listener.accept();self.client.settimeout(10)
   self.backend=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM);self.backend.settimeout(10);self.backend.connect(self.path)
   pending=b''
   while not self.stop.is_set():
    ready,_,_=select.select([self.client,self.backend],[],[],.1)
    for connection in ready:
     chunk=connection.recv(65536)
     if not chunk:return
     if connection is self.client:self.backend.sendall(chunk);continue
     pending+=chunk
     while len(pending)>=5:
      length=struct.unpack('!I',pending[1:5])[0]
      if not 4<=length<=1048576:raise ValueError('Unqualified fixture backend frame')
      if len(pending)<length+1:break
      frame,pending=pending[:length+1],pending[length+1:]
      if self.armed.is_set() and frame[:1]==b'C' and frame[5:]==b'COMMIT\0':
       self.dropped.set();return
      self.client.sendall(frame)
  except BaseException as error:
   if not self.stop.is_set():self.errors.append(type(error).__name__)
  finally:
   for connection in [self.client,self.backend]:
    if connection is not None:
     try:connection.shutdown(socket.SHUT_RDWR)
     except OSError:pass
     connection.close()
 def close(self):
  self.stop.set()
  for connection in [self.listener,self.client,self.backend]:
   if connection is not None:
    try:connection.shutdown(socket.SHUT_RDWR)
    except OSError:pass
    connection.close()
  self.thread.join(2)
  if self.thread.is_alive():raise RuntimeError('Owned fixture relay unresolved')
