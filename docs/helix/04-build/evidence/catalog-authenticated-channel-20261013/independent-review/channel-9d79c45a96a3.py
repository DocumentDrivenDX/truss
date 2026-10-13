"""One admitted local authenticated publication channel; not backend readiness.

The trusted owner supplies a private random credential and the original guarded
operation. TLS, credential issuance/rotation, isolated SQL topology and complete
endpoint/authority lifetime remain separate qualification obligations.
"""
from http.server import BaseHTTPRequestHandler,HTTPServer
import hmac
from truss.execution import Ok

REQUEST=b'{"operation":"read-resource"}'
ROUTE='/protected/read'

class AuthenticatedReadChannel(HTTPServer):
    def __init__(self,credential,operation):
        if type(credential) is not bytes or len(credential)!=32 or not callable(operation):
            raise ValueError('Private exact 256-bit credential and original operation required')
        self._authorization='Bearer '+credential.hex()
        self._operation=operation
        self._consumed=False
        self._failure=None
        self._outcome=None
        super().__init__(('127.0.0.1',0),_Handler)

    def get_request(self):
        connection,address=super().get_request()
        connection.settimeout(5)
        return connection,address

class _Handler(BaseHTTPRequestHandler):
    server_version='truss-protected-channel/0.1'
    sys_version=''
    def log_message(self,*args):pass

    def _deny(self,status):
        self.close_connection=True
        self.send_response(status)
        self.send_header('Content-Type','application/json')
        self.send_header('Content-Length','2')
        self.end_headers()
        if self.command!='HEAD':self.wfile.write(b'{}');self.wfile.flush()

    def _dispatch(self):
        self.close_connection=True
        credentials=self.headers.get_all('Authorization') or []
        if (len(credentials)!=1 or type(credentials[0]) is not str
                or len(credentials[0])!=71 or not credentials[0].isascii()
                or not hmac.compare_digest(credentials[0],self.server._authorization)):
            self._deny(401);return
        allowed={'host','authorization','content-type','content-length','connection','accept','accept-encoding'}
        if (self.command!='POST' or self.path!=ROUTE or self.request_version!='HTTP/1.1'
                or any(name.lower() not in allowed for name in self.headers.keys())
                or self.headers.get_all('Content-Length')!=[str(len(REQUEST))]
                or self.headers.get_all('Content-Type')!=['application/json']
                or self.headers.get_all('Accept-Encoding') not in (None,['identity'])
                or self.server._consumed):
            self._deny(403);return
        try:body=self.rfile.read(len(REQUEST))
        except (TimeoutError,OSError):self._deny(403);return
        if body!=REQUEST:self._deny(403);return
        # One original operation; failed/uncertain publication is never retried.
        self.server._consumed=True
        started=False;packet=None
        def publish(value):
            nonlocal started,packet
            if started or type(value) is not bytes or not 1<=len(value)<=1048576:
                raise ValueError('One bounded immutable original publication packet required')
            started=True;packet=value
            self.send_response(200)
            self.send_header('Content-Type','application/json')
            self.send_header('Content-Length',str(len(value)))
            self.end_headers()
            self.wfile.write(value);self.wfile.flush()
        try:
            result=self.server._operation(publish)
            self.server._outcome=result
            if type(result) is not Ok or not started or type(result.value) is not bytes or result.value!=packet:
                raise ValueError('Original publication completion required')
        except BaseException as error:
            self.server._failure=error
            if not started:
                try:self._deny(503)
                except OSError:pass
            # After any delivery uncertainty close; do not append an error packet.
            self.close_connection=True

    do_POST=_dispatch
    do_GET=_dispatch
    do_HEAD=_dispatch
    do_PUT=_dispatch
    do_PATCH=_dispatch
    do_DELETE=_dispatch
    do_OPTIONS=_dispatch
