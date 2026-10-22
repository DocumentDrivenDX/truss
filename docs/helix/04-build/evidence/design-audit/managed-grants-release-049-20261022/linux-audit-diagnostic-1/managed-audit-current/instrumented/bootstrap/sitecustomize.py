import hashlib,json,os,re,threading,time,unittest
from pathlib import Path
import psycopg

TRACE=Path(os.environ["TRUSS_DIAGNOSTIC_TRACE"])
Path(os.environ["TRUSS_DIAGNOSTIC_BOOTSTRAP_MARKER"]).write_text("loaded\n",encoding="utf-8")
LOCK=threading.Lock()
QUERIES=[]
CANDIDATES=[]
TARGET_ACTIVE=False
TARGET="test_audit_disclosure_native.AuditDisclosureNativeTests.test_whole_group_more_than_1024_events_uses_separate_event_budget"

def _raw(query, connection=None):
    try:
        return query if isinstance(query,str) else query.as_string(connection) if hasattr(query,"as_string") else repr(query)
    except Exception:
        return repr(query)

def _safe(query,connection=None):
    text=_raw(query,connection)
    text=re.sub(r"'(?:''|[^'])*'", "'<literal>'", text)
    text=re.sub(r'\b[0-9]+(?:\.[0-9]+)?\b', '<number>', text)
    return text[:12000]

def _diag(error):
    d=getattr(error,"diag",None)
    names=("severity","sqlstate","message_primary","message_detail","message_hint","context","schema_name","table_name","column_name","constraint_name","statement_position","internal_position","internal_query")
    values={}
    if d is not None:
        for name in names:
            value=getattr(d,name,None)
            values[name]=(_safe(str(value)) if name in ("context","internal_query")
                          else str(value)[:4000]) if value is not None else None
    return {"type":type(error).__name__,"text":str(error)[:4000],"sqlstate":getattr(error,"sqlstate",None),"diag":values}

def _record(query, elapsed, error=None, kind="execute", connection=None):
    raw=_raw(query,connection)
    safe_sql=_safe(query,connection)
    match=re.match(r"\s*([A-Za-z]+)",safe_sql)
    row={"kind":kind,"statementClass":match.group(1).upper() if match else "OTHER","durationSeconds":elapsed,"statementSha256":hashlib.sha256(raw.encode("utf-8","replace")).hexdigest(),"safeSql":safe_sql,"error":_diag(error) if error else None}
    with LOCK:
        QUERIES.append(row)
        if len(QUERIES)>20000: QUERIES.pop(0)
    return row

def _candidate(row,query,args,kwargs):
    if TARGET_ACTIVE and row.get("safeSql","").lstrip().upper().startswith("SELECT"):
        params=args[0] if args else kwargs.get("params")
        CANDIDATES.append((row,query,params))

_execute=psycopg.Cursor.execute
def _timed_execute(self,query,*args,**kwargs):
    started=time.monotonic()
    try:
        result=_execute(self,query,*args,**kwargs)
        row=_record(query,time.monotonic()-started,connection=self.connection)
        _candidate(row,query,args,kwargs)
        return result
    except BaseException as error:
        row=_record(query,time.monotonic()-started,error,connection=self.connection)
        _candidate(row,query,args,kwargs)
        raise
psycopg.Cursor.execute=_timed_execute

_executemany=psycopg.Cursor.executemany
def _timed_executemany(self,query,*args,**kwargs):
    started=time.monotonic()
    try:
        result=_executemany(self,query,*args,**kwargs)
        _record(query,time.monotonic()-started,kind="executemany",connection=self.connection)
        return result
    except BaseException as error:
        _record(query,time.monotonic()-started,error,kind="executemany",connection=self.connection)
        raise

psycopg.Cursor.executemany=_timed_executemany

def _maybe_explain(test):
    failures=[]
    hosts=[]
    for connection,host in getattr(test,"consumer_connections",[]):
        attempt=getattr(getattr(host,"_custody",None),"last_attempt",None)
        error=getattr(attempt,"error",None)
        if error is not None: hosts.append(_diag(error))
    failures.append({"consumerHostAttempts":hosts})
    if CANDIDATES:
        failing=[item for item in CANDIDATES if item[0].get("error")]
        row,query,params=max(failing or CANDIDATES,key=lambda item:item[0]["durationSeconds"])
        result={"statementSha256":row["statementSha256"],"explain":"not attempted","plan":None}
        try:
            connections=getattr(test,"consumer_connections",[])
            if not connections: raise RuntimeError("Original consumer connection is unavailable")
            original_connection=connections[-1][0]
            with psycopg.connect(original_connection.info.dsn,options="-c statement_timeout=10000 -c default_transaction_read_only=on",autocommit=True) as observer:
                with observer.cursor() as cursor:
                    rendered=query if isinstance(query,str) else query.as_string(observer)
                    cursor.execute("EXPLAIN (FORMAT JSON, VERBOSE, COSTS TRUE) "+rendered,params)
                    plan=cursor.fetchone()[0]
                    encoded=json.dumps(plan,sort_keys=True,default=str)
                    if len(encoded.encode("utf-8"))<=2*1024*1024:
                        result["plan"]=plan
                    else:
                        result["plan"]={"truncated":True,"bytes":len(encoded.encode("utf-8")),"sha256":hashlib.sha256(encoded.encode("utf-8")).hexdigest(),"prefix":encoded[:4096]}
            result["explain"]="estimated plan only; ANALYZE was not requested"
        except BaseException as error:
            result["explainError"]=_diag(error)
        failures.append(result)
    with Path(os.environ["TRUSS_DIAGNOSTIC_FAILURES"]).open("w",encoding="utf-8") as out:
        json.dump(failures,out,indent=2,default=str)

def _flush():
    with TRACE.open("w",encoding="utf-8") as out:
        for row in QUERIES: out.write(json.dumps(row,sort_keys=True)+"\n")

import test_audit_disclosure_native as _audit
_target=getattr(_audit.AuditDisclosureNativeTests,"test_whole_group_more_than_1024_events_uses_separate_event_budget")
def _diagnose_target(self,*args,**kwargs):
    global TARGET_ACTIVE
    TARGET_ACTIVE=True
    try: return _target(self,*args,**kwargs)
    except BaseException:
        _maybe_explain(self)
        raise
    finally:
        TARGET_ACTIVE=False
        _flush()
_diagnose_target.__name__=_target.__name__
_diagnose_target.__doc__=_target.__doc__
_diagnose_target.__qualname__=_target.__qualname__
_audit.AuditDisclosureNativeTests.test_whole_group_more_than_1024_events_uses_separate_event_budget=_diagnose_target
