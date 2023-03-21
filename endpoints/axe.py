from flask import Blueprint, request, jsonify
import subprocess

axe_bp = Blueprint('axe_bp', __name__)

@axe_bp.route('/axe', methods=['GET'])
def axe():
    url = request.args.get('url')
    if not url:
        return jsonify({'error': 'URL parameter not provided'}), 400

    cmd = ['axe', url, '--chromedriver-path', '/usr/local/bin/chromedriver', '--chrome-options="no-sandbox"', '--stdout']
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    output = result.stdout.strip().split('\n')

    return jsonify(output)


