
from v1.resources.auth.authorization import Auth
from v1.resources.auth.dbDecorator import dbAccess
from v1.models.text_channels.data_model import ConversacionLog, CampaignConfigModel,Users
from v1.resources.auth.encript import decrypt
from requests.auth import HTTPBasicAuth
from config import app
from time import sleep
import os
import requests
import logging
import json

from mongoengine.context_managers import switch_db
from flask import session
from celery import Celery
from bson.objectid import ObjectId


celery = Celery(__name__)
celery.conf.broker_url = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379")
celery.conf.result_backend = os.environ.get("CELERY_RESULT_BACKEND", "redis://localhost:6379")

@celery.task(name='task0')
def task0(context, **args):
    with context:
        task1(**args)

#@Auth.authenticate
#@dbAccess.mongoEngineAccess
def task1(arg1,arg2,arg3,db):
    logging.debug(f"Entrando a Task1 con id: {arg1}")
    sleep(int((arg3*60)+5))
    logging.info(f"despertó")
    # Sólo se necesita el id conversacion
    with switch_db(ConversacionLog, db):
        logging.info(f"entramos a switch db")
        papperline=[
            {
                '$match': {
                    '_id': ObjectId(arg1)
                }
            }, {
                '$project': {
                    'estado_conversacion': '$estado_comunicacion', 
                    'id_contacto': '$id_contacto', 
                    'contacto_cuenta': '$contacto_cuenta', 
                    'canal': '$canal', 
                    'canal_cuenta': '$canal_cuenta', 
                    'id_campana': '$id_campana', 
                    'tipo_campana': '$tipo_campana', 
                    'nombre_campana': '$nombre_campana', 
                    'ultimo_estado_estados': {
                        '$last': '$estados_comunicacion_historial.estado'
                    }, 
                    'dif_now_last_state': {
                        '$trunc': [
                            {
                                '$divide': [
                                    {
                                        '$subtract': [
                                            '$$NOW', {
                                                '$last': '$estados_comunicacion_historial.datetime'
                                            }
                                        ]
                                    }, 1000
                                ]
                            }
                        ]
                    }
                }
            }
        ]
        conversacion = ConversacionLog.objects.aggregate(papperline)
        convs = []
        for conv in conversacion:
            convs.append(conv)
        logging.debug(f"conversación: {convs}")
    conversacion = convs[0]
    # from time import sleep
    # sleep(i["time"])
    # TODO: "ver que el es el mismo estado de hace 10 min"
    logging.debug(f"conversación: {conversacion}")
    if conversacion["dif_now_last_state"] >= (arg3*60) and conversacion["estado_conversacion"] == "transferred":
        with switch_db(Users, db):
            User = Users.objects(isChannelAccount=True).first()
        if User is not None:
            logging.info("Utilizando cuenta de servicio ya existente")
            KeyWord = app.config["DbConfig"]["EncriptWord"]
            UserApi = User["user_name"]
            UserPass = User["name"]
            UserPass = decrypt(UserPass,KeyWord)
        logging.debug(f"Op message: {str(arg1)}")
        data = {
                "transmitter" : "agent",
                "id_contact" : conversacion['id_contacto'],
                "contact_account" : conversacion['contacto_cuenta'],
                "channel" : conversacion['canal'],
                "channel_account" : conversacion['canal_cuenta'],
                "id_campaign" : conversacion['id_campana'],
                "campaign_name" : conversacion['nombre_campana'],
                "campaign_type" : conversacion['tipo_campana'],
                "operator" : {'id_operador': "system", 'tipo_operador': 'agent'},
                "type_message" : "text",
                "operator_message" : arg2,
                "id_conversation" : str(arg1),
                "talker" : "agent"
            }
        logging.debug(f"Payload to api_text: {data}")
        Url = app.config['DNS_API_TEXT']+"/channel/text_channels/message"
        data = json.dumps(data)
        Headers = {
            'Content-Type': 'application/json'
        }
        Response = requests.request("POST", Url, headers=Headers, data=data, auth=HTTPBasicAuth(UserApi, UserPass))
        if Response.status_code == 200:
            logging.info(f"Respuesta api_texto: {Response.json()}")
        else:
            logging.error(f"Respuesta api_texto (error): {Response.text}")

        # Llamar a la Api Agents para hacer la transferencia de vuelta al bot
        trans_payload = {
            "idConversation": str(arg1),
            "automatic": True
        }
        trans_payload = json.dumps(trans_payload)
        trans_url= app.config['DNS_API_AGENTS2']+"/transferToBot"
        Response_agent = requests.request("PUT", trans_url,
            data=trans_payload, auth=HTTPBasicAuth(UserApi, UserPass),headers=Headers)
            
        if Response_agent.status_code in [200, 201]: # Con 201 quiere tipificar la conversación
            logging.info(f"Respuesta api_agents: {Response_agent.json()}")
        else:
            logging.error(f"Respuesta api_agents (error): {Response_agent.text}")

    return True
