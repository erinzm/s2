from flask import Blueprint, render_template, escape
import json
import numpy as np
from .master import S2, Master
from .db import db, uri_for_image
from PIL import Image
from .imgen import as_base64_png

views = Blueprint('views', __name__)

@views.route('/exp/<int:exp_id>/query')
def get_query(exp_id):
    with db.connection as conn:
        master = Master(conn, exp_id)

        def priority(job, user_id, state):
            return np.random.randn()
        user_id = 0
        job = master.get_job_for(conn, user_id, priority)

        img = Image.open(uri_for_image(conn, exp_id, job['graph_id']))

    return render_template('query.html',
        job=json.dumps(job),
        image=as_base64_png(img))

@views.route('/exp/<int:exp_id>/graph/<int:graph_id>')
def graph_info(exp_id, graph_id):
    with db.connection as conn:
        s2 = S2(conn, exp_id, graph_id)
        print('s2: ', s2)
    
    return escape(repr(s2))