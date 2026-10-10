"""Private native original-generation adoption claim; no public E06 claim.

The native generation owns the authoritative immutable claim root. Executor
indices cannot grant admission before its original claim publishes. Uncertain
observation/publication retains custody; disposal cannot refund it. Full shared
operation/resource recovery integration remains required.
"""
from dataclasses import dataclass, replace, field
from uuid import uuid4
from .execution import Ok, TransactionObservation


@dataclass
class _Capture:
    native: object = None
    reservation_failed: bool = False
    probe_revision: int | None = None


@dataclass(frozen=True, eq=False)
class _Claim:
    executor: object
    port: object
    generation: object
    token: object
    custody: object
    success: object
    refusal: object
    capture: _Capture = field(default_factory=_Capture)


@dataclass(frozen=True)
class _Record:
    claim: _Claim
    phase: str = 'observing'
    native_observation: object = None


@dataclass(frozen=True)
class _Root:
    current: _Record | None = None
    retained: tuple = ()


def _publish_root(generation, root):
    """One original publication point, also used for deterministic fault tests."""
    generation.adoption = root


def _reserve(port, executor, custody, success, refusal):
    from ._native_pg8000 import NativeBoundaryRefusal
    t, g = port._tracker, port._generation
    with t._boundary._lock:
        port._require_scope()
        if (executor._closed or g.ended or g is not t._state.generation or
                t._state.status != b'T' or t._boundary._calling):
            raise NativeBoundaryRefusal('Original active adoption scope unavailable')
        root = g.adoption or _Root()
        if root.current is not None:
            raise NativeBoundaryRefusal('Original generation already claimed')
        if len(t._adoption_custody) >= t._adoption_limit:
            raise NativeBoundaryRefusal('Original adoption retention exhausted')
        with executor._lifecycle_lock:
            if executor._closed or len(executor._native_claims) >= executor._native_claim_limit:
                raise NativeBoundaryRefusal('Original executor adoption retention unavailable')
            claim = _Claim(executor, port, g, port._token, custody, success, refusal)
            native_retention = t._adoption_custody + (claim,)
            executor_retention = executor._native_claims + (claim,)
            # Both stable owners retain original custody before observation,
            # including a reservation whose root publication loses its reply.
            t._adoption_custody = native_retention
            executor._native_claims = executor_retention
        record = _Record(claim)
        _publish_root(g, _Root(record, root.retained))
        return claim


def _current(claim):
    root = claim.generation.adoption
    if root is None or root.current is None or root.current.claim is not claim:
        raise RuntimeError('Original adoption claim lost')
    return root


def _corresponds(claim, native):
    p, g = claim.port, claim.generation
    t, b = p._tracker, p._tracker._boundary
    return (not b._quarantined and not b._calling and not claim.executor._closed
            and not g.ended and t._state.generation is g and t._state.status == b'T'
            and p._token is claim.token and b._operation is claim.token
            and native.port is p and native.generation is g and native.token is claim.token
            and native.call is b.last_call and native.revision == b._revision
            and native.call.capture_complete and native.call.final_status == b'T'
            and claim.capture.native is native)


def start_probe(claim, port):
    """One exact adoption probe capability consumed at native call admission."""
    from ._native_pg8000 import NativeBoundaryRefusal
    if type(claim) is not _Claim or claim.port is not port:
        raise NativeBoundaryRefusal('Original adoption probe capability required')
    root = _current(claim)
    if (root.current.phase != 'observing' or claim.capture.probe_revision is not None or
            claim.token is not port._token or claim.generation is not port._tracker._state.generation):
        raise NativeBoundaryRefusal('Original adoption probe unavailable or already consumed')
    claim.capture.probe_revision = port._tracker._boundary._revision + 1


def capture_original(claim, port, native):
    """Exact probe handoff under native guard; generic observe has no claim."""
    from ._native_pg8000 import NativeBoundaryRefusal
    root = _current(claim)
    if not (root.current.phase == 'observing' and claim.port is port and
            claim.token is native.token and claim.generation is native.generation and
            claim.capture.probe_revision == native.revision and claim.capture.native is None):
        raise NativeBoundaryRefusal('Native completion does not correspond to original adoption probe')
    claim.capture.native = native
    _publish_root(claim.generation, replace(root, current=replace(root.current,
                  phase='observed', native_observation=native)))


def _retain_unknown(claim):
    with claim.port._tracker._boundary._lock:
        root = claim.generation.adoption
        if root is not None:
            terminal = next((item for item in root.retained if item.claim is claim), None)
            if terminal is not None and terminal.phase == 'profile_refused':
                return claim.refusal
            if root.current is not None and root.current.claim is claim:
                if root.current.phase == 'published':
                    return claim.success
                claim.custody.usable = False
                _publish_root(claim.generation, replace(root, current=replace(root.current,
                              phase='unresolved', native_observation=claim.capture.native)))
                return None
        # Reservation publication failed before its root existed. No SQL was
        # submitted; retain its stable owner record without altering a later owner.
        claim.custody.usable = False
        claim.capture.reservation_failed = True
        return None


def is_published(generation, custody):
    root = generation.adoption
    return (root is not None and root.current is not None and
            root.current.phase == 'published' and root.current.claim.custody is custody)


def adopt(executor, port, *, isolation, access_mode):
    from ._host_contracts import TransactionHandle, _Adoption
    from ._native_pg8000 import NativeBoundaryRefusal
    # Allocate the issued handle, original custody and success result before any
    # native observation or final publication. Unpublished custody is inert.
    key = uuid4().hex
    handle = TransactionHandle(executor._issuer, key, isolation, access_mode)
    custody = _Adoption(port, None, handle)
    success = Ok(handle)
    refusal = executor._error('invalid_transaction', 'Actual transaction profile does not match')
    try:
        claim = _reserve(port, executor, custody, success, refusal)
    except NativeBoundaryRefusal:
        return executor._error('invalid_transaction', 'Original native generation unavailable or already claimed')
    except BaseException as error:
        # A reservation publisher can lose its reply after installing the root.
        # Locate only this exact preallocated custody; never alter another owner.
        with port._tracker._boundary._lock:
            original_claim = next((item for item in port._tracker._adoption_custody
                                   if item.custody is custody), None)
        if original_claim is not None:
            _retain_unknown(original_claim)
        if isinstance(error, Exception):
            return executor._error('transaction_unusable', 'Original adoption reservation unavailable')
        raise
    try:
        observed = port._observe_for_adoption(claim)
        b = port._tracker._boundary
        with b._lock:
            root = _current(claim)
            native = claim.capture.native
            if (native is None or native.observation is not observed or
                    type(observed) is not TransactionObservation or native.port is not port or
                    native.generation is not claim.generation or native.token is not claim.token):
                raise NativeBoundaryRefusal('Original observation producer correspondence unavailable')
            # Retain original completed evidence before checking whether a later
            # coordinated call has invalidated its admission revision.
            custody.observation = observed
            root = replace(root, current=replace(root.current, phase='observed', native_observation=native))
            _publish_root(claim.generation, root)
            if not _corresponds(claim, native):
                raise NativeBoundaryRefusal('Original observation revision no longer owns publication')
            if observed.isolation != isolation or observed.access_mode != access_mode:
                # Proven nonpublication + unchanged completed observation permits
                # only this exact claim to refund; retain its refusal history.
                refused = replace(root.current, phase='profile_refused')
                _publish_root(claim.generation, _Root(None, root.retained + (refused,)))
                return refusal
            with executor._lifecycle_lock:
                if not _corresponds(claim, native):
                    raise NativeBoundaryRefusal('Original observation changed before publication')
                executor._transactions[key] = custody
                # This root, rather than the executor index, grants admission.
                _publish_root(claim.generation, replace(root, current=replace(root.current, phase='published')))
        return success
    except BaseException as error:
        known = _retain_unknown(claim)
        if isinstance(error, Exception) and known is not None:
            return known
        if isinstance(error, Exception):
            return executor._error('transaction_unusable', 'Original adoption observation/publication unresolved')
        raise
