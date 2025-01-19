import os
from flask import Flask

def create_app():
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev', # used for signing the session cookie
        DATABASE=os.path.join(app.instance_path, "ruokareseptit.sqlite"),
    )
    app.config.from_object('ruokareseptit.default_settings')
    app.config.from_pyfile("config.py", silent=True)

    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    from . import db
    db.init_app(app)

    from . import home
    # import and register other features here
    app.register_blueprint(home.bp)

    return app
