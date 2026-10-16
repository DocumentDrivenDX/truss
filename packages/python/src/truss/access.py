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
import json
from pydantic import BaseModel
from umf_access.adoption import TargetIdentity
from umf_access.engine_catalog import EngineRead
from umf_access.reviewed import CatalogRead
from umf_access.pages import ReadPage, ReadContinuation
from umf_access.codec_support import revalidate_model
from umf_access.postgres_read import TimedOut
from .execution import Ok
from .query import QueryRows, QueryAbsent
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
                 default_timeout: timedelta, catalog_entries: tuple[EngineRead[Any,Any],...]=()):
        if len(binding_sha256)!=64 or any(c not in '0123456789abcdef' for c in binding_sha256):
            raise ValueError('original native binding SHA-256 required')
        if not platform or not callable(operation):raise ValueError('host operation and native platform pins required')
        self.operation,self.binding_sha256,self.platform=operation,binding_sha256,platform
        self.default_timeout,self.catalog_entries=default_timeout,catalog_entries
        self._budget(None)
    def _budget(self, timeout: timedelta | None)->timedelta:
        value=self.default_timeout if timeout is None else timeout
        if type(value) is not timedelta or not 0 < value.total_seconds() <= 2147483:
            raise TimedOut('positive bounded engine deadline required')
        return value
    def identity(self)->TargetIdentity:
        return TargetIdentity('truss','truss.postgresql.runtime','0.4.39','truss-runtime-pg18.6/0.5',self.binding_sha256,self.platform)
    def read(self,entry:CatalogRead[P,R],parameters:P,*,timeout:timedelta|None=None)->list[R]:
        if not isinstance(entry,EngineRead):raise ValueError('Truss requires an original engine catalog')
        program=entry.artifact();request=program['request'];target=request['target']
        if program['compiler']!='truss-runtime' or target['bindingSha256']!=self.binding_sha256 or any(target[k]!=v for k,v in (('backendId','truss.postgresql.runtime'),('backendVersion','0.4.39'),('targetProfile','truss-runtime-pg18.6/0.5'))):
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
            self.read(entry,entry.parameters.model_validate(sample))
    def page(self,entry:CatalogRead[P,R],parameters:P,*,after:ReadContinuation|None=None,timeout:timedelta|None=None)->ReadPage[R]:
        raise ValueError('WEFT_BLOCKED: engine catalog page program required')
    def stream(self,entry:CatalogRead[P,R],parameters:P,*,max_rows:int,timeout:timedelta|None=None)->Generator[R,None,None]:
        raise ValueError('WEFT_BLOCKED: engine catalog bounded stream program required')
        yield  # retains the synchronous generator ABI without executing a read
