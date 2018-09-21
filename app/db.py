from typing import List
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
            del ctx.postgres_conn
    
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

def uri_for_image(db, exp_id: int, img_id: int) -> str:
    with db.cursor() as c:
        c.execute('SELECT uri FROM images WHERE exp_id = %s AND id = %s', (exp_id, img_id,))
        return c.fetchone()[0]

def get_basis_uris(db, exp_id: int, img_id: int) -> List[str]:
    with db.cursor() as c:
        c.execute('SELECT uri FROM bases WHERE exp_id = %s AND image_id = %s ORDER BY id ASC', (exp_id, img_id))
        return [x[0] for x in c]

def basis_weights_for_node(db, exp_id: int, node_id: int) -> List[float]:
    with db.cursor() as c:
        c.execute('SELECT basis_weights FROM nodes WHERE exp_id = %s AND id = %s', (exp_id, node_id))
        return c.fetchone()[0]

def required_votes(db, exp_id: int) -> int:
    with db.cursor() as c:
        c.execute('SELECT required_votes_per_node FROM experiments WHERE id = %s', (exp_id,))
        return c.fetchone()[0]

def naive_proportion_labeled(db, exp_id: int, graph_id: int) -> int:
    with db.cursor() as c:
        c.execute('''
        WITH
            graph_nodes AS (
                SELECT id, label FROM nodes
                WHERE exp_id = %(exp_id)s
                AND graph_id = %(graph_id)s),
            labeled_nodes AS (
                SELECT id FROM graph_nodes
                WHERE label IS NOT NULL)
        SELECT (
            (SELECT COUNT(*) FROM labeled_nodes)::float
            /
            (SELECT COUNT(*) FROM graph_nodes)::float)
        ''', {'exp_id': exp_id, 'graph_id': graph_id})
        
        return c.fetchone()[0]