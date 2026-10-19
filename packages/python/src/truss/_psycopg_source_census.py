# SPDX-License-Identifier: MIT OR Apache-2.0
"""Private supported-API source response observation, not authority admission.

One statement observes selected whole-database catalogs. Native scan/heap work,
source writers, external executables and a held coherent authority/data cut are
not qualified here. The host owns transaction settlement and containment.
"""
from dataclasses import dataclass
from hashlib import sha256
from importlib.resources import files
import re
from .execution import Error, ExecutionFailure
from .psycopg_host import PsycopgHost
from .catalog_runtime import _pin_cursor

_SOURCE_SHA256 = '494a647e449032e21ebc5e2eb9903619b9385bf99cbde72c63923da44ee23465'
_MAX_IMAGE = 16777216
_CHUNK = 4096

@dataclass(frozen=True, slots=True)
class SourceCensusObservation:
    original_image: bytes
    source_sha256: str
    scope: str = 'native_response_only'
    admitted: bool = False


def observe_source_census_in_transaction(host, transaction):
    if type(host) is not PsycopgHost:
        return Error(ExecutionFailure('execution_obligation','Original supported host required'))
    def capture(cursor, observed):
        return _capture_census(cursor)
    return host._run_operation(transaction,capture)


def _decode_census(cursor):
    if (cursor.description is None or tuple(c.name for c in cursor.description)!=('ordinal','total_bytes','chunk_hex')
            or any(c.type_code!=25 for c in cursor.description)):
        raise ValueError('Exact original census descriptors required')
    image=bytearray();total=None;ordinal=0
    while True:
        rows=cursor.fetchmany(64)
        if not rows:break
        for row in rows:
            if (len(row)!=3 or any(type(cell) is not str for cell in row)
                    or row[0]!=str(ordinal) or ordinal>=4096
                    or re.fullmatch('[1-9][0-9]{0,7}',row[1]) is None):
                raise ValueError('Complete ordered census chunks required')
            size=int(row[1])
            if not 1<=size<=_MAX_IMAGE or (total is not None and size!=total):
                raise ValueError('Exact bounded original census length required')
            total=size;expected=min(_CHUNK,total-len(image))
            if expected<=0 or len(row[2])!=2*expected or re.fullmatch('[0-9a-f]+',row[2]) is None:
                raise ValueError('Exact bounded original census chunk required')
            image.extend(bytes.fromhex(row[2]));ordinal+=1
    if total is None or len(image)!=total:
        raise ValueError('Complete original source image unavailable')
    result=bytes(image);result.decode('utf8',errors='strict')
    return result


def _capture_census(cursor):
    _pin_cursor(cursor)
    cursor.execute("SELECT pg_catalog.current_setting('search_path')",prepare=False)
    original_path=cursor.fetchone()[0]
    cursor.execute("SELECT pg_catalog.set_config('search_path','pg_catalog, pg_temp',true)",prepare=False)
    raw=files('truss').joinpath('_source_census','pg18.sql').read_bytes()
    if sha256(raw).hexdigest()!=_SOURCE_SHA256:
        raise ValueError('Original source-census SQL required')
    source=raw.decode('utf8').strip().removesuffix(';')
    query=("WITH image AS MATERIALIZED (SELECT pg_catalog.convert_to(census,'UTF8') AS body FROM ("+source+") AS original_census) "
        "SELECT part::pg_catalog.text AS ordinal,pg_catalog.octet_length(body)::pg_catalog.text AS total_bytes,"
        "pg_catalog.encode(pg_catalog.substring(body,part*4096+1,4096),'hex') AS chunk_hex "
        "FROM image LEFT JOIN LATERAL pg_catalog.generate_series(0,(pg_catalog.octet_length(body)-1)/4096) AS part ON true ORDER BY part")
    cursor.execute(query,prepare=False,binary=False)
    image=_decode_census(cursor)
    cursor.execute("SELECT pg_catalog.set_config('search_path',%s,true)",(original_path,),prepare=False)
    if cursor.fetchone()!=(original_path,):raise ValueError('Original census caller search path restoration required')
    return SourceCensusObservation(image,_SOURCE_SHA256)
