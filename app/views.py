from flask import Blueprint, render_template, escape, request, abort, redirect, url_for
import logging
import numpy as np
from .master import S2, Master
from .db import db, uri_for_image, get_basis_uris, basis_weights_for_node
from PIL import Image
from .imgen import as_base64_png, load_image, perturb_image

logger = logging.getLogger(__name__)

views = Blueprint('views', __name__)

@views.route('/exp/<int:exp_id>/query')
def get_query(exp_id):
    with db.connection as conn:
        master = Master(conn, exp_id)

        def priority(job, user_id, state):
            return np.random.randn()
        user_id = 0
        job = master.get_job_for(conn, user_id, priority)

        x = load_image(uri_for_image(conn, exp_id, job['graph_id']))
        bases = [load_image(uri) for uri in get_basis_uris(conn, exp_id, job['graph_id'])]
        w = basis_weights_for_node(conn, exp_id, job['node_id'])
        x̂ = perturb_image(x, w, bases)
        img = Image.fromarray(x̂)

    return render_template('query.html',
        exp_id=exp_id,
        job=job,
        image=as_base64_png(img))

@views.route('/exp/<int:exp_id>/job/<int:job_id>', methods=['POST'])
def complete_job(exp_id, job_id):
    if 'label' not in request.form:
        abort(400, "label form parameter must be provided")
    label = int(request.form['label'])
    if label not in [-1, 1]:
        abort(422, "label must be ∈ {-1, 1}")
    
    with db.connection as conn:
        with conn.cursor() as c:
            # update this job to completed status and set the voted label
            c.execute("UPDATE jobs SET status = 'completed', vote_label = %s WHERE exp_id = %s AND id = %s", (label, exp_id, job_id))

            # find graph_id, node_id, ballot_id of job
            c.execute("SELECT graph_id, node_id, ballot_id FROM jobs WHERE exp_id = %s AND id = %s", (exp_id, job_id))
            graph_id, node_id, ballot_id = c.fetchone()
            logger.debug(f'exp: {exp_id}, job: {job_id}, graph: {graph_id}, node: {node_id}, label: {label}, ballot: {ballot_id}')

            # count uncompleted ballots
            c.execute("""
            SELECT count(*)
            FROM jobs
            WHERE exp_id = %s AND graph_id = %s AND node_id = %s
              AND status <> 'completed'
            """, (exp_id, graph_id, node_id))

            n_votes_remaining = c.fetchone()[0]
            logger.debug(f'there are {n_votes_remaining} votes for {graph_id}:{node_id} remaining')
            if n_votes_remaining == 0: # we're done with this node
                # tell the master
                master = Master(conn, exp_id)
                master.voting_done(conn, graph_id, node_id)

    return redirect(url_for(".get_query", exp_id=exp_id))


@views.route('/exp/<int:exp_id>/graph/<int:graph_id>')
def graph_info(exp_id, graph_id):
    with db.connection as conn:
        s2 = S2(conn, exp_id, graph_id)
        print('s2: ', s2)
    
    return escape(repr(s2))