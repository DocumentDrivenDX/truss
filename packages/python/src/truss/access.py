"""Typed SDK reads through Truss-owned transactions and original native admission.

The host supplies a bounded operation context, not a borrowed SQL connection.
Catalog custody never substitutes for Truss authorization or native query scope.
"""
from __future__ import annotations
from collections.abc import Callable, Generator
from contextlib import AbstractContextManager
from datetime import timedelta
from time import monotonic
from typing import Any, TypeVar
import hashlib,json
from pydantic import BaseModel
from umf_access.adoption import TargetIdentity
from umf_access.engine_catalog import EngineRead
from umf_access.reviewed import CatalogRead
from umf_access.pages import ReadPage, ReadContinuation, StaleContinuation
from umf_access.codec_support import revalidate_model
from umf_access.postgres_read import TimedOut
from .execution import Ok
from .query import QueryRows, QueryAbsent, QueryCatalogSources, QueryPage, QueryPageCursor
from umf_access.native_program import program_json, canonical_json
P=TypeVar('P',bound=BaseModel);R=TypeVar('R',bound=BaseModel)

class TrussReadRefused(ValueError):
    def __init__(self, original: object):
        self.original=original
        super().__init__('Truss refused the original typed read; inspect original outcome')

class TrussTarget:
    """RC module-access reads. Protected current-policy adoption is separate.

    operation(timeout) must own an adopted transaction whose native statement
    and whole-operation deadlines do not exceed timeout. Its exit settles the
    transaction and may refuse release; rows escape only after successful exit.
    """
    def __init__(self, operation: Callable[[timedelta],AbstractContextManager[tuple[Any,Any]]], *,
                 binding_sha256: str, platform: tuple[tuple[str,str],...],
                 default_timeout: timedelta, catalog_entries: tuple[EngineRead[Any,Any],...]=(),
                 catalog_sources: QueryCatalogSources | None=None,
                 stream_operation: Callable[[timedelta],AbstractContextManager[tuple[Any,Any]]] | None=None):
        if len(binding_sha256)!=64 or any(c not in '0123456789abcdef' for c in binding_sha256):
            raise ValueError('original native binding SHA-256 required')
        if not platform or not callable(operation):raise ValueError('host operation and native platform pins required')
        if stream_operation is not None and not callable(stream_operation):raise TypeError("Explicit owned stream operation required")
        self.stream_operation=stream_operation
        self.operation,self.binding_sha256,self.platform=operation,binding_sha256,platform
        self.default_timeout,self.catalog_entries=default_timeout,catalog_entries
        targets=[]
        if catalog_sources is not None:
            if type(catalog_sources)is not QueryCatalogSources or type(catalog_sources.request_json)is not str or len(catalog_sources.request_json.encode())>4_194_304:
                raise ValueError('bounded original native catalog sources required')
            captured=program_json(catalog_sources.request_json)
            if type(captured)is not dict:raise ValueError('original native request object required')
            targets.append(captured.get('target'))
        for entry in catalog_entries:
            if not isinstance(entry,EngineRead) or entry.artifact()['compiler']!='truss-runtime':
                raise ValueError('original Truss engine catalog required')
            targets.append(entry.artifact()['request']['target'])
        if not targets:raise ValueError('original native catalog sources or engine entries required')
        for target in targets:
            if (type(target)is not dict or target.get('backendId')!='truss.postgresql.runtime'
                or any(type(target.get(name))is not str or not target[name] or len(target[name])>256 for name in ('backendVersion','targetProfile'))
                or type(target.get('bindingJson'))is not str or target.get('bindingSha256')!=binding_sha256
                or hashlib.sha256(target['bindingJson'].encode()).hexdigest()!=binding_sha256):
                raise ValueError('complete original native target and binding required')
        if any(target!=targets[0] for target in targets[1:]):raise ValueError('native catalog targets differ')
        # Inert complete metadata, never a native admission or current-policy permit.
        self.native_target_json=canonical_json(targets[0])
        self.catalog_sources=catalog_sources
        self._budget(None)
    def _budget(self, timeout: timedelta | None)->timedelta:
        value=self.default_timeout if timeout is None else timeout
        if type(value) is not timedelta or not 0 < value.total_seconds() <= 2147483:
            raise TimedOut('positive bounded engine deadline required')
        return value
    def identity(self)->TargetIdentity:
        target=program_json(self.native_target_json)
        return TargetIdentity('truss',target['backendId'],target['backendVersion'],target['targetProfile'],self.binding_sha256,self.platform)
    def read(self,entry:CatalogRead[P,R],parameters:P,*,timeout:timedelta|None=None)->list[R]:
        if not isinstance(entry,EngineRead):raise ValueError('Truss requires an original engine catalog')
        program=entry.artifact();request=program['request'];target=request['target']
        if program['version']!='weft.engine-read/0.1':raise ValueError('original read catalog required')
        if program['compiler']!='truss-runtime' or target!=program_json(self.native_target_json):
            raise ValueError('Truss original backend or binding differs')
        values=revalidate_model(entry.parameters,parameters)
        budget=self._budget(timeout);deadline=monotonic()+budget.total_seconds()
        binding=json.loads(target['bindingJson'])
        documents=tuple(dict.fromkeys(m['pin']['documentId'] for m in request['modules']))
        with self.operation(budget) as (assembly,transaction):
            if monotonic()>=deadline:raise TimedOut('deadline expired before engine dispatch')
            outcome=assembly.query_in_transaction(transaction,sql=request['sql'],document_ids=documents,
                parameters=values.model_dump(mode='python'),maximum_rows=binding['maximumResultRows'],
                maximum_scan_rows=binding['maximumScanRows'],maximum_bytes=binding['maximumBytes'],engine_program=entry.originals())
            if not isinstance(outcome,Ok) or not isinstance(outcome.value,QueryRows):raise TrussReadRefused(outcome)
            native=outcome.value
            if native.columns!=tuple(entry.result.model_fields):raise ValueError('Truss complete ordered output signature differs')
            result=[]
            for row in native.rows:
                if len(row)!=len(native.columns) or any(isinstance(v,QueryAbsent) for v in row):
                    raise ValueError('ADOPTION_MISMATCH: selected column is absent or row shape differs')
                result.append(entry.result.model_validate(dict(zip(native.columns,row,strict=True))))
            if monotonic()>=deadline:raise TimedOut('deadline expired before engine release')
        if monotonic()>=deadline:raise TimedOut('deadline expired during engine release')
        return result
    def verify(self)->None:
        if not self.catalog_entries:raise ValueError('explicit engine catalog entries required')
        for entry in self.catalog_entries:
            # Verification runs the same original read and release path, never a
            # metadata-only authority shortcut. Samples are compiler inputs.
            request=entry.artifact()['request'];sample={}
            from decimal import Decimal
            for name,p in request['parameters'].items():
                family,value=p['family'],p['value']
                sample[name]={'string':lambda:value,'integer':lambda:int(value),'decimal':lambda:Decimal(value),'boolean':lambda:value=='true'}[family]()
            if entry.artifact()["version"]=="weft.engine-page/0.1":self.page(entry,entry.parameters.model_validate(sample))
            else:self.read(entry,entry.parameters.model_validate(sample))
    def page(self,entry:CatalogRead[P,R],parameters:P,*,after:ReadContinuation|None=None,timeout:timedelta|None=None)->ReadPage[R]:
        if not isinstance(entry,EngineRead):raise ValueError('original engine page catalog required')
        program=entry.artifact();request=program['request'];target=request['target']
        if program['version']!='weft.engine-page/0.1' or program['compiler']!='truss-runtime' or target!=program_json(self.native_target_json):
            raise ValueError('original Truss page backend or binding differs')
        values=revalidate_model(entry.parameters,parameters)
        identity=hashlib.sha256(canonical_json([self.identity().digest(),entry.artifact_json,entry.context_json,
            [(name,type(value).__name__,str(value)) for name,value in values.model_dump(mode='python').items()]]).encode()).hexdigest()
        cursor=None
        if after is not None:
            if type(after)is not ReadContinuation or after.identity_digest!=identity or after.owner_cursor is None:
                raise StaleContinuation('original native cursor and complete page context required')
            cursor=QueryPageCursor(after.owner_cursor,after.values)
        budget=self._budget(timeout);deadline=monotonic()+budget.total_seconds()
        binding=program_json(target['bindingJson'])
        documents=tuple(dict.fromkeys(m['pin']['documentId'] for m in request['modules']))
        with self.operation(budget) as (assembly,transaction):
            if monotonic()>=deadline:raise TimedOut('deadline expired before page dispatch')
            outcome=assembly.query_page_in_transaction(transaction,sql=request['sql'],document_ids=documents,
                parameters=values.model_dump(mode='python'),limit=program['pageSize'],cursor=cursor,
                maximum_rows=binding['maximumResultRows'],maximum_scan_rows=binding['maximumScanRows'],
                maximum_bytes=binding['maximumBytes'],engine_program=entry.originals())
            if not isinstance(outcome,Ok) or not isinstance(outcome.value,QueryPage):raise TrussReadRefused(outcome)
            native=outcome.value
            if native.columns!=tuple(entry.result.model_fields):raise ValueError('Truss complete ordered page output signature differs')
            rows=[]
            for row in native.rows:
                if len(row)!=len(native.columns) or any(isinstance(value,QueryAbsent) for value in row):
                    raise ValueError('ADOPTION_MISMATCH: selected page column absent or row shape differs')
                rows.append(entry.result.model_validate(dict(zip(native.columns,row,strict=True))))
            next_after=None
            if native.next_cursor is not None:
                if native.next_sort_values is None:raise ValueError('original typed native continuation keys required')
                next_after=ReadContinuation(native.next_sort_values,identity,native.next_cursor.original_bytes)
            result=ReadPage(tuple(rows),next_after)
            if monotonic()>=deadline:raise TimedOut('deadline expired before page release')
        if monotonic()>=deadline:raise TimedOut('deadline expired during page release')
        return result
    def stream(self,entry:CatalogRead[P,R],parameters:P,*,max_rows:int,timeout:timedelta|None=None)->Generator[R,None,None]:
        from .query_stream import QueryStreamTimedOut
        try:
            yield from self._stream_owned(entry,parameters,max_rows=max_rows,timeout=timeout)
        except QueryStreamTimedOut as error:
            raise TimedOut(str(error)) from error
    def _stream_owned(self,entry:CatalogRead[P,R],parameters:P,*,max_rows:int,timeout:timedelta|None=None)->Generator[R,None,None]:
        if type(max_rows) is not int or max_rows < 1:raise ValueError('positive required max_rows; no fixed ceiling')
        if self.stream_operation is None:raise ValueError('Explicit qualified owned stream operation required')
        if not isinstance(entry,EngineRead):raise ValueError('Original engine page program required')
        program=entry.artifact();request=program['request'];target=request['target']
        if program['version']!='weft.engine-page/0.1' or program['compiler']!='truss-runtime' or program.get('after') is not None or target!=program_json(self.native_target_json):
            raise ValueError('Complete initial original Truss page program required')
        values=revalidate_model(entry.parameters,parameters);budget=self._budget(timeout)
        def validate(native):
            if native.columns!=tuple(entry.result.model_fields):raise ValueError('Complete ordered stream DTO signature differs')
            result=[]
            for row in native.rows:
                if len(row)!=len(native.columns) or any(isinstance(value,QueryAbsent) for value in row):
                    raise ValueError('ADOPTION_MISMATCH: selected stream column absent or row shape differs')
                result.append(entry.result.model_validate(dict(zip(native.columns,row,strict=True))))
            return result
        final=();first_deadline=monotonic()+budget.total_seconds()
        with self.stream_operation(budget) as (assembly,transaction):
            handle=assembly.query_stream_open_in_transaction(transaction,engine_program=entry.originals(),parameters=values.model_dump(mode='python'),operation_deadline=first_deadline)
            remaining=max_rows
            try:
                while remaining:
                    deadline=first_deadline if remaining==max_rows else monotonic()+budget.total_seconds();count=min(program['pageSize'],remaining)
                    batch=assembly.query_stream_fetch_in_transaction(transaction,handle,count=count,validate=validate,operation_deadline=deadline,final_bound=remaining<=count)
                    if monotonic()>=deadline:raise TimedOut('stream page deadline expired before release')
                    remaining-=len(batch.items)
                    if batch.exhausted or remaining==0:
                        final=batch.items
                        break
                    yield from batch.items
                    # Do not retain a delivered page while fetching the next one.
                    del batch
            finally:
                assembly.query_stream_close_in_transaction(transaction,handle)
        # Both portal close and owned rollback settled before this final page or
        # normal completion becomes observable. Earlier pages remain a prefix.
        if monotonic()>=deadline:raise TimedOut('stream final page deadline expired during cleanup')
        yield from final
