# -*- coding: utf-8 -*-
# -------------------------------------------------------------------------------
# Name:        Test Geopandas et requête WFS IGN
# Author:      J Samaniego
# Created:     27/07/2022
'''
Contenu : Ce script permet de télécharger des données depuis un flux wfs IGN
avec un filtre sur plusieurs BBOX. Les requêtes renvoient 1000 entités max et elles
sont concaténées dans une donnée finale une fois qu'il n'y a plus de donnée à requêter
dans les BBOX.
Il est possible de rendre dynamique la création de bbox à partir d'une donnée
de référence mais attention aux géométries dupliquées si plusieurs bbox
s'enchaînent dans les requêtes (ex: donnée commune ou département).
La donnée finale peut être exportée en GeoJson/GPKG temporairement puis intégré sous
SQL server avec arcpy et la connexion sde.
'''
# -------------------------------------------------------------------------------
# ********* IMPORTS *********
import os,sys
import os.path
from pathlib import Path
from subprocess import run

import geopandas as gpd
import pandas as pd
import arcpy

import requests
from requests import Request
from owslib.wfs import WebFeatureService

import time
from datetime import timedelta

start = time.time()

# ********* FONCTIONS *********
def test_con(url_wfs):
    try:
        # Initialize
        wfs = WebFeatureService(url=url_wfs)
    except:
        # Si erreur à la connexion du flux (surcharge du flux / problème infra IGN)
        print('!!Pobleme de connexion au flux !! => restart')
        run("python " + "Geopandas_wfs.py", check=True)
    print('=> Connexion au flux réussie <=')
    return wfs

def change_crs (dataframe,crsREF,crsTARGET):
    geodata=dataframe.set_crs(epsg=crsREF)
    geodata=geodata.to_crs(epsg=crsTARGET)
    return geodata

# ********* VARIABLES PRINCIPALES *********
# URL for WFS
'''
urla = "https://wxs.ign.fr/cartovecto/geoportail/wfs"
urlb = 'https://wxs-gpu.mongeoportail.ign.fr/externe/39wtxmgtn23okfbbs1al2lz3/wfs'
urlc='https://wxs.ign.fr/administratif/geoportail/wfs'
'''
url= 'https://wxs.ign.fr/parcellaire/geoportail/wfs'

# Variables Path
path_com = r'\\vanasnp00001\SIGVA_ADMIN\COFIROUTE\99_TEST\Commune_test.gpkg'
path=r'\\vanasnp00001\SIGVA_ADMIN\COFIROUTE\99_TEST\parcelles_bbox_wfs_test.gpkg'

# ********* TRAITEMENTS *********
# ----Def BBOX
print("Récupération des BBOX de référence")
list_bbox =[]
gdf_com = gpd.read_file(path_com) # Donnée de référence pour définir les BBOX (ex: commune)
change_crs(gdf_com,2154,4326) # Conversion crs lambert93 to WGS84 pour la récupération des x;y
for i in gdf_com.bounds.iterrows():
    extent= i[1]
    minx=extent['minx']
    miny=extent['miny']
    maxx=extent['maxx']
    maxy=extent['maxy']
    tmp = ','.join([str(miny),str(minx),str(maxy),str(maxx)])
    list_bbox.append(tmp)

print('Initialisation url')
wfs=test_con(url)

# ---- Get data from WFS
print ('liste des layer wfs')
# Fetch the last available layer (as an example) --> 'vaestoruutu:vaki2017_5km'
layer = list(wfs.contents)#['wfs_du:zone_urba']
# Loop dans le flux WFS pour lire les différentes données
layer_find= [] # Traque les couches présentes dans le flux
wfs_target='BDPARCELLAIRE-VECTEUR_WLD_BDD_WGS84G:parcelle' # Data à récupérer
for l in layer :
    if l==wfs_target:
        layer = l
        layer_find.append(l)
if len(layer_find)==0:
    print("La donnée n'est pas dans le flux")
    sys.exit()
else:
    print("Couche <{}> trouvée dans le flux".format(wfs_target))


# ---- Loop dans les bbox : 1 BBOX = lancement d'une ou plusieurs requêtes tant que la réponse de requête est >1000
step=1 # Permet de suivre le nombre total des requêtes envoyées
list_data=[] # Stock la liste des geodataframes renvoyées par les requêtes
for step_b,b in enumerate(list_bbox):
      len_data = 1000
      print('!!!!! BBOX request {}/{} !!!!!!'.format(step_b,len(list_bbox)))
      # Boucle dans de requête par BBOX tant que la réponse est >1000 entités (1000 = entités max renvoyées par l'IGN)
      u = 0 # Variable de départ pour le paramètre startIndex des requêtes à envoyer
      while len_data==1000:
            # Paramètres de la requête GET sur l'url
            # Le paramètre startIndex permet de gérer l'avancement des requêtes dans une BBOX par 1000 max
            params= dict(service='WFS', version="2.0.0", request='GetFeature',
                  typeName=layer,BBOX=b,
                         startIndex=str(u), outputFormat='json')
            try:
                # Lancement de la requête avec les paramètres
                response = Request('GET', url, params=params).prepare().url

                #print('recuperation data geopandas')
                # Lecture de la réponse de la requête avecgeopandas en geodataframe
                data = gpd.read_file(response)
                # Ajout de la réponse dans une liste de geodataframe lisible par pandas et geopandas
                list_data.append(data)
                idx=data.count()['geometry'] # compte le nombre d'entités renvoyées par la requête
                if idx==0:
                      print('pas de geometrie dans la BBOX')
                len_data=idx # Si idx est <1000 => le script passe à la BBOX suivante ou fin de la boucle si dernière BBOX
                u+=idx # Incrémentation de l'index pour le paramètre startIndex
                print("\t - request {} ({}) => next index bbox {}".format(step, idx,u))
                step+=1
            except:
                # Relance de la requête si une erreur est renvoyée (surcharge flux / problème IGN)
                len_data=1000
                print("!!!!!PROBLEME REQUETE {} => RELANCE!!!!!!".format(step))

# Concaténation de la liste des résultats (liste_data) : plusieurs geodataframe vers une seule geodataframe
result = gpd.GeoDataFrame(pd.concat(list_data, ignore_index=True))

# Suppression des doublons à cause des morceaux de BBOX superposées
print('Suppression des doublons')
data_final = result[~result.duplicated()]

# ----Écriture de la donnée finale
print('Ecriture data finale')
change_crs (data_final,4326,2154)
data_final.to_file(path,driver="GPKG")
#result.plot() # Vérifier le résultat en carte

# Résultat traitement geopandas vers feature class pour intégrer la donnée sur SQL server avec arcpy
print ('Intégration dans SQL server via connexion sde')
path_sde= r'C:\0_COFIROUTE\1_Outils\Arcgis\SDE\Connexion à ArcGISAdm@SP2W101-SIG_DEV - Copier.sde'
arcpy.env.workspace = path_sde
arcpy.env.overwriteOutput = True
jeu_class=r'\SDE_BIM_DEV.ARCGISADM.TEST_Julien'
path_final=path_sde+jeu_class
#arcpy.conversion.JSONToFeatures(path, path_final+r'\SDE_BIM_DEV.ARCGISADM.'+'parcelles_IGN_test', "POLYGON")
basename = Path(path).stem
name_gpkg=r'\main.{}'.format(basename)
prefix_name=r'\SDE_BIM_DEV.ARCGISADM.'
name_data='parcelles_IGN_test'
arcpy.management.CopyFeatures(path+name_gpkg,path_final+prefix_name+name_data)

# Suppression du GeoJson/GPKG (fichier temporaire avant intégration en base)
print ('Suppression => {}'.format(path))
if arcpy.Exists(path):
    arcpy.management.Delete(path)

# Récupération temps de traitement
end = time.time()
total_time = timedelta(seconds=end - start)
print("Temps d'execution : {}".format(total_time))

print('Termine')
