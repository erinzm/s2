from typing import List
from collections import defaultdict
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

def graphs_percent_done(db, exp_id: int) -> defaultdict:
    with db.cursor() as c:
        c.execute('''
        WITH
            exp_nodes AS (
                SELECT id, graph_id, label FROM nodes
                WHERE exp_id = %(exp_id)s
            ),
            labeled AS (
                SELECT graph_id, COUNT(*) FROM exp_nodes WHERE label IS NOT NULL GROUP BY graph_id
            ),
            total AS (
                SELECT graph_id, COUNT(*) FROM exp_nodes GROUP BY graph_id
            )
        SELECT labeled.graph_id, (labeled.count::float / total.count::float) AS percent_done FROM labeled, total WHERE labeled.graph_id = total.graph_id
        ''', {'exp_id': exp_id})
    
        d = defaultdict(int)
        for row in c:
            d[row[0]] = row[1]
    
    return d

def graphs_touched_by(db, exp_id: int, user_id: int):
    with db.cursor() as c:
        c.execute('''
        SELECT graph_id
        FROM jobs
        WHERE
            completing_user = %(user_id)s AND
            exp_id = %(exp_id)s
        ''', {'exp_id': exp_id, 'user_id': user_id})

        return set([r[0] for r in c.fetchall()])
