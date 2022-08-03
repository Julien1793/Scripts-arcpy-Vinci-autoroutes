# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:        Request géocodage PR+ABS (Arcgis Pro)
# Author:      J Samaniego
# Created:     05/05/2022
# Contenu :
# Le script pemret de géocoder en PR+ABS une donnée sur le référentiel autoroutier VA.
# Le script fait appel à un API développé par Naomis et hébergé sur l'Arcgis sever VA.
# L'API nécéssite un format JSON en entrée et peut géocoder au maximum 130 entitées
# en une requête.
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

def verif_geom(geom):
    if geom in ('Point','Polyline','Polygon'):
        TRACE ('Geometry ok => {}'.format(geom))
    else:
        ERREUR("La donnée n'est pas au format ligne ou point ")

def verif_proj_type (proj,field,spec):
    if proj== 'AutorouteSpecifique' and field == '' and spec == '':
        ERREUR("Pour l'option AutorouteSpecifique il faut indiquer un champ d'autoroute "
               "ou renseigner manuellement le nom de l'autoroute")

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

        elif projection == 'AutorouteUniquement':
            query = {"GeometrieEsriJson": {"x": x, "y": y, "spatialReference": {"wkid": 2154}},
                       "OptionProjection": {"codeSegment": field, "LocalisationPointProjete": projection,
                                            "EstUniquementSurReseauVinciAutoroute": va},
                       "ThematiquesResultat": ["AdministratifPointInitial", "AdministratifPointProjete", "APS",
                                               "PointLePlusProche"]}
        elif projection == 'PlusProche':
            query = {"GeometrieEsriJson": {"x": x, "y": y, "spatialReference": {"wkid": 2154}},
                       "OptionProjection": {"codeSegment": field,
                                            "EstUniquementSurReseauVinciAutoroute": va},
                       "ThematiquesResultat": ["AdministratifPointInitial", "AdministratifPointProjete", "APS",
                                               "PointLePlusProche"]}

        return query

    def request_GeomToPR_line(self,type,coors,projection,field,va_unique):
        if va_unique ==True:
            va='true'
        else:
            va='false'
        if type== 'Polyline':
            type_rq="paths"
        else:
            type_rq="rings"

        # Si il y a trop de coordonnées dans la ligne ou le polygon => une valeur null est envoyée au géocodage
        # car il est possible de géocoder une entité avec trop de sommets
        if len(coors)>1360:
            query={}
        elif projection == 'AutorouteSpecifique':
            query = {"GeometrieEsriJson": {type_rq: [coors],"spatialReference": {"wkid": 2154}},
                        "OptionProjection": {"codeSegment": field+'[_]%',"LocalisationPointProjete": projection,
                                             "EstUniquementSurReseauVinciAutoroute": va},
                       "ThematiquesResultat": ["AdministratifPointInitial", "AdministratifPointProjete", "APS",
                                               "PointLePlusProche"]}
        elif projection == 'AutorouteUniquement':
            query = {"GeometrieEsriJson": {type_rq: [coors],"spatialReference": {"wkid": 2154}},
                        "OptionProjection": {"codeSegment": field,"LocalisationPointProjete": projection,
                                             "EstUniquementSurReseauVinciAutoroute": va},
                       "ThematiquesResultat": ["AdministratifPointInitial", "AdministratifPointProjete", "APS",
                                               "PointLePlusProche"]}
        elif projection == 'PlusProche':
            query = {"GeometrieEsriJson": {type_rq: [coors],"spatialReference": {"wkid": 2154}},
                        "OptionProjection": {"codeSegment": field,
                                             "EstUniquementSurReseauVinciAutoroute": va},
                       "ThematiquesResultat": ["AdministratifPointInitial", "AdministratifPointProjete", "APS",
                                               "PointLePlusProche"]}

        return query

    def start_request (self,coder,parameter):
        jsonData = json.dumps(parameter)
        js = '&f=json'
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
        try:
            route       = k['Autoroute']
            route_debut = e['Autoroute']
            route_fin   = j['Autoroute']
        except:
            route       = None
            route_debut = None
            route_fin   = None
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
        if type == 'Polygon':
            h=g['AdministratifPointInitial']
            insee = h['commune']['code']
            commune = h['commune']['nom']
        else:
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
        '''
        # Transformation des valeurs texte vide en None
        for key, value in dic_result.items():
            # do something with value
            if value == '':
                dic_result[key] = None
        '''
        return dic_result

#-------------------------------------- FONCTION PRINCIPALE du Script(Traitement) ------------------------------------
def arcgis_GeomtoPR(path,paquet,map_fields,fields_add_input,projection,aut_field,proj_va,spec_aut,coder):
    # Vérification INPUT
    TRACE("************PARAMETERS************")
    desc = arcpy.Describe(path)
    geom_type = desc.shapeType
    verif_geom(geom_type)
    verif_proj_type(projection, aut_field, spec_aut)
    TRACE('Nombre de lignes à géocoder en même temp: {}'.format(paquet))
    TRACE('Géocodage sur VA uniquement: {}'.format(proj_va))
    TRACE("Champs à géocoder : {}".format(fields_add_input))
    TRACE("Type de géocodage : {}".format(projection))
    workspace = desc.path
    TRACE('Workspace de la donnée : {}'.format(workspace))
    TRACE("**********************************")
    # Création du nombre max de requêtes à envoyer en même temps (130)
    fields_add=fields_add_input
    paquet=paquet
    vueUpdate= 'vueUpdate'
    arcpy.management.MakeFeatureLayer(path, vueUpdate)

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
        if projection in ('AutorouteSpecifique') and aut_field != '':
            list_tmp.append(aut_field)
    except:
        ERREUR ("Type projection : {} => le champ autoroute doit être indiqué".format(projection))

    ##pr_polygon = []
    long_str= str(long)
    long_int= int(long_str)
    arcpy.SetProgressor("step","Récupération infos",0,long_int, 1)
    t=arcpy.TestSchemaLock(path)
    if t is False:
        ERREUR ('data lock')
    view = 'view'

    arcpy.management.MakeFeatureLayer(path,view)
    with arcpy.da.SearchCursor(view, list_tmp) as cursor:
        for idx,row in enumerate(cursor):
            #TRACE('Récup : {}/{}'.format(str(idx+1),str(long)))
            arcpy.SetProgressorLabel('Récup : {}/{}'.format(str(idx+1),long))
            ##geom = row.geometry()
            # Si un champ est spécifié pour l'autoroute => récupération du champ pour le géocodage
            if projection== 'AutorouteSpecifique' and aut_field != '' and spec_aut == '':
                aut=row[1]
            # Si un nom d'autoroute est renseigné manuellement => récupération du nom
            elif projection== 'AutorouteSpecifique' and aut_field == '' and spec_aut != '':
                aut=spec_aut
            # Si un champ et un nom sont renseignés en même temps => l'outil est stopé
            elif projection== 'AutorouteSpecifique' and aut_field != '' and spec_aut != '':
                ERREUR("Il est impossible de spécifier un champ et"
                       " un nom d'autoroute en même temps")
            else:
                aut=''
            if geom_type == 'Point':
                pnt = row[0].getPart()
                x_coor = pnt.X
                y_coor = pnt.Y
                query_t = API_GeomToPR().request_GeomToPR_point (x_coor,y_coor,projection,aut,proj_va)
            elif geom_type == 'Polygon':
                '''
                pnt = row[0].centroid
                x_coor = pnt.X
                y_coor = pnt.Y
                '''
                pnt = row[0].getPart()
                list_coor=[]
                for idx2,coor in enumerate(pnt):
                    if idx2 > 0:
                        ERREUR("MULIPARTIE DANS LA DONNÉE => "
                               "problème avec l'entité ligne {} dans la table (ou la selection)".format(idx))
                    for i in coor:
                        list_coor.append([i.X,i.Y])

                query_t = API_GeomToPR().request_GeomToPR_line (geom_type,list_coor,projection,aut,proj_va)
                '''
                if calc_polygon is True:
                    pnts = row[0].getPart()
                    list_tmp=[]
                    for idx2,coor in enumerate(pnts):
                        if idx2 > 0:
                            ERREUR('MULIPARTIE DANS LA DONNÉE')
                        for i in coor:
                            TRACE (i)
                            query_tmp = API_GeomToPR().request_GeomToPR_point (i.X,i.Y,projection,aut,proj_va)
                            response_tmp = API_GeomToPR().start_request(coder, [query_tmp])
                            list_tmp.append(API_GeomToPR().API_resultat(response_tmp['Resultat'][0]))
                            list_prd_tmp=[]
                            list_prf_tmp = []
                            for i in list_tmp:
                                list_prd_tmp.append([i['PR_DEBUT'],i['CODE_DEBUT'],i['AUTOROUTE_DEBUT']])
                                list_prf_tmp.append([i['PR_FIN'],i['CODE_FIN'],i['AUTOROUTE_FIN']])
                    pr_polygon.append([min(list_prd_tmp),max(list_prf_tmp)])
                '''
            elif geom_type =='Polyline':
                pnt = row[0].getPart()
                list_coor=[]
                for idx2,coor in enumerate(pnt):
                    if idx2 > 0:
                        ERREUR("MULIPARTIE DANS LA DONNÉE => "
                               "problème avec l'entité ligne {} dans la table (ou la selection)".format(idx))
                    for i in coor:
                        list_coor.append([i.X,i.Y])
                query_t = API_GeomToPR().request_GeomToPR_line(geom_type,list_coor,projection,aut,proj_va)

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
            if idx+1 == int(long[0]) and len(list_rq)>0:
                list_rq_final.append(list_rq)
            step += 1
            arcpy.SetProgressorPosition()
    del row
    del idx
    del cursor
    arcpy.ResetProgressor()

    # Lancement de l'API par paquet de 130 max
    arcpy.SetProgressor("step", "Lancement API",0, len(list_rq_final), 1)
    list_update = [] # liste finale comportant les réponses des requetes
    for idx,rq in enumerate(list_rq_final):
        #TRACE ('Lancement API {}/{}'.format((idx+1),len(list_rq_final)))
        arcpy.SetProgressorLabel('Lancement API {}/{}'.format((idx+1),len(list_rq_final)))
        response_pr = API_GeomToPR().start_request(coder,rq)
        arcpy.SetProgressorPosition()
        for r in response_pr['Resultat']:
            # Essaye si le résultat n'est pas vide
            try:
                add_res = API_GeomToPR().API_resultat(r)
            # Si le résultat est vide (problème avec l'entité à géocoder) => le dictionnaire est forcé en None
            except:
                add_res={'PR':None,'PR_CENTRE':None,'PR_DEBUT': None, 'PR_FIN':None,
                      'DEPORT':None,'DEPORT_CENTRE': None,
                      'DEPORT_DEBUT': None,'DEPORT_FIN': None, 'SENS': None, 'CODE': None,
                      'CODE_DEBUT': None, 'CODE_FIN': None,
                      'AUTOROUTE':None,'AUTOROUTE_DEBUT':None,'AUTOROUTE_FIN':None,'SCA': None,
                      'SCA_name': None, 'DEX': None, 'DEX_name': None,'DRE': None, 'DRE_name': None,
                      'DISTRICT': None, 'DISTRICT_name': None,'CENTRE_ENTRETIEN': None,'CE_name': None,
                      'INSEE': None, 'COMMUNE': None}
            list_update.append(add_res)


        '''
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
    arcpy.ResetProgressor()
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
    #arcpy.env.overwriteOutput = True

    # Si la donnée est sur SQL server (accès sde) => activation opération
    if ".sde" in workspace :
        edit.startEditing(False, False)
        edit.startOperation()
        TRACE("!!!!EDIT with operation!!!!")
    elif ".sde" not in workspace and int(str(long)) <= 80000:
        TRACE ("!!!!EDIT without operation!!!!")
        edit.startEditing(False, False)
    elif ".sde" not in workspace and int(str(long)) > 80000:
        TRACE ("!!!!NO EDIT!!!!")
    arcpy.SetProgressor("step", "Update de la table", 0,long_int, 1)

    result=[]
    list_fail=[]
    with arcpy.da.UpdateCursor(path, fields_add) as Ucursor:
        t = arcpy.TestSchemaLock(path)
        TRACE("\t - La donnée peut acquérir un verrouillage : {}".format(t))
        for uidx,urow in enumerate(Ucursor):
            #TRACE("MAJ : {}/{}".format(uidx+1,long))
            arcpy.SetProgressorLabel("Finalisation => MAJ : {}/{}".format(uidx+1,long_int))
            for f in map_fields:
                # Si le champ correspond au champ de géocodage => écriture du résultat
                if f[0] not in ("SHAPE@", aut_field):
                    idx_field = [i for i, val in enumerate(fields_add) if val == f[0]]
                    # Récupération de la postion du résultat dans list_update et correspondance du champ du dictionnaire
                    attr=list_update[uidx][f[1]]
                    # Si le résultat a écrire dans la donnée n'est pas null => écriture du résultat
                    # Sinon ajout du None dans une liste
                    if attr is not None:
                        urow[idx_field[0]] = attr
                    else:
                        result.append(attr)
            # Si le résultat de tous les champs est None => ajout dans de la ligne dans la liste des fails
            if result.count(None)==len(fields_add):
                list_fail.append(uidx + 1)
            result=[]
            # Application de l'update dans la table
            Ucursor.updateRow(urow)

            arcpy.SetProgressorPosition()
    del urow
    del uidx
    del Ucursor

    if ".sde" in workspace:
        edit.stopOperation()
        edit.stopEditing(True)
    elif ".sde" not in workspace and int(str(long)) <= 80000:
        edit.stopEditing(True)

    if len(list_fail)>0:
        ALERTE("Des entités n'ont pas pu être géocodées correctement :"
               "\n - entité avec trop de points dans la géométrie (résultat du géocodage vide)"
               "\n - ou la géométrie est trop loin du référentiel (résultat du géocodage vide)"
               "\n Numéros des lignes dans la sélection avec un géocodage impossible : {}"
               "\n => TOTAL des entités non géocodées = {}".format(list_fail,len(list_fail)))

    # Récupération temps de traitement
    end = time.time()
    total_time = timedelta(seconds=end - start)
    TRACE("Temps d'execution : {} pour {} entité(s) géocodée(s)".format(total_time, long))
    TRACE('Termine')

#-------------------------------------------------------------------------------------------------------------------
#**********************************************--VARIABLES MAIN--***************************************************
#-------------------------------------------------------------------------------------------------------------------
if __name__ == '__main__':
    Test = False
    if Test is True:
        DATA = r'C:\0_COFIROUTE\3_SIG\01_WORK\2022\22_05_03_Photo_COFIROUTE\Work.gdb\Photo_2020'
        FIELDS_LIST = ['AUTOROUTE','PR']

    else:
        DATA         = arcpy.GetParameter(0) # Donnée à géocoder dans le projet
        PAQUET       = arcpy.GetParameter(1) # Choix du nombre d'entité à géocoder en même temps
        FIELDS       = arcpy.GetParameterAsText(2)  # Champs à géocoder
        FIELDS_LIST_tmp  = FIELDS.split(';') # Champs à géocoder transformé en liste
        MAP_FIELDS=[] # Liste de la correspondance des champs (champ dans la table => attribut du géocodage)
        # Récupération de la liste de correspondance des champs
        for f in FIELDS_LIST_tmp:
            spt = f.split(' ')
            MAP_FIELDS.append(spt)
        TRACE(MAP_FIELDS)
        FIELDS_LIST =[] # Liste des champs à géocoder dans la table (sans correspondance)
        # Récupération de la liste des champs à géocoder dans la table
        for f in MAP_FIELDS:
            FIELDS_LIST.append(f[0])
        TRACE (FIELDS_LIST)
        PROJ         = arcpy.GetParameterAsText(3)  # Type de projection pour le géocodage
        PROJ_VA      = arcpy.GetParameter(4) # Si coché : projection uniquement sur route VA (booléen facultatif)
        FIELD_TARGET = arcpy.GetParameterAsText(5) # Champ cible pour la projection spécifique (facultatif)
        SPEC_AUT     = arcpy.GetParameterAsText(6) # Nom de l'autoroute sur laquelle géocoder (facultatif)
        CODER        = arcpy.GetParameterAsText(7) # URL de l'API de géocodage
    # Lancement du script
    arcgis_GeomtoPR(DATA,PAQUET,MAP_FIELDS,FIELDS_LIST,PROJ,FIELD_TARGET,PROJ_VA,SPEC_AUT,CODER)
