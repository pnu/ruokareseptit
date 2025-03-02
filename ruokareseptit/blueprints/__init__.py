""" Applications views
"""

from . import home
from . import recipes
from . import auth
from . import my


def register_app_blueprints(app):
    """ Register views
    """
    app.register_blueprint(home.bp)
    app.register_blueprint(recipes.bp)
    app.register_blueprint(auth.bp)
    app.register_blueprint(my.bp)
