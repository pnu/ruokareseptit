""" Applications views
"""

from . import home, recipes, auth, my

def register_blueprints(app):
    """ Register views
    """
    app.register_blueprint(home.bp)
    app.register_blueprint(recipes.bp)
    app.register_blueprint(auth.bp)
    app.register_blueprint(my.bp)
