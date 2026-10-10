"""Private pinned resource capture; not complete index or installer admission.

Only a trusted registered resource handle supplies open/read. This component
charges the declared read bound, not actual interpreter/decoder/hash workspace.
"""
from dataclasses import dataclass
from hashlib import sha256
from ._resource_account import ByteAllocation, BytePermitAccount


@dataclass(frozen=True, eq=False)
class ResourceCapture:
    original: bytes
    allocation: ByteAllocation
    account: BytePermitAccount


def capture_resource(resource, expected_length, expected_sha256, maximum_length,
                     account, producer):
    """Read once through a complete bounded binary-read handle, retaining bytes.

    The independently selected entry/profile supplies lengths and digest. No
    path lookup, package index selection, database submission or retry occurs.
    On read/close/correspondence failure, quarantine the original charge.
    """
    if (type(expected_length) is not int or type(maximum_length) is not int
            or expected_length < 0 or maximum_length < 0
            or expected_length > maximum_length):
        raise ValueError('Selected exact resource length bound required')
    if (type(expected_sha256) is not str or len(expected_sha256) != 64
            or any(c not in '0123456789abcdef' for c in expected_sha256)):
        raise ValueError('Independent exact resource digest required')
    # One sentinel byte distinguishes exact EOF from an appended payload.
    bound = expected_length + 1
    permit = account.reserve(producer, bound)
    allocation = account.allocate(producer, permit, bound)
    try:
        with resource.open('rb') as stream:
            original = stream.read(bound)
        if type(original) is not bytes or len(original) != expected_length:
            raise ValueError('Resource byte length mismatch')
        if sha256(original).hexdigest() != expected_sha256:
            raise ValueError('Resource digest mismatch')
        account.terminate(producer, permit)
        return ResourceCapture(original, allocation, account)
    except BaseException:
        # Error/close/termination does not establish safe release of all views.
        account.close(producer)
        raise
