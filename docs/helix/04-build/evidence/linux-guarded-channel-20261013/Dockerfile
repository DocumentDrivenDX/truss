FROM oven/bun:1.4.2 AS bun
FROM python:3.11-slim
COPY --from=bun /usr/local/bin/bun /opt/homebrew/bin/bun
COPY wheels/ /wheels/
RUN pip install --no-cache-dir 'psycopg[binary]==3.3.6' 'jsonschema==4.26.0' 'referencing==0.37.0' 'fasteners==0.20' 'platformdirs==4.12.4' 'psutil==7.2.2' /wheels/*.whl
RUN python -c "import psycopg,weft,pgserver; from psycopg import pq; print(psycopg.__version__,pq.version()); assert callable(weft.prepare_security_mapping_json); assert callable(weft.inspect_security_mapping_subject_key_json)"
