"""Ruokareseptit application factory"""

import os
from flask import Flask

from .model import auth, db, navigation


def create_app():
    """Create app, register handlers and blueprints"""
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY="dev",  # used for signing the session cookie
        DATABASE=os.path.join(app.instance_path, "ruokareseptit.sqlite"),
    )
    app.config.from_object("ruokareseptit.default_settings")
    app.config.from_pyfile("config.py", silent=True)

    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    db.init_app(app)
    auth.register_before_request(app)
    navigation.register_context_processor(app)

    # pylint: disable=import-outside-toplevel
    from .blueprints import register_app_blueprints

    register_app_blueprints(app)

    return app
