import geopandas as gpd
import requests
from requests import Request
from owslib.wfs import WebFeatureService

# URL for WFS backend
#urla = "https://wxs.ign.fr/cartovecto/geoportail/wfs?VERSION=2.0.0&TYPENAMES=BDCARTO_BDD_WLD_WGS84G:acces_equipement&COUNT=1000&SRSNAME=EPSG:4326&BBOX=46.83807589,2.05303178,47.53821707,3.03137375&request=GetFeature&outputFormat=json"
#urlb = 'https://wxs-gpu.mongeoportail.ign.fr/externe/39wtxmgtn23okfbbs1al2lz3/wfs'
url= 'https://wxs.ign.fr/parcellaire/geoportail/wfs'
TRACE ('Initialisation url')
# Initialize
wfs = WebFeatureService(url=url)

# Get data from WFS
# -----------------

TRACE ('liste des layer wfs')
# Fetch the last available layer (as an example) --> 'vaestoruutu:vaki2017_5km'
layer = list(wfs.contents)#['wfs_du:zone_urba']
for l in layer :
      if l=='BDPARCELLAIRE-VECTEUR_WLD_BDD_WGS84G:parcelle':
            layer = l
# Specify the parameters for fetching the data
params_test = dict(service='WFS', version="2.0.0", request='GetFeature',
      typeName=l,BBOX='46.83807589,2.05303178,47.53821707,3.03137375', outputFormat='json')

params= dict(service='WFS', version="2.0.0", request='GetFeature',
      typeName=l,COUNT='15000', outputFormat='json')
TRACE ('lancement request')
# Parse the URL with parameters
q = Request('GET', url, params=params).prepare().url

TRACE('recuperation data geopandas')
# Read data from URL
data = gpd.read_file(q)

TRACE('termine')
