# SPDX-License-Identifier: MIT OR Apache-2.0
"""Owned ephemeral local certificate; no production issuer/key qualification."""
from pathlib import Path
import tempfile,subprocess,ssl

def owned_tls(test):
 directory=tempfile.TemporaryDirectory(prefix='truss-channel-tls-',dir='/private/tmp');test.addCleanup(directory.cleanup)
 root=Path(directory.name);certificate=root/'certificate.pem';key=root/'private-key.pem'
 subprocess.run(['openssl','req','-x509','-newkey','rsa:2048','-nodes','-keyout',str(key),'-out',str(certificate),'-days','1','-subj','/CN=127.0.0.1','-addext','subjectAltName=IP:127.0.0.1'],check=True,capture_output=True,timeout=20)
 key.chmod(0o600)
 server=ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER);server.minimum_version=ssl.TLSVersion.TLSv1_3;server.load_cert_chain(certificate,key)
 client=ssl.create_default_context(cafile=str(certificate));client.minimum_version=ssl.TLSVersion.TLSv1_3
 return server,client
