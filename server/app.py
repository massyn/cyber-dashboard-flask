from flask import Flask
from api import api_blueprint
from dashboard import create_dashboard
from library import read_config

server = Flask(__name__)
config = read_config()

server.secret_key = config['secret_key']

server.register_blueprint(api_blueprint)

dash_app = create_dashboard(server)

if __name__ == "__main__":
    server.run(host='0.0.0.0', port=8080, debug=True)
