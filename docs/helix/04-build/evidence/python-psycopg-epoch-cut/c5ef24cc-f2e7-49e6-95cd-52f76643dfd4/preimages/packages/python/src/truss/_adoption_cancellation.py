"""Private executor-issued persistent adoption signal; no native outcome claims."""
from threading import RLock

class AdoptionCancellation:
    def __init__(self,owner):
        self._owner=owner
        self._lock=RLock()
        self._custody=None
        self._requested=False
        self._active=None
    def request(self):
        with self._lock:
            self._requested=True
            child=self._active
        # Never hold the context lock while entering native dispatch locks.
        return child.request() if child is not None else 'latched'
    def requested(self):
        with self._lock:return self._requested
    def bind(self,owner,custody):
        with self._lock:
            if owner is not self._owner or self._custody is not None:return False
            self._custody=custody
            return True
    def attach(self,custody,child):
        with self._lock:
            if custody is not self._custody or self._active is not None:return False
            self._active=child
            requested=self._requested
        if requested:child.request()
        return True
    def detach(self,custody,child):
        with self._lock:
            if custody is not self._custody or self._active is not child:return False
            self._active=None
            return True
