import requests
import sys,os
from urllib.request import urlopen
'''
url = 'https://wxs.ign.fr/vxlh30ais2rjyt2nb4ivupn2/telechargement/prepackage/PARCELLAIRE-EXPRESS_PACK-FXX_et_DOM_2022-04-01$PARCELLAIRE_EXPRESS_1-0__SHP_LAMB93_D001_2022-04-01/file/PARCELLAIRE_EXPRESS_1-0__SHP_LAMB93_D001_2022-04-01.7z'
TRACE ('requete')
r = requests.get(url, allow_redirects=True)
path=r'C:\0_COFIROUTE\3_SIG\Test\DL_IGN\test.7z'
TRACE ('ecriture')
open(path, 'wb').write(r.content)
'''

link = "https://geoservices.ign.fr/parcellaire-express-pci#telechargementdep"
f = urlopen(link)
myfile = f.read()
TRACE(myfile)

TRACE ('termine')