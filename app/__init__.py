import click
from flask import Flask, current_app
from flask.cli import with_appcontext
from flask.helpers import get_debug_flag
from .config import DevConfig, ProdConfig

def make_app() -> Flask:
    app = Flask(__name__)

    config = DevConfig() if get_debug_flag() else ProdConfig()
    app.config.from_object(config)

    register_extensions(app)

    return app

def register_extensions(app: Flask):
    from .db import db
    db.init_app(app)
    from .extensions import toolbar
    toolbar.init_app(app)
            pass
        return '<body></body>'

    return app

def register_extensions(app: Flask):
    from .db import db
    db.init_app(app)
    from .extensions import toolbar
    toolbar.init_app(app)

@click.command('init-db')
@with_appcontext
def init_db():
    click.echo(click.style('[!] initializing database', fg='green'))
    from .db import db
    with db.connection as conn:
        with conn.cursor() as c:
            with current_app.open_resource('schema.sql', 'r') as f:
                c.execute(f.read())
