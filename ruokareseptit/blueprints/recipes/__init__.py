"""Public recipes listings and search"""

from flask import Blueprint

from . import browse
from . import categories
from . import search

bp = Blueprint("recipes", __name__, url_prefix="/recipes")
bp.register_blueprint(browse.bp)
bp.register_blueprint(categories.bp)
bp.register_blueprint(search.bp)
