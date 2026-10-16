"""Private Unix-socket SCRAM login adapter, not human/permit admission.

The trusted host supplies the original server socket/database and credentials.
Human/service enrollment and original engine connection custody remain separate.
Never serialize credentials or expose driver errors through this boundary.
"""
from dataclasses import dataclass, field
import psycopg


@dataclass(frozen=True, slots=True)
class ScramPreparationLogin:
    socket_directory: str
    port: int
    database: str
    native_login: str
    password: str = field(repr=False, compare=False)

    def open_connection(self):
        """Engine connection factory; no adopted socket or trust fallback."""
        if (type(self.socket_directory) is not str or not self.socket_directory.startswith('/')
                or '\0' in self.socket_directory or len(self.socket_directory.encode()) > 4096
                or type(self.port) is not int or not 1 <= self.port <= 65535
                or any(type(v) is not str or not v or '\0' in v or len(v.encode()) > 63
                       for v in (self.database, self.native_login))
                or type(self.password) is not str or not self.password or '\0' in self.password
                or len(self.password.encode()) > 4096):
            raise ValueError('Original bounded SCRAM login configuration required')
        connection = None
        try:
            connection = psycopg.connect(host=self.socket_directory, port=self.port,
                dbname=self.database, user=self.native_login, password=self.password,
                require_auth='scram-sha-256', connect_timeout=5, autocommit=True,
                options='-c search_path=pg_catalog,pg_temp -c statement_timeout=10000')
            if not connection.pgconn.used_password:
                raise ValueError('Original SCRAM password exchange required')
            with connection.cursor() as cursor:
                cursor.execute("""SELECT pg_catalog.current_setting('server_version_num'),
                    current_user::text,session_user::text,pg_catalog.current_database()::text,
                    r.rolcanlogin,r.rolsuper,r.rolcreaterole,r.rolcreatedb,r.rolreplication,r.rolbypassrls
                    FROM pg_catalog.pg_roles r WHERE r.rolname=session_user""", prepare=False)
                if cursor.fetchmany(2) != [('180006', self.native_login, self.native_login,
                        self.database, True, False, False, False, False, False)]:
                    raise ValueError('Original ordinary SCRAM login context required')
            return connection
        except BaseException as error:
            cleanup_failed = False
            if connection is not None:
                try:
                    connection.close()
                except BaseException:
                    cleanup_failed = True
            if isinstance(error, Exception):
                message = 'Original SCRAM login refused'
                if cleanup_failed:
                    message += '; connection cleanup unconfirmed'
                raise ValueError(message) from None
            if cleanup_failed:
                error.add_note('SCRAM connection cleanup unconfirmed')
            raise
