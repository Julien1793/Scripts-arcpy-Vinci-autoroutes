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
La donnée finale pourrait être exportées en GeoJson puis intégré sous SQL server
avec arcpy et la connexion sde.
'''
# -------------------------------------------------------------------------------

import os,sys
import os.path

import geopandas as gpd
import pandas as pd
import arcpy

import requests
from requests import Request
from owslib.wfs import WebFeatureService

import time
from datetime import timedelta

start = time.time()

# URL for WFS backend
'''
urla = "https://wxs.ign.fr/cartovecto/geoportail/wfs?VERSION=2.0.0&TYPENAMES=BDCARTO_BDD_WLD_WGS84G:acces_equipement&COUNT=1000&SRSNAME=EPSG:4326&BBOX=46.83807589,2.05303178,47.53821707,3.03137375&request=GetFeature&outputFormat=json"
urlb = 'https://wxs-gpu.mongeoportail.ign.fr/externe/39wtxmgtn23okfbbs1al2lz3/wfs'
urlc='https://wxs.ign.fr/administratif/geoportail/wfs'
'''
url= 'https://wxs.ign.fr/parcellaire/geoportail/wfs'
path_com = r'C:\0_COFIROUTE\3_SIG\Test\commune_test.geojson'
#path= r'C:\0_COFIROUTE\3_SIG\Test\parcelles_bbox_wfs_test.shp'
path=r'C:\0_COFIROUTE\3_SIG\Test\parcelles_bbox_wfs_test.gpkg'
print('Initialisation url')

# Def BBOX
list_bbox =[]
gdf_com = gpd.read_file(path_com, crs="EPSG:4326") # Donnée de référence pour définir les BBOX (ex: commune)
for i in gdf_com.bounds.iterrows():
    extent= i[1]
    minx=extent['minx']
    miny=extent['miny']
    maxx=extent['maxx']
    maxy=extent['maxy']
    tmp = ','.join([str(miny),str(minx),str(maxy),str(maxx)])
    list_bbox.append(tmp)


# Initialize
wfs = WebFeatureService(url=url)

# Get data from WFS
# -----------------

print ('liste des layer wfs')
# Fetch the last available layer (as an example) --> 'vaestoruutu:vaki2017_5km'
layer = list(wfs.contents)#['wfs_du:zone_urba']

# Loop dans le flux WFS pour lire les différentes données
for l in layer :
    if l=='BDPARCELLAIRE-VECTEUR_WLD_BDD_WGS84G:parcelle':
        layer = l
    else:
        print("La donnée n'est pas dans le flux")
        sys.exit()

step_b=0
step=0
list_data=[]
# Loop dans les bbox de la donnée de référence : 1 BBOX = lancement d'une ou plusieurs requêtes si réponse requête >1000
for b in list_bbox:
      step_b+=1
      len_data = 1000
      print('!!!!! BBOX request {}/{} !!!!!!'.format(step_b,len(list_bbox)))
      # Boucle dans de requête par BBOX tant que la réponse est >1000 entités (1000 = entités max renvoyées par l'IGN)
      u = 0 # Variable de départ pour le paramètre startIndex des requêtes à envoyer
      while len_data==1000:
            step+=1
            # Paramètres de la requête GET sur l'url
            # Le paramètre startIndex permet de gérer l'avancement des requêtes dans une BBOX par 1000 max
            params= dict(service='WFS', version="2.0.0", request='GetFeature',
                  typeName=layer,BBOX=b,
                         startIndex=str(u), outputFormat='json')
            #print('lancement request')

            # Lancement de la requête avec les paramètres
            q = Request('GET', url, params=params).prepare().url

            #print('recuperation data geopandas')
            # Lecture de la réponse de la requête avec geopandas
            data = gpd.read_file(q)
            list_data.append(data)
            #print(data.count())
            #idx=len(data['id'].value_counts())
            idx=data.count()['geometry'] # compte le nombre d'entités renvoyées par la requête
            if idx==0:
                  print('pas de geometrie dans la BBOX')
            len_data=idx # Si idx est <1000 => le script passe à la BBOX suivante ou fin de la boucle si dernière BBOX
            u+=idx # Incrémentation de la de l'index pour le paramètre startIndex
            print("\t - request {} => {}".format(step, idx))
            print("\t - next index = {}".format(u))
            frames = list_data

      result = gpd.GeoDataFrame(pd.concat(frames, ignore_index=True))

# Suppression des doublons à cause des morceaux de BBOX superposées
print('suppression des doublons')
list_id=[]
list_del=[] # Track les id des parcelles supprimées
for index, row in result.iterrows():
    id=row['id'] # Champ clés unique de la donnée des parcelles
    # Si l'id n'a pas été encore trouvé il est ajouté dans une liste unique
    if id not in list_id:
        list_id.append(id)
    # Si l'id est déjà dans la liste unique alors c'est un doublon et la parcelle est supprimées
    else:
        list_del.append(id)
        result.drop(index, inplace=True)

# Écriture de la donnée finale
print('Ecriture data finale')
#result.to_file(path, driver="ESRI Shapefile")GPKG
result.to_file(path, driver="GPKG")
#result.plot() # Vérifier le résultat en carte
# Possibilité de faire un json or geojson to feature class pour intégrer la donnée sur SQL server avec arcpy
print ('Intégration dans SQL server via connexion sde')
path_sde= 'mettre chemin sde'
jeu_class=r'\SDE_BIM_DEV.ARCGISADM.TEST_Julien'
path_final=path_sde+jeu_class
#arcpy.conversion.JSONToFeatures(path, path_final+r'\SDE_BIM_DEV.ARCGISADM.'+'parcelles_IGN_test', "POLYGON")
basename = os.path.basename(path).replace('.gpkg','')
name_gpkg=r'\main.{}'.format(basename)
arcpy.management.CopyFeatures(path+name_gpkg,path_final+r'\SDE_BIM_DEV.ARCGISADM.'+'parcelles_IGN_test')

# Suppression du GeoJson (fichier temporaire avant intégration en base)
#path_del=path.replace('.shp','.dbf')
print ('Suppression => {}'.format(path))
if arcpy.Exists(path):
    arcpy.management.Delete(path)

# Récupération temps de traitement
end = time.time()
total_time = timedelta(seconds=end - start)
print("Temps d'execution : {}".format(total_time))

print('Termine')
