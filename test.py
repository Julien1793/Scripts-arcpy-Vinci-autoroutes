import sys,os
import requests
import json
import geojson
url = "https://apicarto.ign.fr/api/gpu/zone-urba"
path= r'C:\0_COFIROUTE\3_SIG\Test\test.geojson'
params ={"type": "Point","coordinates":[-1.691634,48.104237]}
headers = {'content-type': 'application/json'}
jsonData = json.dumps(params)
response =requests.get(url,data=params,headers=headers)
print (response.json())
with open(path, 'w') as f:
    json.dump(response.json(), f)
print ("termine")


#https://apicarto.ign.fr/api/doc/gpu#/Documents%20d'urbanisme%20(PLU%2C%20POS%2C%20CC%2C%20PSMV)/get_gpu_zone_urba
