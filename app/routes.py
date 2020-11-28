from flask import Flask
from flask import Flask, render_template, flash, redirect, url_for, request
from flask_table import Table, Col

from app import app
from app.planttabel import get_planttabel, merge_plantenfiches
from app.googleplanten import GooglePlanten


@app.route('/test')
def test():
    print(app.config['SECRET_KEY'])
    return render_template('template.html', pagetitle='Test')
    
@app.route('/')
@app.route('/index' , methods=['GET', 'POST'])
@app.route('/home', methods=['GET', 'POST'])
def index():
    formfilter = False
    formselectie = False
    pagesubtitle = False
    pagesubcontent = False
    pagesubtype = False

    if request.method == "POST":

        formsubmit = request.form.get('submit')

        if formsubmit == 'Filter planten':
            formsoortplant = request.form.get('soortplant')
            formbloei = request.form.getlist('bloei')
            formbodemvereisten = request.form.getlist('bodemvereisten')
            formzonschaduw = request.form.getlist('zonschaduw')

            formfilter = [{'soortplant': formsoortplant, 'bloei': formbloei, 'bodemvereisten': formbodemvereisten, 'zonschaduw': formzonschaduw } ]
            filter_formsoortplant = ""
            filter_formbloei = ""
            filter_formbodemvereisten = ""
            filter_formzonschaduw = ""
            if len(formsoortplant) > 0:
                filter_formsoortplant = "Soort: {}".format(formsoortplant)
            if len(formbloei) > 0:
                if not len(filter_formbloei) > 0:
                    filter_formbloei = "Bloei: "
                for e in formbloei:
                    filter_formbloei = "{} {}".format(filter_formbloei, e)                
            if len(formbodemvereisten) > 0:
                if not len(filter_formbodemvereisten) > 0:
                    filter_formbloei = "Bodemvereisten: "                
                for e in formbodemvereisten:
                    filter_formbodemvereisten = "{} {}".format(filter_formbodemvereisten, e)
            if len(formzonschaduw) > 0:      
                if not len(filter_formbloei) > 0:
                    filter_formzonschaduw = "Zon/Schaduw: "                
                for e in formzonschaduw:
                    filter_formzonschaduw = "{} {}".format(filter_formzonschaduw, e)

            formtitel = "Filters"
            formselectie = "{}  {}  {}  {}".format(filter_formsoortplant, filter_formbloei, filter_formbodemvereisten, filter_formzonschaduw)
            
        elif formsubmit == 'Maak fiches':
            selected_fiches = request.form.getlist('plantid[]')
            aantal_gemaakte_fiches = 0
            if selected_fiches and len(selected_fiches) > 0:
                planten.update_sheet_last_editor()
                result, aantal_gemaakte_fiches = merge_plantenfiches(selected_fiches)
                if result:
                    pagesubtitle = "Fiches zijn aangemaakt"
                    pagesubtype = "fiches"
                    pagesubcontent = "{} fiche(s) weggeschreven.".format(aantal_gemaakte_fiches)                    
                else:
                    pagesubtitle = "Fout bij het maken van de fiches"
                    pagesubcontent = "Geen resultaten"
            else:
                pagesubtitle = "Er werden geen fiches geselecteerd"
                pagesubcontent = "Geen resultaten"


    plantenstats, planttabel, aantal_planten = get_planttabel(formfilter)
    
    '''
    aantal_zon = 0
    aantal_zonschaduw = 0
    aantal_schaduw = 0
    if aantal_planten > 0:
        aantal_zon=int(100*float(plantenstats[0])/float(aantal_planten))
        aantal_zonschaduw=int(100*float(plantenstats[1])/float(aantal_planten)),
        aantal_schaduw=int(100*float(plantenstats[2])/float(aantal_planten)),'''

    return render_template('plantform.html', 
            pagesubcontent=pagesubcontent,
            pagesubtitle=pagesubtitle,
            pagesubtype=pagesubtype,
            pagesubbekijkfiches=app.config['DRIVE_VIEW'],
            url_google_add=app.config['DRIVE_ADD'],
            url_google_edit=app.config['DRIVE_EDIT'],
            url_google_list=app.config['DRIVE_LIST'],
            pagetitle='Home', 
            soortplant=[{'name':'Boom'}, {'name':'Bloeiende heester'}, 
            {'name':'Groene heester'}, {'name':'Klimplant'}, {'name':'Vaste plant'}, 
            {'name':'Tweejarige'}, {'name':'Bodembedekker'},
            {'name':'Gras'}, {'name':'Bamboe'},
            ],
            bodemvereisten=[{'name':'Geen vereisten'}, {'name':'Vochtig'}, 
            {'name':'Goed doorlaatbaar'}, {'name':'Rijk'}, {'name':'Arm'}, 
            {'name':'Zand'}, {'name':'Zuur'},
            {'name':'Humusrijk'}, {'name':'Kalkrijk'},
            ],
            zonschaduw=[{'name':'Zon'}, {'name':'Halfschaduw'}, {'name':'Schaduw'}
            ],
            bloei=[{'name':'Jan'}, {'name':'Feb'}, 
            {'name':'Mar'}, {'name':'Apr'}, {'name':'Mei'}, 
            {'name':'Jun'}, {'name':'Jul'}, {'name':'Aug'}, {'name':'Sep'},
            {'name':'Okt'}, {'name':'Nov'}, {'name':'Dec'},
            ],
            aantal_planten=aantal_planten,
            planttabel=planttabel
            )


@app.route('/about')
def about():
    return render_template('template.html', pagetitle='About')

