from flask import Blueprint, render_template, escape, request, abort
import json
import numpy as np
from .master import S2, Master
from .db import db, uri_for_image, get_basis_uris, basis_weights_for_node
from PIL import Image
from .imgen import as_base64_png, load_image, perturb_image

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
        job=json.dumps(job),
        image=as_base64_png(img))

@views.route('/exp/<int:exp_id>/graph/<int:graph_id>/node/<int:node_id>/label', methods=['POST'])
def label_node(exp_id, graph_id, node_id):
    if 'label' not in request.form:
        abort(400, "label form parameter must be provided")
    label = int(request.form['label'])
    if label not in [-1, 1]:
        abort(422, "label must be ∈ {-1, 1}")
    
    return '', 200


@views.route('/exp/<int:exp_id>/graph/<int:graph_id>')
def graph_info(exp_id, graph_id):
    with db.connection as conn:
        s2 = S2(conn, exp_id, graph_id)
        print('s2: ', s2)
    
    return escape(repr(s2))