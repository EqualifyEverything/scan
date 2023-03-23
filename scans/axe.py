import json
import subprocess
from flask import Flask, request, jsonify

with open('maps/axe.json') as f:
    header_mapping = json.load(f)

app = Flask(__name__)

@app.route('/axe')
def axe_scan():
    url = request.args.get('url')
    cmd = f'axe {url} --chromedriver-path /usr/local/bin/chromedriver --chrome-options="no-sandbox" --stdout'
    output = subprocess.check_output(cmd, shell=True)
    response = json.loads(output.decode('utf-8'))

    # Define header mapping
    with open('maps/axe.json') as f:
        header_mapping = json.load(f)

    # Transform headers
    for item in response:
        # Keep only mapped fields
        item_copy = {}
        for key, value in item.items():
            new_key = header_mapping.get(key)
            if new_key:
                item_copy[new_key] = value
        item.clear()
        item.update(item_copy)

        # Flatten nested fields
        for field in ['testEngine', 'testEnvironment']:
            flattened_fields = {}
            for key, value in item.items():
                if key.startswith(field):
                    new_key = key.replace(f"{field}.", "")
                    flattened_fields[new_key] = value
            item.update(flattened_fields)
            for key in flattened_fields:
                del item[f"{field}.{key}"]

    # Return transformed response
    return jsonify(response)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8083)
