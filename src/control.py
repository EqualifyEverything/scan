from utils.watch import logger
import threading
from flask import Flask, jsonify
import uppies

app = Flask(__name__)
uppies_thread = None


def run_uppies():
    uppies.main()


@app.route('/uppies/start', methods=['POST'])
def start_uppies():
    global uppies_thread
    if uppies_thread is None or not uppies_thread.is_alive():
        uppies_thread = threading.Thread(target=run_uppies)
        uppies_thread.start()
        return jsonify({'status': 'uppies started'})
    else:
        return jsonify({'status': 'uppies already running'})


@app.route('/uppies/stop', methods=['POST'])
def stop_uppies():
    global uppies_thread
    if uppies_thread and uppies_thread.is_alive():
        # Implement a way to stop uppies.py gracefully, e.g., by setting a flag in uppies.py
        # ...
        uppies_thread.join()  # Wait for the thread to stop
        return jsonify({'status': 'uppies stopped'})
    else:
        return jsonify({'status': 'uppies not running'})


@app.route('/uppies/status', methods=['GET'])
def uppies_status():
    if uppies_thread and uppies_thread.is_alive():
        return jsonify({'status': 'running'})
    else:
        return jsonify({'status': 'not running'})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8086)
