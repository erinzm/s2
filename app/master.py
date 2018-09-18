from typing import Callable
import operator
import logging
from datetime import datetime, timedelta
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

        with db.cursor() as c:
            # do we have both -1 and +1 labelled nodes?
            # note: this is faster than 'SELECT array_agg(label) @> '{-1,1}' FROM nodes WHERE exp_id = %s'
            c.execute('''
            SELECT
                (EXISTS(SELECT 1 FROM nodes
                       WHERE exp_id = %(exp_id)s
                       AND graph_id = %(graph_id)s
                       AND label=-1)
                AND
                EXISTS(SELECT 1 FROM nodes
                       WHERE exp_id = %(exp_id)s
                       AND graph_id = %(graph_id)s
                       AND label=1))
            ''', {'exp_id': exp_id, 'graph_id': graph_id})
            have_pair = c.fetchone()[0]

        self.state = 'mssp' if have_pair else 'random_sampling'
        logger.debug(f'S2({exp_id}, {graph_id}) constructed with state={self.state}')

    def get_query(self, db) -> int:
        if self.state == 'random_sampling':
            with db.cursor() as c:
                # pick a random node we know nothing about
                # TODO: activity
                c.execute('''
                WITH nodes_of_interest AS (
                    SELECT id FROM nodes
                        WHERE exp_id = %s
                        AND graph_id = %s
                        AND label IS NULL
                )
                SELECT id FROM nodes_of_interest
                    OFFSET (SELECT floor(random()*count(*)) FROM nodes_of_interest)
                    LIMIT 1
                ''', (self.exp_id, self.graph_id))

                node_id = c.fetchone()[0]
                logger.debug(f'got random node {node_id}')

                return node_id

        elif self.state == 'mssp':
            # try to find obvious cuts and cut them
            logger.debug('performing obvious cuts')
            self._perform_obvious_cuts(db)

            # try to pick a MSSP midpoint
            logger.debug('picking an MSSP vertex')
            vert = self._mssp(db)

            # if we can't find one, we assume that we're done (two-separable-components assumption).
            if vert is None:
                pass

            return vert

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
    
    def _mssp(self, db):
        with db.cursor() as c:
            c.execute('''
            WITH routes AS
                ( SELECT *
                    FROM pgr_dijkstra( 'SELECT id, i source, j target, 1 "cost", 1 "reverse_cost" FROM edges WHERE exp_id = %(exp_id)s AND graph_id = %(graph_id)s',
                                    (SELECT array_agg(id)
                                    FROM nodes
                                    WHERE exp_id = %(exp_id)s
                                        AND graph_id = %(graph_id)s
                                        AND label = 1),
                                    (SELECT array_agg(id)
                                    FROM nodes
                                    WHERE exp_id = %(exp_id)s
                                        AND graph_id = %(graph_id)s
                                        AND label = -1)) ),
                routeCosts as (
                    SELECT start_vid, end_vid, agg_cost
                    FROM routes
                    WHERE edge = -1
                ),
                shortestShortestPath AS (
                    SELECT *
                    FROM routes
                    WHERE (start_vid, end_vid) = (SELECT start_vid, end_vid FROM routeCosts ORDER BY agg_cost ASC LIMIT 1)
                )
            SELECT node
            FROM shortestShortestPath
            WHERE path_seq = (select count(*)/2 + 1 from shortestShortestPath)
            ''', {'exp_id': self.exp_id, 'graph_id': self.graph_id})
            row = c.fetchone()
            mssp = None if row is None else row[0]
            logger.debug(f"[exp:{self.exp_id}] found MSSP! for {self.graph_id}: {mssp}")

            return mssp

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

            # Scan the job table for expired jobs and reinstate them
            c.execute('''
            UPDATE jobs
            SET
                status = 'unassigned',
                checked_out_at = NULL
            WHERE
                checked_out_at + %(timeout)s < now()
                AND exp_id = %(exp_id)s
                AND status = 'waiting'
            ''', {'timeout': timedelta(seconds=30), 'exp_id': self.exp_id})
            logger.debug(f'[{self.exp_id}]: reset {c.rowcount} expired jobs to UNASSIGNED status')

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

            # switch this job to WAITING and set the time we checked it out
            c.execute("UPDATE jobs SET status = 'waiting', checked_out_at = %s WHERE id = %s",
                      (datetime.now(), opt_job['job']['job_id'],))
            
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

        db.commit()

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
        