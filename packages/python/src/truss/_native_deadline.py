"""Private original monotonic scheduling custody, not I/O termination proof."""
from time import monotonic_ns

class NativeDeadlineExpired(RuntimeError):
    pass

class NativeOperationDeadline:
    def __init__(self, ordinary_ms, settlement_ms):
        if any(type(x) is not int or x < 1 for x in (ordinary_ms, settlement_ms)):
            raise ValueError('Positive exact deadline allowances required')
        self.started_ns = monotonic_ns()
        self.ordinary_cutoff_ns = self.started_ns + ordinary_ms * 1000000
        self.settlement_ms = settlement_ms
        self.settlement_cutoff_ns = None
        self.accepted_basis = None

    def check(self):
        cutoff = (self.ordinary_cutoff_ns if self.settlement_cutoff_ns is None
                  else self.settlement_cutoff_ns)
        if monotonic_ns() >= cutoff:
            raise NativeDeadlineExpired('Original scheduling allowance expired')

    def begin_settlement(self):
        # One irreversible phase transition; neither cleanup calls nor later
        # recovery observations can restart the original allowance.
        if self.settlement_cutoff_ns is None:
            self.settlement_cutoff_ns = monotonic_ns() + self.settlement_ms * 1000000
        self.check()

    def seal(self):
        if self.accepted_basis is None:
            self.check()
            observed = monotonic_ns()
            cutoff = (self.ordinary_cutoff_ns if self.settlement_cutoff_ns is None
                      else self.settlement_cutoff_ns)
            if observed >= cutoff:
                raise NativeDeadlineExpired('Original completion allowance expired')
            self.accepted_basis = (self.started_ns, self.ordinary_cutoff_ns,
                                   self.settlement_cutoff_ns, observed)
        return self.accepted_basis

    def remaining_seconds(self):
        cutoff = (self.ordinary_cutoff_ns if self.settlement_cutoff_ns is None
                  else self.settlement_cutoff_ns)
        remaining = cutoff - monotonic_ns()
        if remaining <= 0:
            raise NativeDeadlineExpired('Original receive allowance expired')
        return remaining / 1000000000
