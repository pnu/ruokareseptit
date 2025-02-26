"""User pages
"""

from flask import Blueprint

from . import recipes
from . import reviews


bp = Blueprint("my", __name__, url_prefix="/my")
bp.register_blueprint(recipes.bp)
bp.register_blueprint(reviews.bp)
