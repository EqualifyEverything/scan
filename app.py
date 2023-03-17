from flask import Flask
from endpoints.axe import axe_blueprint
# Import other blueprints here

app = Flask(__name__)

app.register_blueprint(axe_blueprint)
# Register other blueprints here

# Enable logging
import logging
logging.basicConfig(level=logging.DEBUG)

# ... (API key validation and other configurations)

if __name__ == '__main__':
    app.run()
