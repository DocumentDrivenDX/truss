"""Synthetic frozen-core call-sequence witness; not native qualification."""
import hashlib
import json
from pathlib import Path
import sys

import pg8000.core as core
from pg8000_accounted_instance_candidate import AccountedFrameFile
from truss._resource_account import BytePermitAccount


class Transport:
    def __init__(self, data):
        self.data = data
        self.calls = 0

    def recv_into(self, view):
        self.calls += 1
        count = min(len(view), len(self.data))
        view[:count] = self.data[:count]
        self.data = self.data[count:]
        return count


def main():
    destination = Path(sys.argv[1])
    if destination.exists():
        raise ValueError('Fresh receipt required')
    core_path = Path(core.__file__)
    core_hash = hashlib.sha256(core_path.read_bytes()).hexdigest()
    assert core_hash == 'cac1e50502901bcea3ddab588e0350149dd8fd771156ae1c531a2a04b3925e26'
    # Two independently authored frames: body five bytes versus body one byte.
    first = b'D\x00\x00\x00\x09abcde'
    second = b'Z\x00\x00\x00\x05T'
    producer = object()
    account = BytePermitAccount(producer, 16777216, 33554432, 100)
    transport = Transport(first + second)
    file = AccountedFrameFile(transport, account, producer)
    header = core._read(file, 5)
    body = core._read(file, 5)
    before = transport.calls
    repeated_body_length_result = core._read(file, 5)
    assert (header, body, repeated_body_length_result) == (first[:5], first[5:], second[:5])
    assert transport.calls > before
    file.close()
    sources = [Path(__file__), Path(__file__).with_name('pg8000_accounted_instance_candidate.py'),
               Path(sys.modules[BytePermitAccount.__module__].__file__)]
    receipt = {
        'schema': 'truss-pg8000-read-phase-alias/0.1',
        'python': sys.version, 'coreSource': str(core_path), 'coreSha256': core_hash,
        'sources': [{'path': str(path), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()} for path in sources],
        'inputHex': (first + second).hex(), 'requestedLengths': [5, 5, 5],
        'returnedHex': [header.hex(), body.hex(), repeated_body_length_result.hex()],
        'ingressCallsBeforeThirdRead': before, 'ingressCallsAfterThirdRead': transport.calls,
        'accountAfterClose': account.snapshot(producer),
        'observation': 'Length alone cannot distinguish repeated five-byte body from next header',
        'scope': 'Actual pinned core _read with synthetic transport and manually scheduled calls; no CoreConnection/native cycle',
        'driverQualified': False, 'nativeSequenceFailureProven': False,
    }
    with destination.open('x') as output:
        json.dump(receipt, output, indent=2)
        output.write('\n')


if __name__ == '__main__':
    main()
