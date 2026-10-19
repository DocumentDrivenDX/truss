# SPDX-License-Identifier: MIT OR Apache-2.0
"""Basic real Bun pipe workflow; no semantic/native security support claim."""
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch
from truss._current_query_pipe import CurrentQueryPipe, CurrentQueryPipeError, _envelope


class CurrentQueryPipeTests(unittest.TestCase):
    def test_numeric_envelope_id_does_not_become_text(self):
        with self.assertRaises(CurrentQueryPipeError):
            _envelope(b'{"requestId":1e3}')

    def test_original_frames_share_child_and_retain_exact_response(self):
        bun = shutil.which('bun') or '/opt/homebrew/bin/bun'
        if not Path(bun).is_file():
            self.skipTest('Bun required')
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / 'echo.ts'
            source.write_text('''import {readSync,writeSync} from 'node:fs';
function read(n){const b=Buffer.alloc(n);let at=0;while(at<n){const k=readSync(0,b,at,n-at,null);if(!k)process.exit(0);at+=k;}return b;}
for(;;){const h=read(4),body=read(h.readUInt32BE(0)),v=JSON.parse(body.toString('utf8'));
const out=Buffer.from(JSON.stringify({requestId:v.requestId,kind:'echo',sourceReceipt:v.sourceReceipt,original:v.value}));
const header=Buffer.alloc(4);header.writeUInt32BE(out.length);writeSync(1,header);writeSync(1,out);}
''')
            with CurrentQueryPipe((bun, str(source))) as child:
                for i in range(2):
                    value = {'requestId': 'call-' + str(i), 'sourceReceipt':'a'*64, 'value': {'decimalToken': '9007199254740993.0001'}}
                    raw = json.dumps(value, separators=(',', ':')).encode()
                    result = child.exchange(raw, source_receipt='a'*64)
                    self.assertEqual(result, json.dumps({'requestId':value['requestId'], 'kind':'echo', 'sourceReceipt':'a'*64,
                                                         'original':value['value']}, separators=(',', ':')).encode())
                with patch.object(child._child, 'kill', side_effect=PermissionError('temporary containment failure')):
                    with self.assertRaises(PermissionError):
                        child.close()
                self.assertIsNone(child._child.poll())
                self.assertFalse(child._cleanup_complete)
                child.close()
                self.assertIsNotNone(child._child.poll())
                self.assertTrue(child._cleanup_complete)
                with self.assertRaises(CurrentQueryPipeError):
                    child.exchange(raw, source_receipt='a'*64)
                with self.assertRaises(CurrentQueryPipeError):
                    child.exchange(b'{"requestId":"fresh"}', source_receipt='a'*64)
