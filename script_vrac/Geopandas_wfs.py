# -*- coding: utf-8 -*-
# -------------------------------------------------------------------------------
# Name:        Name script
# Author:      J Samaniego
# Created:     27/07/2022
# Contenu : Ce script permet de télécharger des données depuis un flux wfs IGN en
# y intégrant une BBOX fixe. Les requêtes renvoient 1000 entités max et elles sont
# concaténées dans une donnée finale une fois qu'il n'y a plus de donnée à requêter
# dans le BBOX.
# Il serait possible de rendre dynamique la création de bbox à partir d'une donnée
# de référence mais attention aux géométries dupliquées si plusieurs bbox
# s'enchaînent dans les requêtes (ex: donnée commune ou département).
# -------------------------------------------------------------------------------

import os,sys

import geopandas as gpd
import pandas as pd
import requests
from requests import Request
from owslib.wfs import WebFeatureService

# URL for WFS backend
'''
urla = "https://wxs.ign.fr/cartovecto/geoportail/wfs?VERSION=2.0.0&TYPENAMES=BDCARTO_BDD_WLD_WGS84G:acces_equipement&COUNT=1000&SRSNAME=EPSG:4326&BBOX=46.83807589,2.05303178,47.53821707,3.03137375&request=GetFeature&outputFormat=json"
urlb = 'https://wxs-gpu.mongeoportail.ign.fr/externe/39wtxmgtn23okfbbs1al2lz3/wfs'
urlc='https://wxs.ign.fr/administratif/geoportail/wfs'
'''
url= 'https://wxs.ign.fr/parcellaire/geoportail/wfs'
path= r'C:\0_COFIROUTE\3_SIG\Test\parcelles_bbox_wfs_test.geojson'
print('Initialisation url')
# Initialize
wfs = WebFeatureService(url=url)

# Get data from WFS
# -----------------

print ('liste des layer wfs')
# Fetch the last available layer (as an example) --> 'vaestoruutu:vaki2017_5km'
layer = list(wfs.contents)#['wfs_du:zone_urba']
len_data=1000

for l in layer :
      if l=='BDPARCELLAIRE-VECTEUR_WLD_BDD_WGS84G:parcelle':
            layer = l

u=0
step=0

# Loop request on specific bbox each 1000 feature (max default for wfs ign)
list_data=[]
while len_data==1000:
      step+=1
      # Specify the parameters for fetching the data
      params= dict(service='WFS', version="2.0.0", request='GetFeature',
            typeName=layer,BBOX='48.710733173187116,3.0383824899604126,48.761793729066646,3.139243665925044',
                   startIndex=str(u), outputFormat='json')
      print('lancement request')

      # Parse the URL with parameters
      q = Request('GET', url, params=params).prepare().url

      print('recuperation data geopandas')
      # Read data from URL
      data = gpd.read_file(q)
      list_data.append(data)
      idx=len(data['id'].value_counts())
      len_data=idx
      u+=idx
      print("next index = {}".format(u))
      print("request {} => {}".format(step, idx))
      frames = list_data

result = gpd.GeoDataFrame(pd.concat(frames, ignore_index=True))
result.to_file(path, driver="GeoJSON")
#result.plot() # Vérifier le résultat en carte
print('Termine')
