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
        moyenne={}
        deputy_stats = {}

        deputy_details = get_deputy_data(deputy_slug, deputy_activities, deputy_stats)
        
        get_global_statistics(deputy_activities, moyenne)
        
        return render_template(
            '/components/details.html',  
            deputy_activities=deputy_details,
            dt=moyenne,
            deputy_stats=deputy_stats
        )

    def get_deputy_data(deputy_slug, deputy_activities, deputy_stats):
        for data in deputy_activities['deputes'] : 
            if data['depute']['slug'] == deputy_slug :
                deputy_details = data["depute"]
                deputy_stats['weeks'] = data['depute']['semaines_presence']
                deputy_stats['proposes'] = round(data['depute']['amendements_proposes'] /data['depute']['semaines_presence'] ,2)
                deputy_stats['signes'] = round(data['depute']['amendements_signes']/data['depute']['semaines_presence'] ,2)
                deputy_stats['adoptes'] = round(data['depute']['amendements_adoptes']/data['depute']['semaines_presence'] ,2)
        return deputy_details

    def get_global_statistics(deputy_activities, moyenne):
        deputy_number=0
        weeks_quantity=0
        amendements_proposes=0
        amendements_signes=0
        amendements_adoptes=0
        
        for data in deputy_activities['deputes'] : 
            deputy_number += 1
            weeks_quantity += data['depute']['semaines_presence']
            amendements_proposes += data['depute']['amendements_proposes']
            amendements_signes += data['depute']['amendements_signes']
            amendements_adoptes += data['depute']['amendements_adoptes']
        
        moyenne['weeks'] = round(weeks_quantity / deputy_number,2)
        moyenne['proposes'] = round(amendements_proposes / weeks_quantity, 2)
        moyenne['signes'] = round(amendements_signes / weeks_quantity, 2)
        moyenne['adoptes'] = round(amendements_adoptes / weeks_quantity, 2)

    
    @app.route('/political-parties', methods=['GET'])
    def get_all_political_parties():
        return True
    
    @app.route('/political-party/<political_party_id>', methods=['GET'])
    def get_political_party(political_party_id):
        return True    
    
    return app