"""Ruokareseptit application module
"""

import os
from flask import Flask


def create_app():
    """Flask application factory.
    """
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',  # used for signing the session cookie
        DATABASE=os.path.join(app.instance_path, "ruokareseptit.sqlite"),
    )
    app.config.from_object('ruokareseptit.default_settings')
    app.config.from_pyfile("config.py", silent=True)

    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # pylint: disable=import-outside-toplevel

    from . import db
    db.init_app(app)

    from . import navigation
    from . import home
    from . import recipes
    from . import edit
    from . import auth
    app.context_processor(navigation.navigation_context)
    app.register_blueprint(home.bp)
    app.register_blueprint(recipes.bp)
    app.register_blueprint(edit.bp)
    app.register_blueprint(auth.bp)

    return app
