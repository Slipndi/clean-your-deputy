
from asyncore import write
import json
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
ROUND_VALUE = 2
RESPONSE_FORMAT = 'json'

class deputies_form(FlaskForm):
    select_field = SelectField(u'Choix du député')

class parties_form(FlaskForm):
    select_field = SelectField(u'Choix du parti')
    


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
        
        all_group_json = requests.get('https://www.nosdeputes.fr/organismes/groupe/json').json()
        party_form = parties_form()
        party_form.select_field.choices = [(party['organisme']['acronyme'], party['organisme']['nom']) for party in all_group_json['organismes']]
        
        return render_template('/components/select-form.html', deputy=deputy_form, party=party_form)
    
    @app.route('/deputy', methods=['GET'])
    def get_deputy() -> render_template :
        """Récupération de toutes les données à afficher sur le député séléctionné

        Returns:
            render_template: retourne le template d'affichage avec les informations et le graphique
            reprenant les informations 
        """        
        deputy_slug = request.args.get('select_field')
        deputy_activities = get_deputies_activities()
        moyenne={}
        deputy_stats={}

        deputy_details = get_deputy_data(deputy_slug, deputy_activities, deputy_stats)
        get_global_statistics(deputy_activities, moyenne)
        
        chart = generate_chart(deputy_stats, moyenne)
        
        return render_template(
            '/components/deputy/details.html',  
            deputy_activities=deputy_details,
            deputy_stats=deputy_stats,
            chart = chart
        )

    @app.route('/party', methods=['GET'])
    def get_party() -> render_template :
        """Route permetant l'affichage des partis politiques

        Returns:
            render_template: la page html composé des informations  JSON et du graphique généré.
        """        
        moyenne={}
        party_acronyme = request.args.get('select_field')
        party_data =get_party_data (party_acronyme, get_deputies_activities())
        get_global_statistics(get_deputies_activities(), moyenne)
        
        chart = generate_chart(party_data, moyenne)
        
        return render_template('components/party/details.html', party=party_data, chart=chart)
    
    
    def generate_chart(selected_stats : dict, global_stats : dict) -> base64 :
        """Génération d'un chart à l'aide de la bibliothèque matplotlib
        

        Args:
            selected_stats (dict): Statistiques spécifique au député / parti
            global_stats (dict): Statistiques générale 

        Returns:
            base64: l'image en base64
        """        
        nom = selected_stats['nom']
        # On vide le graphique pour éviter les superpositions
        plt.clf()
        
        # Mise en forme de la data pour affichage
        labels = ['proposés', 'signés', 'adoptés']
        selected = [selected_stats['proposes'], selected_stats['signes'], selected_stats['adoptes']]
        general = [global_stats['proposes'], global_stats['signes'], global_stats['adoptes']]
        
        # génération des barres
        x_axis = np.arange(len(labels))
        plt.bar(x_axis -0.2, selected, width=0.4, label=nom)
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
    
    def get_deputies_activities() -> dict :
        """Récupération de l'activité de tous les députés

        Returns:
            dict: Récupération de toute les données de l'api
        """        
        return requests.get(f'https://www.nosdeputes.fr/synthese/data/{RESPONSE_FORMAT}').json()

    def get_deputy_data(deputy_slug:str, deputy_activities:dict, deputy_stats:dict) -> dict :
        """Récupération des données du député selectionné uniquement

        Args:
            deputy_slug (str): slug du député
            deputy_activities (dict): activité général des députés
            deputy_stats (dict): dict à renseigner et renvoyer

        Returns:
            dict: _description_
        """        
        for data in deputy_activities['deputes'] : 
            if data['depute']['slug'] == deputy_slug :
                deputy_details = data["depute"]
                deputy_stats['nom'] = data['depute']['nom']
                deputy_stats['weeks'] = data['depute']['semaines_presence']
                if deputy_stats['weeks'] > 0 : 
                    deputy_stats['proposes'] = round(data['depute']['amendements_proposes'] /data['depute']['semaines_presence'] ,ROUND_VALUE)
                    deputy_stats['signes'] = round(data['depute']['amendements_signes']/data['depute']['semaines_presence'] ,ROUND_VALUE)
                    deputy_stats['adoptes'] = round(data['depute']['amendements_adoptes']/data['depute']['semaines_presence'] ,ROUND_VALUE)
                else : 
                    deputy_stats['proposes'] = 0
                    deputy_stats['signes'] = 0
                    deputy_stats['adoptes'] = 0
        return deputy_details
    
    def get_party_data(acronyme : str, deputies_activity: dict) -> dict : 
        """ Récupération des données du parti politique séléctionné

        Args:
            acronyme (str): code du parti
            deputies_activity (dict): dict python contenant l'activité des députés

        Returns:
            dict: dict reprenant les données à afficher sur la page principale
        """        
        party_data = {}
        count=weeks=oral=write=proposes=signes=adoptes=presences=interventions=rapports=0
        
        for data in deputies_activity['deputes'] :
            if data['depute']['groupe_sigle'] == acronyme :
                count+=1
                weeks += data['depute']['semaines_presence']
                oral += data['depute']['questions_orales']
                write += data['depute']['questions_ecrites']
                proposes += data['depute']['amendements_proposes']
                signes += data['depute']['amendements_signes']
                adoptes += data['depute']['amendements_adoptes']
                presences += data['depute']['commission_presences']
                interventions += data['depute']['commission_interventions']
                rapports += data['depute']['rapports']
                
        party_data['count'] = count
        party_data['nom'] = acronyme
        party_data['weeks'] = weeks
        if weeks > 0 : 
            party_data['oral'] = round(oral/weeks, ROUND_VALUE)
            party_data['write'] = round(write/weeks, ROUND_VALUE)
            party_data['proposes'] = round(proposes/weeks, ROUND_VALUE)
            party_data['signes'] = round(signes/weeks, ROUND_VALUE)
            party_data['adoptes'] = round(adoptes/weeks, ROUND_VALUE)
            party_data['interventions'] = round(interventions/presences, ROUND_VALUE)
            party_data['rapports'] = round(rapports/presences, ROUND_VALUE)
        else : 
            party_data['oral'] = 0
            party_data['write'] = 0
            party_data['proposes'] = 0
            party_data['signes'] = 0
            party_data['adoptes'] = 0
            party_data['interventions'] = 0
            party_data['rapports'] = 0
        
        return party_data
        

    def get_global_statistics(deputy_activities:dict, moyenne:dict) -> None :
        """Récupération de toutes les statistiques

        Args:
            deputy_activities (dict): dictionnaire python contenant toute l'activité des députés
            moyenne (dict): dict à retourner
        """        
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
        
        moyenne['weeks'] = round(weeks_quantity / deputy_number,ROUND_VALUE)
        moyenne['proposes'] = round(amendements_proposes / weeks_quantity, ROUND_VALUE)
        moyenne['signes'] = round(amendements_signes / weeks_quantity, ROUND_VALUE)
        moyenne['adoptes'] = round(amendements_adoptes / weeks_quantity, ROUND_VALUE)
        
    return app