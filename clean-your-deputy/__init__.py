
from flask import Flask, render_template, request
import requests
import secrets
import numpy as np
import matplotlib
matplotlib.use('Agg')

import matplotlib.pyplot as plt
from flask_wtf import FlaskForm
from wtforms import SelectField

import base64
from io import BytesIO

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
    def index() -> str:
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
        """Récupération de toutes les données à afficher sur le député séléctionné

        Returns:
            render_template: retourne le template d'affichage avec les informations et le graphique
            reprenant les informations 
        """        
        deputy_slug = request.args.get('select_field')
        deputy_activities = requests.get(f'https://www.nosdeputes.fr/synthese/data/{RESPONSE_FORMAT}').json()
        moyenne={}
        deputy_stats={}

        deputy_details = get_deputy_data(deputy_slug, deputy_activities, deputy_stats)
        get_global_statistics(deputy_activities, moyenne)
        
        chart = generate_chart(deputy_stats, moyenne)
        
        return render_template(
            '/components/details.html',  
            deputy_activities=deputy_details,
            deputy_stats=deputy_stats,
            chart = chart
        )

    def get_deputy_data(deputy_slug, deputy_activities, deputy_stats) -> dict :
        for data in deputy_activities['deputes'] : 
            if data['depute']['slug'] == deputy_slug :
                deputy_details = data["depute"]
                deputy_stats['nom'] = data['depute']['nom']
                deputy_stats['weeks'] = data['depute']['semaines_presence']
                deputy_stats['proposes'] = round(data['depute']['amendements_proposes'] /data['depute']['semaines_presence'] ,2)
                deputy_stats['signes'] = round(data['depute']['amendements_signes']/data['depute']['semaines_presence'] ,2)
                deputy_stats['adoptes'] = round(data['depute']['amendements_adoptes']/data['depute']['semaines_presence'] ,2)
        return deputy_details

    def get_global_statistics(deputy_activities, moyenne) -> None :
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
    
    
    def generate_chart(selected_stats : dict, global_stats : dict) :
        # On vide le graphique pour éviter les superpositions
        plt.clf()
        
        # Mise en forme de la data pour affichage
        labels = ['proposés', 'signés', 'adoptés']
        selected = [selected_stats['proposes'], selected_stats['signes'], selected_stats['adoptes']]
        general = [global_stats['proposes'], global_stats['signes'], global_stats['adoptes']]
        
        # génération des barres
        x_axis = np.arange(len(labels))
        plt.bar(x_axis -0.2, selected, width=0.4, label=selected_stats['nom'])
        plt.bar(x_axis + 0.2, general, width=0.4, label='moyenne')

        # labels
        plt.xticks(x_axis, labels)
        
        # Ajout de la légende
        plt.legend()
        
        # Retour en base64 pour affichage
        buf = BytesIO()
        plt.savefig(buf, format="png", transparent=True)
        data = base64.b64encode(buf.getbuffer()).decode("ascii")
        
        return data
    
    return app