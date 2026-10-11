import json, os, runpy, sys, time
sys.path.insert(0, '/Users/erik/Projects/truss/scripts')
import native_fixture
original = native_fixture.get_server
events=[]
def measured(*args, **kwargs):
    start=time.perf_counter(); server=original(*args, **kwargs)
    events.append({'event':'fixture-ready' if os.environ.get('TRUSS_NATIVE_WORKER') else 'cluster-ready','seconds':time.perf_counter()-start})
    cleanup=server.cleanup
    def close(*a, **k):
        start=time.perf_counter()
        try: return cleanup(*a, **k)
        finally: events.append({'event':'fixture-cleanup' if os.environ.get('TRUSS_NATIVE_WORKER') else 'cluster-cleanup','seconds':time.perf_counter()-start})
    server.cleanup=close
    return server
native_fixture.get_server=measured
sys.argv=sys.argv[1:]
sys.path.insert(0, os.path.dirname(os.path.abspath(sys.argv[0])))
try: runpy.run_path(sys.argv[0],run_name='__main__')
finally:
    with open(os.environ['TRUSS_TIMING_FILE'],'w') as f: json.dump(events,f)
