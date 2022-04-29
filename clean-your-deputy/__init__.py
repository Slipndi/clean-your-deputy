import os
import string
from tkinter import Image
from tkinter.tix import Select

from flask import Flask, render_template, request
import requests
import secrets
import json
from flask_wtf import FlaskForm
from wtforms import SelectField

# Constantes utiles dans l'application
PICTURE_HEIGHT = 60
RESPONSE_FORMAT = 'json'

class deputies_form(FlaskForm):
    select_field = SelectField('Choix du député')


def create_app(test_config=None) -> Flask:        
    # Création et configuration de l'application
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_pyfile('config.py', silent=True)
    # génération d'une api key aléatoire
    app.secret_key = secrets.token_urlsafe(16)

    @app.route('/', methods=['GET'])
    def index():
        """ Point d'entrée de l'application, génère l'affichage de la liste des députés

        Returns:
            render_template: renvois le template component/select-form.html accompagné d'un simple formulaire
            ce formulaire est composé d'un select
        """
        all_deputies_json = requests.get('https://www.nosdeputes.fr/deputes/enmandat/json').json()
        deputy_form = deputies_form()
        deputy_form.select_field.choices = [(deputy['depute']['slug'], deputy['depute']['nom']) for deputy in all_deputies_json['deputes']]   

        return render_template('/components/select-form.html', form_to_display=deputy_form)

    
    @app.route('/deputy', methods=['GET'])
    def get_deputy():
        deputy_slug = request.args.get('select_field')
        deputy_activities = requests.get(f'https://www.nosdeputes.fr/synthese/data/{RESPONSE_FORMAT}').json()
        for data in deputy_activities['deputes'] : 
            if data['depute']['slug'] == deputy_slug :
                deputy_details = data["depute"]
        
        return render_template(
            '/components/details.html',  
            deputy_activities=deputy_details
        )

    
    @app.route('/political-parties', methods=['GET'])
    def get_all_political_parties():
        return True
    
    @app.route('/political-party/<political_party_id>', methods=['GET'])
    def get_political_party(political_party_id):
        return True    
    
    return app