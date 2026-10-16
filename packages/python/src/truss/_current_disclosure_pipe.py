"""Explicit candidate transport capacity; no source/semantic/native admission.

The legacy pipe remains fixed at4MiB. Only the separate0.2 disclosure profile's
post-native inspection command may carry16MiB, sharing the original process,
receipt, deadline, correlation and failure/cleanup behavior.
"""
from ._current_query_pipe import CurrentQueryPipe,CurrentQueryPipeError,_envelope

VERSION='umf.security.private-disclosure-child/0.2-candidate'

class CurrentDisclosurePipe(CurrentQueryPipe):
    def _request_capacity(self,request):
        if len(request)>16*1024*1024:
            raise CurrentQueryPipeError('Bounded original disclosure request required')
        envelope=_envelope(request)
        if envelope.get('version')!=VERSION or envelope.get('kind') not in (
                'initialize','evaluate-disclosure','inspect-native-disclosure'):
            raise CurrentQueryPipeError('Explicit original disclosure protocol required')
        return (16 if envelope['kind']=='inspect-native-disclosure' else 4)*1024*1024
