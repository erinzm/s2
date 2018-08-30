import psycopg2
from psycopg2.pool import ThreadedConnectionPool
from flask import _app_ctx_stack

class Postgres(object):
    def __init__(self, app=None, pool_size=10):
        self.app = app
        self.pool = None
        self.pool_size = pool_size

        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        self.pool = ThreadedConnectionPool(1, self.pool_size, app.config['POSTGRES_URL'])
        app.teardown_appcontext(self.teardown)
    
    def teardown(self, exception):
        ctx = _app_ctx_stack.top
        conn = getattr(ctx, 'postgres_conn', None)
        if conn is not None:
            self.pool.putconn(conn)
            del ctx.conn
    
    def _connect(self):
        return self.pool.getconn()
    
    @property
    def connection(self):
        ctx = _app_ctx_stack.top
        if ctx is not None:
            if not hasattr(ctx, 'postgres_conn'):
                ctx.postgres_conn = self._connect()
            return ctx.postgres_conn
    
    def cursor(self):
        return self.connection.cursor()

db = Postgres()
