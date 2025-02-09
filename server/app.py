from flask import Flask
from api import api_blueprint
from dashboard import create_dashboard
from library import read_config, cloud_storage_read

server = Flask(__name__)

config = read_config()

# == get the files from the storage account, but don't overwrite it if they already exist
cloud_storage_read(config['data']['summary'],False)
cloud_storage_read(config['data']['detail'],False)

server.secret_key = config['secret_key']

server.register_blueprint(api_blueprint)

dash_app = create_dashboard(server)

if __name__ == "__main__":
    server.run(host='0.0.0.0', port=8080, debug=True)
