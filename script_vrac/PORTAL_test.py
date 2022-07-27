# -*- coding: utf-8 -*-
# -------------------------------------------------------------------------------
# Name:        Name script
# Author:      J Samaniego
# Created:     27/07/2022
# Contenu : Tests gestion des services/flux sur arcgis server VA
# -------------------------------------------------------------------------------

from arcgis.gis import GIS
import arcgis.gis.admin

gis = GIS("url portail arcgis VA", "loggin", "mdp")

gis_servers = gis.admin.servers.list()
# Print les serveurs du portail
for server in gis_servers:
    for service in server.services.list():
        print(service)

server1 = gis_servers[0] # Premier serveur
flds = server1.services.folders # Dossier où sont stockés les services
hosted_services = server1.services.list(folder='Foncier') # Dossier Foncier
for i in hosted_services: # Loop dans le dossier Foncier pour lire les services
    serv_prop =i.properties # Récupération des propriétés de chaque service

    status = i.status # Récupération de l'état du service en run ou à l'arrêt
    # Ex: Output status en run = {'configuredState': 'STARTED', 'realTimeState': 'STARTED'}
    # ou status stoppé = {'configuredState': 'STOPPED', 'realTimeState': 'STOPPED'}
    # Possibilité de stopper ou démarrer le service => i.stop() ou i.start()

    # Possibilité de récupérer les paramètres du service (ex: nom du service)
    print(serv_prop['serviceName'])  # ex: print le nom de chaque service du dossier Foncier

print ('Terminé')
