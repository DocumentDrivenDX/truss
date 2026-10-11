SELECT pg_catalog.jsonb_build_object(
 'expressions',(SELECT COALESCE(pg_catalog.jsonb_agg(pg_catalog.jsonb_build_object(
   'table',c.relname,'column',a.attname,'generated',a.attgenerated,
   'definition',pg_catalog.pg_get_expr(d.adbin,d.adrelid,false))
   ORDER BY c.relname COLLATE pg_catalog."C",a.attnum),'[]'::pg_catalog.jsonb)
   FROM pg_catalog.pg_attrdef d JOIN pg_catalog.pg_class c ON c.oid=d.adrelid
   JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace
   JOIN pg_catalog.pg_attribute a ON a.attrelid=d.adrelid AND a.attnum=d.adnum
   WHERE n.nspname='truss'),
 'constraints',(SELECT COALESCE(pg_catalog.jsonb_agg(pg_catalog.jsonb_build_object(
   'table',r.relname,'name',c.conname,'kind',c.contype,
   'definition',pg_catalog.pg_get_constraintdef(c.oid,false),'validated',c.convalidated,
   'deferrable',c.condeferrable,'deferred',c.condeferred,'local',c.conislocal,
   'inheritedCount',c.coninhcount::pg_catalog.text,'noInherit',c.connoinherit,
   'parent',(SELECT pn.nspname||'.'||pr.relname||'.'||pc.conname FROM pg_catalog.pg_constraint pc JOIN pg_catalog.pg_class pr ON pr.oid=pc.conrelid JOIN pg_catalog.pg_namespace pn ON pn.oid=pr.relnamespace WHERE pc.oid=c.conparentid),
   'columns',(SELECT COALESCE(pg_catalog.jsonb_agg(a.attname ORDER BY k.ord),'[]'::pg_catalog.jsonb) FROM unnest(c.conkey) WITH ORDINALITY k(num,ord) JOIN pg_catalog.pg_attribute a ON a.attrelid=c.conrelid AND a.attnum=k.num),
   'target',(SELECT fn.nspname||'.'||f.relname FROM pg_catalog.pg_class f JOIN pg_catalog.pg_namespace fn ON fn.oid=f.relnamespace WHERE f.oid=c.confrelid),
   'targetColumns',(SELECT COALESCE(pg_catalog.jsonb_agg(a.attname ORDER BY k.ord),'[]'::pg_catalog.jsonb) FROM unnest(c.confkey) WITH ORDINALITY k(num,ord) JOIN pg_catalog.pg_attribute a ON a.attrelid=c.confrelid AND a.attnum=k.num),
   'backingIndex',(SELECT xn.nspname||'.'||x.relname FROM pg_catalog.pg_class x JOIN pg_catalog.pg_namespace xn ON xn.oid=x.relnamespace WHERE x.oid=c.conindid),
   'updateAction',c.confupdtype,'deleteAction',c.confdeltype,'match',c.confmatchtype)
   ORDER BY r.relname COLLATE pg_catalog."C",c.conname COLLATE pg_catalog."C"),'[]'::pg_catalog.jsonb)
   FROM pg_catalog.pg_constraint c JOIN pg_catalog.pg_class r ON r.oid=c.conrelid
   JOIN pg_catalog.pg_namespace n ON n.oid=c.connamespace WHERE n.nspname='truss'),
 'indexes',(SELECT COALESCE(pg_catalog.jsonb_agg(pg_catalog.jsonb_build_object(
   'table',r.relname,'name',c.relname,'kind',c.relkind,
   'definition',pg_catalog.pg_get_indexdef(i.indexrelid,0,false),
   'valid',i.indisvalid,'ready',i.indisready,'live',i.indislive,
   'unique',i.indisunique,'primary',i.indisprimary,'exclusion',i.indisexclusion,
   'immediate',i.indimmediate,'nullsNotDistinct',i.indnullsnotdistinct,
   'clustered',i.indisclustered,'replicaIdentity',i.indisreplident,
   'options',c.reloptions,'accessMethod',am.amname,
   'keyCount',i.indnkeyatts::pg_catalog.text,'attributeCount',i.indnatts::pg_catalog.text,
   'keys',(SELECT COALESCE(pg_catalog.jsonb_agg(pg_catalog.pg_get_indexdef(i.indexrelid,k.ord::integer,false) ORDER BY k.ord),'[]'::pg_catalog.jsonb) FROM unnest(i.indkey::smallint[]) WITH ORDINALITY k(num,ord)),
   'opclasses',(SELECT COALESCE(pg_catalog.jsonb_agg(onsp.nspname||'.'||op.opcname ORDER BY k.ord),'[]'::pg_catalog.jsonb) FROM unnest(i.indclass::oid[]) WITH ORDINALITY k(id,ord) JOIN pg_catalog.pg_opclass op ON op.oid=k.id JOIN pg_catalog.pg_namespace onsp ON onsp.oid=op.opcnamespace),
   'collations',(SELECT COALESCE(pg_catalog.jsonb_agg(cn.nspname||'.'||co.collname ORDER BY k.ord),'[]'::pg_catalog.jsonb) FROM unnest(i.indcollation::oid[]) WITH ORDINALITY k(id,ord) LEFT JOIN pg_catalog.pg_collation co ON co.oid=k.id LEFT JOIN pg_catalog.pg_namespace cn ON cn.oid=co.collnamespace),
   'keyOptions',i.indoption::pg_catalog.text,
   'parents',(SELECT COALESCE(pg_catalog.jsonb_agg(pn.nspname||'.'||p.relname ORDER BY inh.inhseqno),'[]'::pg_catalog.jsonb) FROM pg_catalog.pg_inherits inh JOIN pg_catalog.pg_class p ON p.oid=inh.inhparent JOIN pg_catalog.pg_namespace pn ON pn.oid=p.relnamespace WHERE inh.inhrelid=c.oid))
   ORDER BY r.relname COLLATE pg_catalog."C",c.relname COLLATE pg_catalog."C"),'[]'::pg_catalog.jsonb)
   FROM pg_catalog.pg_index i JOIN pg_catalog.pg_class c ON c.oid=i.indexrelid
   JOIN pg_catalog.pg_class r ON r.oid=i.indrelid
   JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace
   JOIN pg_catalog.pg_am am ON am.oid=c.relam WHERE n.nspname='truss'))::pg_catalog.text
