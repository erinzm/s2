from flask import Flask
from flask.helpers import get_debug_flag
from .config import DevConfig, ProdConfig

def make_app() -> Flask:
    app = Flask(__name__)

    config = DevConfig() if get_debug_flag() else ProdConfig()
    app.config.from_object(config)

    register_extensions(app)
    from .cli import register_cli
    register_cli(app)
    
    from .views import views
    app.register_blueprint(views)

    return app

def register_extensions(app: Flask):
    from .db import db
    db.init_app(app)
    from .extensions import toolbar
    toolbar.init_app(app)
