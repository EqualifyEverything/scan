from flask import Blueprint, request, jsonify
import subprocess
import re

axe_blueprint = Blueprint('axe', __name__)

@axe_blueprint.route('/axe-core', methods=['GET'])
def axe_core():
    # ... (rest of the axe_core function)
