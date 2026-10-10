"""Private host byte-permit bookkeeping, not allocator/native metering.

The trusted producer supplies original allocation-release and termination facts.
No database authority, actual heap bound or recovery observation is manufactured.
"""
from dataclasses import dataclass
from threading import Lock


@dataclass(frozen=True, eq=False)
class BytePermit:
    pass


@dataclass(frozen=True, eq=False)
class ByteAllocation:
    pass


class BytePermitAccount:
    def __init__(self, producer, capacity, cumulative_allocation, maximum_records):
        for value in (capacity, cumulative_allocation, maximum_records):
            if type(value) is not int or value < 0:
                raise ValueError('Exact nonnegative bound required')
        if producer is None:
            raise ValueError('Original producer required')
        self._producer = producer
        self._capacity = capacity
        self._cumulative_limit = cumulative_allocation
        self._maximum_records = maximum_records
        self._permits = {}
        self._allocations = {}
        self._owned = self._reserved = self._spent = 0
        self._closed = False
        self._lock = Lock()

    def _original(self, producer):
        if producer is not self._producer:
            raise ValueError('Original producer required')

    @staticmethod
    def _amount(amount):
        if type(amount) is not int or amount < 0:
            raise ValueError('Exact nonnegative byte amount required')

    def reserve(self, producer, amount):
        self._amount(amount)
        with self._lock:
            self._original(producer)
            if self._closed:
                raise ValueError('Account closed')
            if len(self._permits) + len(self._allocations) >= self._maximum_records:
                self._closed = True
                raise ValueError('Record capacity exhausted')
            if self._owned + self._reserved + amount > self._capacity:
                self._closed = True
                raise ValueError('Live byte capacity exhausted')
            if self._spent + self._reserved + amount > self._cumulative_limit:
                self._closed = True
                raise ValueError('Cumulative allocation capacity exhausted')
            permit = BytePermit()
            self._permits[permit] = [amount, False]
            self._reserved += amount
            return permit

    def allocate(self, producer, permit, amount):
        """Draw down before the trusted producer allocates/hands off bytes."""
        self._amount(amount)
        if type(permit) is not BytePermit:
            raise ValueError('Original byte permit required')
        with self._lock:
            self._original(producer)
            state = self._permits.get(permit)
            if self._closed or state is None or state[1]:
                raise ValueError('Original open permit required')
            if amount > state[0] or len(self._permits) + len(self._allocations) >= self._maximum_records:
                self._closed = True
                raise ValueError('Allocation overrun; original custody retained')
            allocation = ByteAllocation()
            self._allocations[allocation] = [amount, False]
            state[0] -= amount
            self._reserved -= amount
            self._owned += amount
            self._spent += amount
            return allocation

    def release(self, producer, allocation):
        """Producer asserts original allocation no longer has any consumer."""
        if type(allocation) is not ByteAllocation:
            raise ValueError('Original byte allocation required')
        with self._lock:
            self._original(producer)
            state = self._allocations.get(allocation)
            if state is None or state[1]:
                raise ValueError('Original unreleased allocation required')
            state[1] = True
            self._owned -= state[0]

    def terminate(self, producer, permit):
        """Producer confirms no further work can consume the original permit."""
        if type(permit) is not BytePermit:
            raise ValueError('Original byte permit required')
        with self._lock:
            self._original(producer)
            state = self._permits.get(permit)
            if state is None or state[1]:
                raise ValueError('Original unterminated permit required')
            self._reserved -= state[0]
            state[0] = 0
            state[1] = True

    def close(self, producer):
        with self._lock:
            self._original(producer)
            self._closed = True
            # Unknown allocations/permits remain retained and charged.

    def snapshot(self, producer):
        with self._lock:
            self._original(producer)
            return (self._owned, self._reserved, self._spent, self._closed)
