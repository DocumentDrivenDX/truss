# SPDX-License-Identifier: MIT OR Apache-2.0
"""Restart-durable local implementation of CONTRACT-007 HostRecoveryRegistry.

The embedding host owns this file and its access. Original obligations and
observations are immutable; this registry neither executes nor retries work.
"""
import json
from contextlib import contextmanager
import sqlite3
from pathlib import Path
from uuid import uuid4
from hashlib import sha256
from .contracts import ProfilePin


class HostRecoveryRegistry:
    retention='restart_durable'
    profile=ProfilePin(identity='truss-host-recovery-registry',version='0.1.0',
        sha256=sha256(b'CONTRACT-007 synchronous SQLite host registry: immutable obligation, context-authorized inspect, compare-and-append observation, restart-durable').hexdigest())

    def __init__(self,path):
        self.path=Path(path)
        # Exclusive creation avoids opening a newly created journal with broad permissions.
        if not self.path.exists():
            with self.path.open('xb') as file:self.path.chmod(0o600)
        with self._connect() as db:
            db.execute('CREATE TABLE IF NOT EXISTS obligation(reference TEXT PRIMARY KEY, id TEXT UNIQUE NOT NULL, original TEXT NOT NULL)')
            db.execute('CREATE TABLE IF NOT EXISTS observation(reference TEXT NOT NULL, ordinal INTEGER NOT NULL, original TEXT NOT NULL, PRIMARY KEY(reference,ordinal), FOREIGN KEY(reference) REFERENCES obligation(reference))')

    @contextmanager
    def _connect(self):
        db=sqlite3.connect(self.path,timeout=1)
        try:
            db.execute('PRAGMA synchronous=FULL');db.execute('PRAGMA foreign_keys=ON')
            with db:yield db
        finally:db.close()

    @staticmethod
    def _text(value):return json.dumps(value,sort_keys=True,separators=(',',':'))

    def register(self,obligation):
        original=self._text(obligation)
        with self._connect() as db:
            db.execute('BEGIN IMMEDIATE')
            row=db.execute('SELECT reference,original FROM obligation WHERE id=?',(obligation['obligationId'],)).fetchone()
            if row:
                if row[1]!=original:raise ValueError('Recovery obligation conflict')
                return row[0]
            reference=str(uuid4())
            db.execute('INSERT INTO obligation VALUES(?,?,?)',(reference,obligation['obligationId'],original))
            return reference

    def inspect(self,reference,context):
        with self._connect() as db:
            row=db.execute('SELECT original FROM obligation WHERE reference=?',(reference,)).fetchone()
            if not row:raise ValueError('Original recovery obligation missing')
            obligation=json.loads(row[0])
            if obligation['target']!=context:raise ValueError('Original installed recovery context required')
            observations=[json.loads(r[0]) for r in db.execute('SELECT original FROM observation WHERE reference=? ORDER BY ordinal',(reference,))]
            return {'obligation':obligation,'observations':observations}

    def append(self,reference,observation):
        with self._connect() as db:
            db.execute('BEGIN IMMEDIATE')
            previous=db.execute('SELECT ordinal,original FROM observation WHERE reference=? ORDER BY ordinal DESC LIMIT 1',(reference,)).fetchone()
            expected=json.loads(previous[1])['observationId'] if previous else None
            if observation['expectedPreviousObservationId']!=expected:raise ValueError('Recovery observation conflict')
            db.execute('INSERT INTO observation VALUES(?,?,?)',(reference,previous[0]+1 if previous else 1,self._text(observation)))
