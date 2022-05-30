# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:        Export parcelle et fichiers ONF
# Author:      J Samaniego
# Created:     25/05/2022
# Contenu :
# À partir des parcelles ONF sélectionnées dans Arcgispro, cet outil permet
# d'exporter les fichiers qui sont associés à celle(s)-ci. Les fichiers sont
# stockés dans une table (champ blob) qui est reliée aux parcelles.
#-------------------------------------------------------------------------------
import os
import arcpy
from arcpy import da

def TRACE(txt):
    print(txt)
    arcpy.AddMessage(txt)

def ALERTE(txt):
    print(txt)
    arcpy.AddWarning(txt)

def ERREUR(txt):
    print ("ERREUR : " + txt)
    arcpy.AddError(txt)
    sys.exit ()

#***************************--VARIABLES ARCGIS--******************************************
inLayer      = arcpy.GetParameter(0) # Couche des parcelles ONF dans le projet
inTable      = arcpy.GetParameter(1) # Table des documents ONF dans le projet
fileLocation = arcpy.GetParameterAsText(2) # Dossier où les exports seront stockés
name_shp     = arcpy.GetParameterAsText(3) # Nom de la donnée shapefile des parcelles

#***************************--TRAITEMENTS--***********************************************
TRACE ("!! Dossier Export : {}".format(fileLocation))
# Liste les id à récupérer dans la table des pièces jointes grâce à la selection des parcelles dans arcgis
list_id = []
list_id_parcelle =[]
with da.SearchCursor(inLayer,['GlobalID','IDSITE'])as cursor:
    for i in cursor:
        id=i[0]
        id_parcelle=i[1]
        list_id.append(id)
        list_id_parcelle.append([id,id_parcelle])

TRACE ("ID des parcelles sélectionnées : "+str(list_id))
TRACE (list_id_parcelle)
# Récupère les fichiers des parcelles sélectionnées
u=0
wc ="REL_GLOBALID in ({})".format(str(list_id)[1:-1])
with da.SearchCursor(inTable, ['DATA', 'ATT_NAME', 'ATTACHMENTID','REL_GLOBALID'],where_clause=wc)as cursor:
    for item in cursor:
        u+=1
        attachment = item[0]
        filenum='Unamed'+'_'
        for elem in list_id_parcelle:
            if str(elem[0])==str(item[3]):
                filenum=str(elem[1])+'_'
        filename = filenum + str(item[1])
        TRACE ("Export : "+filename)
        open(fileLocation + os.sep + filename, 'wb').write(attachment.tobytes())
        del item
        del filenum
        del filename
        del attachment

# Export des parcelles en shapefile
TRACE ("Export des parcelles en shapefile")
arcpy.conversion.FeatureClassToFeatureClass(inLayer, fileLocation, name_shp+".shp")

TRACE ("Fichiers exportés : "+str(u))
TRACE ("Terminé")