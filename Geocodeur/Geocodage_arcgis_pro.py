# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:        Request géocodage PR+ABS (Arcgis Pro)
# Author:      J Samaniego
# Created:     05/05/2022
# Contenu :
# Le script pemret de géocoder en PR+ABS une donnée sur le référentiel autoroutier VA.
# Le script fait appel à un API développé par Naomis et hébergé sur l'Arcgis sever VA.
# L'API nécéssite un format JSON en entrée et peut géocoder au maximum 150 entitées
# pour les points/polygons et 130 pour les lignes en une requête.
#-------------------------------------------------------------------------------

import json
import sys,os
import time
from datetime import timedelta
import arcpy
import requests
start = time.time()

#-------------------------------------------------------------------------------------------------------------------
#**********************************************--FONCTIONS--********************************************************
#-------------------------------------------------------------------------------------------------------------------

#-----------------------------------------Fonctions message arcpy---------------------------------------------------
def TRACE(txt):
    print(txt)
    arcpy.AddMessage(txt)

def ALERTE(txt):
    arcpy.AddWarning(txt)

def ERREUR(txt):
    TRACE ("ERREUR : " + txt)
    arcpy.AddError(txt)
    sys.exit ()

def verif_input(geom):
    if geom in ('Point','Line','Polyline','Polygon'):
        TRACE ('Geometry ok')
    else:
        ERREUR("La donnée n'est pas au format ligne ou point ")

#----------------------------------------- Classe/fonctions API ---------------------------------------------------
class API_GeomToPR:
    def request_GeomToPR_point (self,x,y,projection,field,va_unique):
        if va_unique ==True:
            va='true'
        else:
            va='false'
        if projection == 'AutorouteSpecifique':
            query = {"GeometrieEsriJson": {"x": x, "y": y, "spatialReference": {"wkid": 2154}},
                       "OptionProjection": {"codeSegment": field+'[_]%', "LocalisationPointProjete": projection,
                                            "EstUniquementSurReseauVinciAutoroute": va},
                       "ThematiquesResultat": ["AdministratifPointInitial", "AdministratifPointProjete", "APS",
                                               "PointLePlusProche"]}

        else:
            query = {"GeometrieEsriJson": {"x": x, "y": y, "spatialReference": {"wkid": 2154}},
                       "OptionProjection": {"codeSegment": field, "LocalisationPointProjete": projection,
                                            "EstUniquementSurReseauVinciAutoroute": va},
                       "ThematiquesResultat": ["AdministratifPointInitial", "AdministratifPointProjete", "APS",
                                               "PointLePlusProche"]}
        return query

    def request_GeomToPR_line(self,coors,projection,field,va_unique):
        if va_unique ==True:
            va='true'
        else:
            va='false'
        if projection == 'AutorouteSpecifique':
            query = {"GeometrieEsriJson": {"paths": [coors],"spatialReference": {"wkid": 2154}},
                        "OptionProjection": {"codeSegment": field+'[_]%',"LocalisationPointProjete": projection,
                                             "EstUniquementSurReseauVinciAutoroute": va},
                       "ThematiquesResultat": ["AdministratifPointInitial", "AdministratifPointProjete", "APS",
                                               "PointLePlusProche"]}
        else:
            query = {"GeometrieEsriJson": {"paths": [coors],"spatialReference": {"wkid": 2154}},
                        "OptionProjection": {"codeSegment": field,"LocalisationPointProjete": projection,
                                             "EstUniquementSurReseauVinciAutoroute": va},
                       "ThematiquesResultat": ["AdministratifPointInitial", "AdministratifPointProjete", "APS",
                                               "PointLePlusProche"]}
        return query

    def start_request (self,coder,parameter):
        jsonData = json.dumps(parameter)
        js = '&f=json'
        #url = 'https://arcgisserverdev.vinci-autoroutes.com/arcgis/rest/services/Referentiel/ReferentielGeocodeurV2/MapServer/exts/Geocodeur/Geom2APS?GeometrieEtOption=%s%s'
        url = coder+'?GeometrieEtOption=%s%s'
        result = requests.get(url % (jsonData, js)).json()
        return result

    def API_resultat (self,resultat):
        # Dic Résultat APS debut
        c = resultat['ApsDebut']
        d = resultat['ApsFin']
        g = resultat['ApsMilieu']
        # Dic Résultat sur le segment (code segment notamment)
        e = c['Segment']
        j = d['Segment']
        k = g['Segment']
        # Dic Résultat sur les limites d'exploitation
        h = g['AdministratifPointProjete']
        # Variable à récupérer sur le JSON résultat
        pr_debut  = c['Pr']
        pr_fin    = d['Pr']
        pr_centre = g['Pr']
        deport_centre = g['Deport']
        deport_debut  = c['Deport']
        deport_fin    = d['Deport']
        sens = k['Sens']#['Valeur'][4:]
        route       = k['Autoroute']
        route_debut = e['Autoroute']
        route_fin   = j['Autoroute']
        code_route       = k['Code']
        code_route_debut = e['Code']
        code_route_fin   = j['Code']
        sca_code  = h['sca']['code']
        sca_nom   = h['sca']['nom']
        dex_code  = h['dex']['code']
        dex_nom   = h['dex']['nom']
        dre_code  = h['dre']['code']
        dre_nom   = h['dre']['nom']
        dist_code = h['district']['code']
        dist_nom  = h['district']['nom']
        ce_code   = h['ce']['code']
        ce_nom    = h['ce']['nom']
        insee     = h['commune']['code']
        commune   = h['commune']['nom']

        #Ajout des résultat dans une liste sous forme de dictionnaire
        dic_result = {'PR':pr_centre,'PR_CENTRE':pr_centre,'PR_DEBUT': pr_debut, 'PR_FIN':pr_fin,
                      'DEPORT':deport_centre,'DEPORT_CENTRE': deport_centre,
                      'DEPORT_DEBUT': deport_debut,'DEPORT_FIN': deport_fin, 'SENS': sens, 'CODE': code_route,
                      'CODE_DEBUT': code_route_debut, 'CODE_FIN': code_route_fin,
                      'AUTOROUTE':route,'AUTOROUTE_DEBUT':route_debut,'AUTOROUTE_FIN':route_fin,'SCA': sca_code,
                      'SCA_name': sca_nom, 'DEX': dex_code, 'DEX_name': dex_nom,'DRE': dre_code, 'DRE_name': dre_nom,
                      'DISTRICT': dist_code, 'DISTRICT_name': dist_nom,'CENTRE_ENTRETIEN': ce_code,'CE_name': ce_nom,
                      'INSEE': insee, 'COMMUNE': commune}
        return dic_result

#-------------------------------------- FONCTION PRINCIPALE du Script(Traitement) ------------------------------------
def arcgis_GeomtoPR(path,fields_add_input,projection,aut_field,proj_va,calc_polygon,coder):
    # Vérification INPUT
    TRACE('Géocodage sur VA uniquement: {}'.format(proj_va))
    desc = arcpy.Describe(path)
    geom_type = desc.shapeType
    TRACE(geom_type)
    if geom_type=='Polygon':
        TRACE ('Calcul du début et fin des polygon : {}'.format(calc_polygon))
    verif_input(geom_type)
    workspace = desc.path
    TRACE('Workspace : {}'.format(workspace))
    # Création du nombre max de requêtes à envoyer en même temps (Point/Polygon=150 et ligne=130)
    fields_add=fields_add_input
    if geom_type in ('Point','Polygon'):
        paquet=150
    else:
        paquet=130

    # Vérification si les champs du géocodage à récupérer existent déjà dans la donnée
    # Si oui => indique que le champ existe déjà
    # Si non => création du champ
    fields_names = [f.name for f in arcpy.ListFields(path)]
    for field in fields_add:
        if field not in fields_names:
            TRACE('Création du champ : {}'.format(field))
            if field == 'CENTRE_ENTRETIEN':
                alias = "Centre d'entretien"
                arcpy.AddField_management(path, field, "TEXT", field_alias=alias)
            elif field in ('PR','PR_DEBUT','PR_CENTRE','PR_FIN'):
                if field!='PR':
                    alias_tmp = field.split('_')
                    alias     = alias_tmp[0]+' '+alias_tmp[1].lower()
                else:
                    alias = None
                arcpy.AddField_management(path,field,"FLOAT",field_alias=alias)
            elif field in ('DEPORT','DEPORT_DEBUT','DEPORT_CENTRE','DEPORT_FIN'):
                alias_tmp = field.replace('_', ' ')
                alias     = alias_tmp.capitalize()
                arcpy.AddField_management(path, field, "FLOAT", field_alias=alias)
            elif field in ('DISTRICT','COMMUNE'):
                alias = field.capitalize()
                arcpy.AddField_management(path, field, "TEXT", field_alias=alias)
            elif field == 'INSEE':
                alias= 'Code '+field
                arcpy.AddField_management(path, field, "TEXT", field_alias=alias)
            else:
                arcpy.AddField_management(path, field, "TEXT",field_length=50)
        else:
            TRACE ('le champ {} existe déjà'.format(field))

    # Comptage des entités dans la table => donne le nombre total d'éléments à géocoder
    long = arcpy.management.GetCount(path)
    # Création des liste de requete à envoyer par paquet de 150 max
    list_rq = [] # liste de requete temporaire
    list_rq_final= [] # Liste de requete à envoyer par paquet de 150
    step = 1
    ##fields_names = [f.name for f in arcpy.ListFields(path)]
    TRACE ('!!!!! Récupération des infos dans la donnée à géocoder !!!!!')
    # Ajout du champ système geometry dans la liste des champs
    list_tmp=["SHAPE@"]
    try:
        if projection in ('AutorouteSpecifique'):
            list_tmp.append(aut_field)
        else:
            pass
    except:
        ERREUR ("Type projection : {} => le champ autoroute doit être indiqué".format(projection))

    pr_polygon = []
    with arcpy.da.SearchCursor(path, list_tmp) as cursor:
        for idx,row in enumerate(cursor):
            TRACE('Récup : {}/{}'.format(str(idx+1),str(long)))
            ##geom = row.geometry()
            if projection== 'AutorouteSpecifique':
                aut=row[1]
            else:
                aut=''
            if geom_type == 'Point':
                pnt = row[0].getPart()
                x_coor = pnt.X
                y_coor = pnt.Y
                query_t = API_GeomToPR().request_GeomToPR_point (x_coor,y_coor,projection,aut,proj_va)
            elif geom_type == 'Polygon':
                pnt = row[0].centroid
                x_coor = pnt.X
                y_coor = pnt.Y
                query_t = API_GeomToPR().request_GeomToPR_point (x_coor,y_coor,projection,aut,proj_va)
                if calc_polygon is True:
                    pnts = row[0].getPart()
                    list_tmp=[]
                    for idx2,coor in enumerate(pnts):
                        if idx2 > 0:
                            ERREUR('MULIPARTIE DANS LA DONNÉE')
                        for i in coor:
                            query_tmp = API_GeomToPR().request_GeomToPR_point (i.X,i.Y,projection,aut,proj_va)
                            response_tmp = API_GeomToPR().start_request(coder, [query_tmp])
                            list_tmp.append(API_GeomToPR().API_resultat(response_tmp['Resultat'][0]))
                            list_prd_tmp=[]
                            list_prf_tmp = []
                            for i in list_tmp:
                                list_prd_tmp.append([i['PR_DEBUT'],i['CODE_DEBUT'],i['AUTOROUTE_DEBUT']])
                                list_prf_tmp.append([i['PR_FIN'],i['CODE_FIN'],i['AUTOROUTE_FIN']])
                    pr_polygon.append([min(list_prd_tmp),max(list_prf_tmp)])
            elif geom_type in ('Line','Polyline'):
                pnt = row[0].getPart()
                list_coor=[]
                for idx2,coor in enumerate(pnt):
                    if idx2 > 0:
                        ERREUR('MULIPARTIE DANS LA DONNÉE')
                    for i in coor:
                        list_coor.append([i.X,i.Y])
                '''
                startpt = row[0].firstPoint
                startx  = startpt.X
                starty  = startpt.Y
                endpt   = row[0].lastPoint
                endx    = endpt.X
                endy    = endpt.Y
                query_t  = API_GeomToPR().request_GeomToPR_line(startx, starty, endx, endy,projection, aut,proj_va)
                '''
                query_t = API_GeomToPR().request_GeomToPR_line(list_coor, projection, aut, proj_va)
            else:
                ERREUR("La donnée n'est pas au format ligne ou point ")
            # Si le paquet de requete est <150 alors la requete peut intégrer la sous liste
            if step < paquet:
                list_rq.append(query_t)
            # Si la sous liste de requete atteint son maximum (150 ou 130) => le paquet de 150 requetes est stocké dans
            # la liste de requete à envoyer. List_rq est reset et le comptage jusqu'à 150 ou 130 recommence
            if step == paquet:
                step =0
                list_rq.append(query_t)
                list_rq_final.append(list_rq)
                list_rq = []
            # Si le cuseur arrive sur la dernière entitée de la table => le dernier paquet de requetes est stocké dans
            # la liste de requete à envoyer (forcement <150 ou <130).
            if idx+1 == int(long[0]):
                list_rq_final.append(list_rq)
            step += 1

    # Lancement de l'API par paquet de 150 ou 130 max
    list_update = [] # liste finale comportant les réponses des requetes
    for idx,rq in enumerate(list_rq_final):
        TRACE ('Lancement API {}/{}'.format((idx+1),len(list_rq_final)))
        response_pr = API_GeomToPR().start_request(coder,rq)
        for r in response_pr['Resultat']:
            add = API_GeomToPR().API_resultat(r)
            list_update.append(add)
        if calc_polygon is True:
            # Si la donnée est un polygon => Remplacement des fin et debut dans les résultats
            if geom_type== 'Polygon':
                for idx,u in enumerate(list_update):
                    u['PR_DEBUT'] = pr_polygon[idx][0][0]
                    u['CODE_DEBUT']=pr_polygon[idx][0][1]
                    u['AUTOROUTE_DEBUT'] = pr_polygon[idx][0][2]
                    u['PR_FIN'] = pr_polygon[idx][1][0]
                    u['CODE_FIN'] = pr_polygon[idx][1][1]
                    u['AUTOROUTE_FIN'] = pr_polygon[idx][1][2]

        '''
        try :
            for r in response_pr['Resultat']:
                add=API_GeomToPR().API_resultat (r)
                list_update.append(add)
        except:
            TRACE (rq)
            ERREUR('PROBLREME AVEC LA REQUETE CI DESSUS')
        '''
    # Ecriture des résultats des requetes dans la donnée de départ à géocoder
    TRACE("!!!!!!Update de la table!!!!!!!!!!")
    # Test la donnée est dans un jeu de classe d'entité
    # Si oui (except) la variable workspace est amputée du chemin du jeu de classe d'entité
    try:
        edit = arcpy.da.Editor(workspace)
    except:
        TRACE ("**La donnée est dans un jeu de classe d'entité**")
        spl=workspace.split(os.sep)
        wk=[]
        for idx,w in enumerate(spl):
            if idx < 8:
                wk.append(w)
        workspace=os.sep.join(wk)
        TRACE ('\t -workspace reconstruit: {}'.format (workspace))
        edit = arcpy.da.Editor(workspace)

    edit.startEditing(False, False)
    # Si la donnée est sur SQL server (accès sde) => activation opération
    if ".sde" in workspace:
        edit.startOperation()
    with arcpy.da.UpdateCursor(path, fields_add) as cursor:
        for idx,row in enumerate(cursor):
            TRACE("MAJ : {}/{}".format(idx+1,long))
            ##geom = row.geometry()
            for f in fields_add:
                # Si le champ correspond au champ de géocodage => écriture du résultat
                if f not in ("SHAPE@", aut_field):
                    idx_field = [i for i, val in enumerate(fields_add) if val == f]
                    ##TRACE ('{}={}'.format(f,list_update[s][f]))
                    row[idx_field[0]] = list_update[idx][f]
            cursor.updateRow(row)
    # Si la donnée est sur SQL server (accès sde) => désactivation opération
    if ".sde" in workspace:
        edit.stopOperation()
    # Désactivation de l'édition
    edit.stopEditing(True)
    # Récupération temps de traitement
    end = time.time()
    total_time = timedelta(seconds=end - start)
    TRACE("Temps d'execution : {} pour {} entité(s) géocodée(s)".format(total_time, long))
    TRACE ('Termine')

#-------------------------------------------------------------------------------------------------------------------
#**********************************************--VARIABLES MAIN--***************************************************
#-------------------------------------------------------------------------------------------------------------------
if __name__ == '__main__':
    Test = False
    if Test is True:
        DATA         = r'C:\0_COFIROUTE\3_SIG\01_WORK\2022\05_13_22_Zone_exclusion_bruit\RENDU_FINAL\rendu_final_bruit.gdb\zone_exclusion_methode2'
        FIELDS_LIST  = ['SENS', 'PR_DEBUT', 'PR_FIN', 'INSEE', 'COMMUNE', 'SCA',
                            'DEX', 'DRE', 'DISTRICT', 'CENTRE_ENTRETIEN']
        PROJ         = 'AutorouteUniquement'
        FIELD_TARGET = ''
    else:
        DATA         = arcpy.GetParameter(0) # Donnée à géocoder dans le projet
        FIELDS       = arcpy.GetParameterAsText(1)  # Champs à géocoder
        FIELDS_LIST  = FIELDS.split(';') # Champs à géocoder transformé en liste
        PROJ         = arcpy.GetParameterAsText(2)  # Type de projection pour le géocodage
        PROJ_VA      = arcpy.GetParameter(3) # Si coché : projection uniquement sur route VA (booléen facultatif)
        CALC_POLYGON = arcpy.GetParameter(4) # Si coché : calcul début et fin des polygon mais traitement plus long (booléen facultatif)
        FIELD_TARGET = arcpy.GetParameterAsText(5) # Champ cible pour la projection spécifique (facultatif)
        CODER        = arcpy.GetParameterAsText(6) # URL de l'API de géocodage
# Lancement du script d
arcgis_GeomtoPR(DATA,FIELDS_LIST,PROJ,FIELD_TARGET,PROJ_VA,CALC_POLYGON,CODER)
