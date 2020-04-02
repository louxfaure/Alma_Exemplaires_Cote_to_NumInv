#!/usr/bin/python3
# -*- coding: utf-8 -*-
#Modules externes
import os
import re
import logging
import csv
import xml.etree.ElementTree as ET

#Modules maison 
from Alma_Apis_Interface import Alma_Apis_Records
from logs import logs

SERVICE = "Cote_To_NumInv"

LOGS_LEVEL = 'INFO'
LOGS_DIR = os.getenv('LOGS_PATH')

REGION = 'EU'
API_KEY = os.getenv('PROD_IEP_BIB_API')
SET_ID = '1125272040004675'

OUT_FILE = '/media/sf_Partage_LouxBox/Cote_To_NumInv.csv'

#On initialise le logger
logs.init_logs(LOGS_DIR,SERVICE,LOGS_LEVEL)
log_module = logging.getLogger(SERVICE)
log_module.info("Début du traitement")
report = open(OUT_FILE, "w")
report.write("Code-barres\tStatut de la mise à jour\tNuméro d'inventaire\n")

alma_api = Alma_Apis_Records.AlmaRecords(apikey=API_KEY, region=REGION, service=SERVICE)
items_link = alma_api.get_set_members_list(SET_ID)
for links in items_link :
    log_module.debug(links)
    status,response = alma_api.get_item_with_url(links)
    if status == 'Error':
        log_module.error("{} :: Echec :: {}".format(links,response))
        report.write("{}\tErreur Retrouve Exemplaire\t{}\n".format(links,response))
        continue
    # Change location and remove holdinds infos
    item = ET.fromstring(response)
    # log_module.debug(item)
    barcode = item.find(".//item_data/barcode").text
    num_inv = item.find(".//item_data/inventory_number").text
    log_module.debug(num_inv)
    if num_inv is None :
        mms_id = item.find(".//bib_data/mms_id").text
        holding_id = item.find(".//holding_data/holding_id").text
        item_id = item.find(".//item_data/pid").text
        #Si j'ai une cote alternative je la privilégie
        call_number = item.find(".//holding_data/call_number").text if item.find(".//item_data/alternative_call_number").text is None else item.find(".//item_data/alternative_call_number").text
        item.find(".//item_data/inventory_number").text = call_number
        log_module.debug(call_number)
        set_status, set_response = alma_api.set_item(mms_id, holding_id,item_id,ET.tostring(item))
        log_module.debug(set_response)
        if set_status == 'Error':
            log_module.error("{} :: Echec :: {}".format(barcode,set_response))
            report.write("{}\tErreur Mise à jour Exemplaire\t{}\n".format(barcode,set_response))
            continue
        log_module.info("{} :: Succes :: {}".format(barcode,call_number))
        report.write("{}\tExemplaire mis à jour\t{}\n".format(barcode,call_number))
    else :
        log_module.info("{} :: L'exemplaire a déjà un numéro d'inventaire :: {}".format(barcode,num_inv))
        report.write("{}\tExemplaire non modifié\t{}\n".format(barcode,num_inv))


report.close
log_module.info("FIN DU TRAITEMENT")
