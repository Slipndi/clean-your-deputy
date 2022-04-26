import os
from tkinter import Image

from flask import Flask, render_template
import requests

# Constantes utiles dans l'application
PICTURE_HEIGHT = 60
RETURN_FORMAT = 'json'

def create_app(test_config=None) -> Flask:        
    # Création et configuration de l'application
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_pyfile('config.py', silent=True)

    @app.route('/', methods=['GET'])
    def index():
        return render_template('index.html')

    @app.route('/deputies', methods=['GET'])
    def get_all_deputies():
        all_deputies = requests.get('https://www.nosdeputes.fr/deputes/enmandat/json').json()
        return all_deputies
    
    @app.route('/deputy/<deputy_slug>', methods=['GET'])
    def get_deputy(deputy_slug):
        deputy_picture = requests.get(f'https://www.nosdeputes.fr/depute/photo/{deputy_slug}/{PICTURE_HEIGHT}').content
        deputy_data = requests.get(f'https://www.nosdeputes.fr/{deputy_slug}/{RETURN_FORMAT}').json()
        return deputy_picture
    
    @app.route('/political-parties', methods=['GET'])
    def get_all_political_parties():
        return True
    
    @app.route('/political-party/<political_party_id>', methods=['GET'])
    def get_political_party(political_party_id):
        return True    
    
    return app