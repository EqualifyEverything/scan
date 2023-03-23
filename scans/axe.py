import json
import subprocess
from flask import Flask, request, jsonify

with open('maps/axe.json') as f:
    header_mapping = json.load(f)

app = Flask(__name__)

def process_response(response_dict, mapping):
    processed = {}
    for key, value in response_dict.items():
        if isinstance(value, dict):
            for inner_key, inner_value in value.items():
                combined_key = f"{key}.{inner_key}"
                new_key = mapping.get(combined_key)
                if new_key:
                    processed[new_key] = inner_value
                else:
                    processed[combined_key] = inner_value
        else:
            new_key = mapping.get(key)
            if new_key:
                processed[new_key] = value
            else:
                processed[key] = value
    return processed


@app.route('/axe')
def axe_scan():
    url = request.args.get('url')
    cmd = f'axe {url} --chromedriver-path /usr/local/bin/chromedriver --chrome-options="no-sandbox" --stdout'
    output = subprocess.check_output(cmd, shell=True)
    response = json.loads(output.decode('utf-8'))

    # Check if the response is a list and get the first item
    if isinstance(response, list) and len(response) > 0:
        response = response[0]

    # Define header mapping
    with open('maps/axe.json') as f:
        header_mapping = json.load(f)

    # Process response
    transformed_response = process_response(response, header_mapping)

    # Return transformed response
    return jsonify(transformed_response)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8083)
