from typing import Callable
import operator
import logging
import psycopg2.extras
import numpy as np
from .db import required_votes

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

            # do we have both -1 and +1 labelled nodes?
            # note: this is faster than 'SELECT array_agg(label) @> '{-1,1}' FROM nodes WHERE exp_id = %s'
            c.execute('''
            SELECT
                EXISTS(SELECT 1 FROM nodes
                       WHERE exp_id = %s AND label=-1)
                AND
                EXISTS(SELECT 1 FROM nodes
                       WHERE exp_id = %s and label=1)
            ''', (exp_id, exp_id))
            have_pair = c.fetchone()[0]

        self.state = 'mssp' if have_pair else 'random_sampling'
        logger.debug(f'S2({exp_id}, {graph_id}) constructed with state={self.state}')

    def get_query(self, db) -> int:
        if self.state == 'random_sampling':
            with db.cursor() as c:
                # pick a random node we know nothing about
                # TODO: activity
                c.execute('''
                SELECT id FROM nodes
                    WHERE exp_id = %s
                      AND label IS NULL
                    OFFSET floor(random()*%s)
                    LIMIT 1
                ''', (self.exp_id, self.n_nodes))
                return c.fetchone()[0]
        elif self.state == 'mssp':
            # try to find obvious cuts and cut them
            self._perform_obvious_cuts(db)

        else:
            raise ValueError()
    
    def _perform_obvious_cuts(self, db):
        with db.cursor() as c:
            c.execute('''
            DELETE FROM edges edge USING nodes i, nodes j
                WHERE edge.exp_id = %(exp_id)s AND edge.graph_id = %(graph_id)s
                     AND i.exp_id = %(exp_id)s AND i.graph_id = %(graph_id)s
                     AND j.exp_id = %(exp_id)s AND j.graph_id = %(graph_id)s
                AND i.id = edge.i and j.id = edge.j
                AND i.label <> j.label
            ''', {'exp_id': self.exp_id, 'graph_id': self.graph_id})

    def __repr__(self) -> str:
        return f'<S² #v: {self.n_nodes}, #e: {self.n_edges}>'

class Master:
    def __init__(self, db, exp_id):
        self.exp_id = exp_id
    
    def get_job_for(self, db, user_id, priority: Callable[..., float]):
        logger.debug(f'getting job in experiment {self.exp_id} for user {user_id}')

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
        # find the majority
        with db.cursor() as c:
            c.execute("""
            SELECT sum(vote_label)
                FROM jobs
                WHERE exp_id = %s AND graph_id = %s AND node_id = %s
            """, (self.exp_id, graph_id, node_id))

            sum_labels = c.fetchone()[0]
            assert sum_labels is not None
        
        majority_label = np.sign(sum_labels)
        logger.debug(f'voting done for {graph_id}:{node_id}, majority label is {majority_label}')

        with db.cursor() as c:
            # set the node's label
            c.execute('UPDATE nodes SET label = %s WHERE exp_id = %s AND graph_id = %s AND id = %s', (int(majority_label), self.exp_id, graph_id, node_id))

        # run s2 again to get new jobs for this graph
        s2 = S2(db, self.exp_id, graph_id)
        new_node = s2.get_query(db)
        logger.debug(f'getting new node for {graph_id}: {new_node}')
        jobs = [
            (self.exp_id, graph_id, new_node, ballot_id, Status.UNASSIGNED)
            for ballot_id in range(required_votes(db, self.exp_id))
        ]

        with db.cursor() as c:
            psycopg2.extras.execute_values(c, 'INSERT INTO jobs (exp_id, graph_id, node_id, ballot_id, status) VALUES %s',
                jobs)