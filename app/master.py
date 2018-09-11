from typing import Callable
import operator
import logging

logger = logging.getLogger(__name__)

class Status:
    UNASSIGNED = 'unassigned'
    WAITING    = 'waiting'
    COMPLETED  = 'completed'

class S2:
    def __init__(self, db, exp_id, graph_id):
        self.exp_id = exp_id
        self.graph_id = graph_id

        with db.cursor() as c:
            c.execute('''
            SELECT
                (SELECT COUNT(*) FROM nodes WHERE exp_id = %s AND graph_id = %s),
                (SELECT COUNT(*) FROM edges WHERE exp_id = %s AND graph_id = %s)
            ''', (exp_id, graph_id, exp_id, graph_id))
            self.n_nodes, self.n_edges = c.fetchone()

            assert self.n_nodes != 0
            assert self.n_edges != 0

    def get_query(self, db) -> int:
        with db.cursor() as c:
            # random sampling
            # TODO: activity
            c.execute('''
            SELECT id FROM nodes
            WHERE exp_id = %s
              AND label IS NULL
            OFFSET floor(random()*%s)
            LIMIT 1
            ''', (self.exp_id, self.n_nodes))
            return c.fetchone()[0]
    
    def __repr__(self) -> str:
        return f'<S² #v: {self.n_nodes}, #e: {self.n_edges}>'

class Master:
    def __init__(self, db, exp_id):
        self.exp_id = exp_id
    
    def get_job_for(self, db, user_id, priority: Callable[..., float]):
        logger.debug(f'getting job in experiment {self.exp_id} for {user_id}')

        with db.cursor() as c:
            c.execute("SELECT COUNT(*) FROM jobs WHERE exp_id = %s AND status = 'unassigned'", (self.exp_id,))
            n_jobs = c.fetchone()[0]
            logger.debug(f'{n_jobs} unassigned jobs available')

            # TODO: handle empty job list
            if n_jobs == 0:
                return None

            c.execute('''
            SELECT
                id, graph_id, node_id, ballot_id
            FROM jobs
            WHERE exp_id = %s
              AND status = 'unassigned'
            ''', (self.exp_id,))

            jobs = [
                {
                    'job_id': job_id,
                    'graph_id': graph_id,
                    'node_id': node_id,
                    'ballot_id': ballot_id,
                }
                for job_id, graph_id, node_id, ballot_id in c
            ]

            state = None # TODO: uggghhh
            jobs = [{'job': job, 'priority': priority(job, user_id, state)}
                        for job in jobs]

            opt_job = max(jobs, key=operator.itemgetter('priority'))

            logger.debug(f'found optimal job: {opt_job}')

            # switch this job to WAITING
            c.execute("UPDATE jobs SET status = 'waiting' WHERE id = %s",
                      (opt_job['job']['job_id'],))
            
            return opt_job['job']

    def voting_done(self, db, graph_id, node_id):
        pass