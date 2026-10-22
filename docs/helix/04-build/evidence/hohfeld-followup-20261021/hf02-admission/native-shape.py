import json,tempfile,pathlib,psycopg
from truss import LocalPostgres
root=pathlib.Path(tempfile.mkdtemp(prefix='truss-hf02-acl-'))
results=[]
with LocalPostgres(root/'data') as local:
 with psycopg.connect(local.info.connection_uri,autocommit=True) as admin:
  admin.execute('CREATE ROLE probe_actor LOGIN')
  admin.execute("CREATE FUNCTION public.private_effect() RETURNS text LANGUAGE plpgsql VOLATILE AS $$ BEGIN RETURN 'effect'; END $$")
  admin.execute('REVOKE ALL ON FUNCTION public.private_effect() FROM PUBLIC')
  admin.execute("CREATE FUNCTION public.admitted() RETURNS bool LANGUAGE plpgsql VOLATILE AS $$ BEGIN RETURN false; END $$")
  p=psycopg.conninfo.conninfo_to_dict(local.info.connection_uri);p['user']='probe_actor'
  with psycopg.connect(**p,autocommit=True) as caller:
   for sql in ("SELECT CASE WHEN public.admitted() THEN public.private_effect() ELSE 'denied' END", "WITH a AS MATERIALIZED(SELECT public.admitted() AS ok) SELECT effect.* FROM a LEFT JOIN LATERAL (SELECT public.private_effect() WHERE a.ok) effect ON true"):
    try:actual={'rows':caller.execute(sql).fetchall()}
    except psycopg.Error as e:actual={'sqlstate':e.sqlstate}
    results.append({'sql':sql,'actual':actual})
print(json.dumps({'postgres':'18.6','scope':'Native ACL evaluation only; no Truss runtime claim','results':results},indent=2))
