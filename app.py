from flask import Flask
from endpoints.axe import axe_bp
from endpoints.other import other_bp

EqualifyApp = Flask(__name__)

EqualifyApp.register_blueprint(axe_bp)
EqualifyApp.register_blueprint(other_bp)

if __name__ == '__main__':
    EqualifyApp.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8083)))
