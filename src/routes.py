from flask import Blueprint
from src.controllers.domain_lookup_controller import domain_lookup

# main blueprint to be registered with application
api = Blueprint('api', __name__)

# register user with api blueprint
api.register_blueprint(domain_lookup)
