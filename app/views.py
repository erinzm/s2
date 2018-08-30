from flask import Blueprint, render_template

views = Blueprint('views', __name__)

@views.route('/exp/<int:exp_id>/query')
def get_query(exp_id):
    return render_template('query.html')