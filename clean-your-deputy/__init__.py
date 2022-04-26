import os

from flask import Flask, render_template


def create_app(test_config=None) -> Flask:
    # Création et configuration de l'application
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_pyfile('config.py', silent=True)

    @app.route('/', methods=['GET'])
    def index():
        return render_template('index.html')

    @app.route('/deputies', methods=['GET'])
    def get_al_deputies():
        return True
    
    @app.route('/deputy/<deputy_id>')
    def get_deputy(deputy_id):
        return deputy_id
    
    @app.route('/political-parties', methods=['GET'])
    def get_all_political_parties():
        return True
    
    @app.route('/political-party/<political_party_id>')
    def get_political_party(political_party_id):
        return True    
    return app