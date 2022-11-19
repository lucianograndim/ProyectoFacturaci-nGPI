from datetime import datetime
from bson import ObjectId
import requests
import random
import time
import json
from multiprocessing import Process
from flask import session
from mongoengine.context_managers import switch_db
from v1.resources.auth.authorization import Auth
from v1.resources.auth.dbDecorator import dbAccess
from flask import Flask, jsonify, request
from flask_restful import Resource, reqparse, Api
from flask_mongoengine import MongoEngine
from config import app
import logging
from v1.models.whatsapp.modelo_datos_wsap import ConversacionLog, InteraccionLog, WebHookData, Device, CampaignLog
#parametros de entrada de la api
parametros_input = reqparse.RequestParser()
# Este id se crea al iniciar una campaña
parametros_input.add_argument('id_camp', type=str, required=False,  location='json', help="...")
# Numero de wsap del contacto 
parametros_input.add_argument('destinatario', type=str, required=True,  location='json', help="...")
# Cuenta de wsap asociada o nombre del webhook que ejecuta la peticion
parametros_input.add_argument('origen', type=str, required=False,  location='json', help="...")
# Nombre general de la campaña
parametros_input.add_argument('nombre_camp', type=str, required=False,  location='json', help="...")
# Tipo de campaña
parametros_input.add_argument('type_camp', type=str, default="inbound",  location='json', help="...")
# Id de la cuenta de canal 
parametros_input.add_argument('id_cuenta_canal', type=str, required=False,  location='json', help="...")
# Configuracion asociadas al dispositivo y canla de wsap - Campañas: parametros canal
parametros_input.add_argument('canal_config', type=dict, required=False,  location='json', help="...")
# Id o nombre del bot (api_bot)
parametros_input.add_argument('id_bot', type=str,  required=False,  location='json', help="...")
# Id que identifica univocamente al contacto (puede ser rut, nombre completo,numero wsap, etc) 
parametros_input.add_argument('id_contacto', type=str, required=False,  location='json', help="...")
# Parametro que le indica a la api si la conversacion debe iniciar o responder un mensaje de una conversacion ya iniciada.
# Los parametros de mas abajo corresponde a una conversacion ya iniciada.
parametros_input.add_argument('accion_api', type=str, default='iniciar_conversacion',  choices=['iniciar_conversacion','evento', 'mensaje_contacto'], location='json', help="Seleccione accionar de la api: 'iniciar_conversacion','evento' o 'mensaje_contacto'.")
# Mensaje del contacto. En el mensaje inicial no se envia. Lo envia a la api solo el webhook.
parametros_input.add_argument('mensaje_contacto', type=str, location='json', help="")
# Id de conversacion. En el mensaje inicial no se envia. Lo envia a la api solo el webhook.
parametros_input.add_argument('id_conversacion', type=str, location='json', help="")
# Id de interaccion. En el mensaje inicial no se envia. Lo envia a la api solo el webhook.
parametros_input.add_argument('id_interaccion', type=str, location='json', help="")

# operador {tipo_operador:bot/agente, id_operador:"bot1/agentes_ventas"}

class WebhookWassi(Resource):
    @Auth.authenticate    
    @dbAccess.mongoEngineAccess
    def get(self):
        #Alias de base de datos para mongoengine
        user_db = session["dbMongoEngine"]
        logging.debug(user_db)
        return jsonify({"message":"request ok.", "session":session, "status":200})
    
    #Este metodo proviene de un servidor externo que envia un webhook
    #Por lo tanto no tiene metodos de autentificacion.
    def post(self):
        #Alias de base de datos para mongoengine
        user_db = session["dbMongoEngine"]
        #Recuperar argumentos de json en body del request
        argumentos = request.get_json(force=True)     
        logging.debug(argumentos)
        #Si el webhook envia una lista nos quedamos con el primer elemento (que esperamos sea un diccionario)
        if type(argumentos) is list:
            argumentos = argumentos[0]
        #Verifico que recibo un diccionario desde el webhook
        if type(argumentos) is dict:
            #Verifico que el webhook viene con los parametros requeridos en el diccionario
            if 'event' in argumentos and 'id' in argumentos and 'device' in argumentos and 'data' in argumentos:
                # Linea para evitar mensajes entrantes de grupos de whatsapp. 
                if argumentos['data']['chat']['type']!='chat':
                    return #Mensaje no proviene de un chat
            else:
                return #Objeto del Webhook no trae los datos que se necesitan
        else:
            return #Webhook no esta mandando un diccionario
        
        #Parametros del webhook
        evento = argumentos['event']
        logging.debug(f'1. EVENTO = {evento}')
        id_device = argumentos['device']['id']
        logging.debug(f'1.1 Id Device = {id_device}') #Id de dispositivo
        id_interaccion_wassi = argumentos['id']
        logging.debug(f'2. Id Interaccion = {id_interaccion_wassi}')

        #Si el evento es un mensaje de entrada
        if evento=='message:in:new':
            numero_contacto = argumentos['data']['fromNumber'] #Destinatario
            numero_dispositivo = argumentos['data']['toNumber'] #Origen 
            mensaje_contacto = argumentos['data']['body']
            logging.debug(f'3. Mensaje = {mensaje_contacto}')
            #Obtener id_cuenta_canal utilizando id_dispositivo.
            cuenta_canal = Device.objects.get(device_id=id_device)  
            id_cuenta_canal = cuenta_canal.device_name
            #Obtener id_campaña utilizando id_cuenta_canal. Si hay mas de una campaña asociada, me quedo con la campaña activa.
            campaign_log = CampaignLog.objects.get(id_cuenta_canal=id_cuenta_canal, estado_camp='activa')
            #Configuro parametros que se enviaran a la api de mensajeria
            payload =  {"id_camp":str(campaign_log.id), "destinatario":numero_contacto, "origen":numero_dispositivo, 
                        "nombre_camp":campaign_log.nombre_camp, "id_cuenta_canal":id_cuenta_canal, "canal_config":campaign_log.parametros_canal, 
                        "id_bot":campaign_log.operadores["id_operador"], "mensaje_contacto":mensaje_contacto, "id_interaccion":id_interaccion_wassi}
            #!Verificar si mensaje entrante corresponde a una conversacion ya iniciada (y no cauducada) de la campaña activa.
            #Defino si la conversacion esta iniciando (nueva) o ya habia comenzado (antigua)
            conversacion = ConversacionLog.objects(id_campana=str(campaign_log.id), destinatario=numero_contacto).order_by('-id').first()
            #Si conversacion es nueva la inicio con api mensajeria
            if not conversacion or mensaje_contacto=='*reset':
                logging.info('Conversacion Nueva.')
                payload.update({"accion_api":"iniciar_conversacion", "id_contacto":numero_contacto})
            #Si conversacion es antigua la continuo con api mensajeria
            else:
                logging.info('Conversacion Antigua.')
                payload.update({"accion_api":"mensaje_contacto", "id_contacto":conversacion.id_contacto, "id_conversacion":str(conversacion.id)})

            #buscar conversacion para obtener parametros de la api de mensajeria.
            #Se obtiene la ultima conversacion registrada del match origen-destinatario.
            logging.debug(f'4.a Destinatario = {numero_contacto}')
            logging.debug(f'4.c Id Dispositivo = {id_device}')
            endpoint_api_mensajeria = app.config['API_MENSAJES_WHATSAPP_ENDPOINT']
            headers = {"Content-Type": "application/json"}
            requests.request("POST", endpoint_api_mensajeria, data=json.dumps(payload), headers=headers)
        

        #Si el evento NO es un mensaje de entrada, entonces es una notificacion de envio o lectura de mensaje
        #Para estos eventos solo se actualizaran los registros de la base de datos
        else:
            evento_contacto = argumentos['data']['ack']
            if evento_contacto=='message:out':
                estado_mensaje=''
                estado_comunicacion=''
            disposicion_canal=evento_contacto            
            estado_mensaje=evento_contacto
            estado_comunicacion=evento_contacto
            #usar id de interaccion para actualizar log_interaccion y encontrar id_conversacion.
            try:
                interaccion = InteraccionLog.objects.get(id_interaccion=id_interaccion_wassi)
                interaccion.estado_mensaje=estado_mensaje
                interaccion.save()
                #Se obtiene conversacion utilizando el parametro id_conversacion guardado en log de interaccion.
                conversacion = ConversacionLog.objects.get(id=interaccion.id_conversacion)   
                conversacion.estado_comunicacion = {'estado':estado_comunicacion, 'datetime':datetime.now()}
                conversacion.estados_comunicacion_historial.append({'estado':estado_comunicacion, 'datetime':datetime.now()})
                conversacion.disposition_canal = disposicion_canal
                conversacion.save()
            except Exception as e:
                logging.warning('Error al actualizar log de interaccion o conversacion. Error: '+str(e))
        return {"status":200}

class ApiMensajeriaWsap(Resource):
    
    @Auth.authenticate    
    @dbAccess.mongoEngineAccess       
    def post(self):
        #Alias de base de datos para mongoengine
        user_db = session["dbMongoEngine"]
        parametros = dict(parametros_input.parse_args()); 
        numero_contacto= parametros["destinatario"]
        id_contacto= parametros["id_contacto"]
        id_cuenta_canal = parametros["id_cuenta_canal"]
        accion_api= parametros["accion_api"]
        numero_dispositivo = parametros["origen"]
        reference = parametros["id_camp"]
        token = app.config['TOKEN_CUENTA_WASSI']
        id_contacto = parametros["id_contacto"]
        accion_api = parametros["accion_api"]
        disp_origen = Device.objects.get(device_name=id_cuenta_canal).device_id
        
        #Esta accion ocurre cuando la campaña inicia la conversacion bot-contacto
        if accion_api=='iniciar_conversacion':
            #Registro de la conversacion. El id de conversacion se crea en la primera llamada de la api. Despues el webhook lo envia como parametro.
            id_conversacion = self.conversacion_log(parametros)
            #! Si hay un mensaje de contacto entrante registrar interaccion. Enviar mensaje a api_bot

            #LLAMADA INICIAL A BOT            
            respuesta_apibot = self.callBot(id_conversacion, interaccion_num=1, parametros_llamada=parametros, 
                                            comando_canalAbot="iniciar_conversacion", accion_contacto="", mensaje="")
            #Recuperar primera respuesta de bot
            mensaje_bot = respuesta_apibot["mensaje_bot"]
            intencionContacto = respuesta_apibot["metadata_bot"]["intencionContacto"]
            intencionBot = respuesta_apibot["metadata_bot"]["intencionBot"]
            comando_botAcanal = respuesta_apibot["metadata_bot"]["comandoAcanal"]
            #Enviar primer mensaje a wasil
            resultado = self.enviar_mje_wassi(numero_contacto, disp_origen, mensaje_bot, reference, token)
            id_interaccion = resultado['id']
            estado_interaccion = resultado['estado']
            self.interaccion_log(id_conversacion=id_conversacion, id_wassi=id_interaccion, hablante='bot', intencion=intencionBot, 
                                 mensaje=mensaje_bot, accion=comando_botAcanal, parametros_llamada=parametros)            
            self.update_conversacion_log(id_conversacion, estado_comunicacion=estado_interaccion, disposicion_canal='CONVERSACION_INICIADA')
            
        #Esta accion ocurre cuando el contacto responde a los mensajes del bot
        elif accion_api in ['evento', 'mensaje_contacto']:
            #Recepcionar mensaje del contacto
            mensaje_contacto = parametros["mensaje_contacto"]
            comando_canalAbot = 'hablar'
            #Actualizar log conversacion
            id_conversacion = parametros["id_conversacion"]
            id_interaccion = parametros["id_interaccion"]
            self.update_conversacion_log(id_conversacion, estado_comunicacion='mensaje_contacto_recibido')            
            #!Enviar mje a api bot
            respuesta_apibot = self.callBot(id_conversacion, interaccion_num=2, parametros_llamada=parametros, 
                                            comando_canalAbot=comando_canalAbot, accion_contacto="enviando_texto", mensaje=mensaje_contacto)
            #!Respuesta bot
            mensaje_bot = respuesta_apibot["mensaje_bot"]
            intencionContacto = respuesta_apibot["metadata_bot"]["intencionContacto"]
            intencionBot = respuesta_apibot["metadata_bot"]["intencionBot"]
            comando_botAcanal = respuesta_apibot["metadata_bot"]["comandoAcanal"]
            #Log de respuesta del contacto
            self.interaccion_log(id_conversacion=id_conversacion, id_wassi=id_interaccion, hablante='contacto', intencion=intencionContacto, 
                                 mensaje=mensaje_contacto, accion=comando_canalAbot, parametros_llamada=parametros)                                
            #Enviar respuesta de bot a wasil
            resultado = self.enviar_mje_wassi(numero_contacto, disp_origen, mensaje_bot, reference, token)
            id_interaccion = resultado['id']
            self.update_conversacion_log(id_conversacion, estado_comunicacion='mensaje_bot_enviado')
            self.interaccion_log(id_conversacion=id_conversacion, id_wassi=id_interaccion, hablante='bot', intencion=intencionBot, 
                                 mensaje=mensaje_bot, accion=comando_botAcanal, parametros_llamada=parametros)
        return jsonify(parametros)

    def callBot(self,id_conversacion, interaccion_num, parametros_llamada, comando_canalAbot, accion_contacto, mensaje):
        id_bot = parametros_llamada["id_bot"]
        id_contacto = parametros_llamada["id_contacto"]
        nombre_camp = parametros_llamada["nombre_camp"]
        id_camp = parametros_llamada["id_camp"]
        canal = "whatsapp"
        id_cuenta_canal = parametros_llamada["id_cuenta_canal"]
        payload={"id_bot":id_bot, "id_contacto":id_contacto, "nombre_camp":nombre_camp, "id_camp":id_camp, 
                 "canal":canal, "cuenta_canal":id_cuenta_canal, "id_conversacion_canal":str(id_conversacion), 
                 "comando_canalAbot":comando_canalAbot, "num_interaccion":interaccion_num, "mensaje":mensaje, 
                 "accion_contacto":accion_contacto}
        logging.debug(f"payload apibot = {payload}")
        endpoint_api_bot = app.config['API_BOT_TALK_ENDPOINT']
        headers = {"Content-Type": "application/json"}
        response = requests.request("POST", endpoint_api_bot, data=json.dumps(payload), headers=headers)
        respuesta_apibot = response.json()
        return respuesta_apibot

    def enviar_mje_wassi(self, destinatario, disp_origen, mensaje, referencia, token, retries=5):
        json_data = {"message":mensaje,
        "phone":destinatario,
        "device":disp_origen,
        "reference":referencia,
        "retries":retries}
        endpoint_send_message = app.config['API_WASSI_SEND_MESSAGE']
        headers = {"Content-Type": "application/json","Token": token}
        try:
            response = requests.request("POST", endpoint_send_message, json=json_data, headers=headers)
        except:
            return {"status":500, "message":"Ha ocurrido un error"}
        if not response.status_code == 201:
            return {"status":400, "message":"Ha fallado el envío del mensaje"}
        else:
            return {"status":200, "message":"Mensaje creado exitosamente","id":response.json()["waId"], "estado":response.json()["webhookStatus"]}

    def conversacion_log(self, parametros_llamada):

        conversacion = ConversacionLog(
            canal = 'whatsapp',
            canal_cuenta = parametros_llamada['id_cuenta_canal'],
            canal_config = parametros_llamada["canal_config"],
            nombre_campana = parametros_llamada['nombre_camp'],
            id_campana = parametros_llamada['id_camp'],
            id_contacto = parametros_llamada['id_contacto'],
            origen = parametros_llamada['origen'],
            destinatario = parametros_llamada['destinatario'],
            #id_agente = parametros_llamada[],
            id_bot = parametros_llamada['id_bot'],
            datatime_inicio = datetime.now(),
            estado_comunicacion = {'estado':'start', 'datetime':datetime.now()},
            estados_comunicacion_historial = [{'estado':'start', 'datetime':datetime.now()}]
        )
        conversacion.save()
        id_conversacion = str(conversacion.id)

        return id_conversacion

    def update_conversacion_log(self, id_conversacion, estado_comunicacion, disposicion_canal=''):
        id_conversacion = ObjectId(id_conversacion)
        conversacion = ConversacionLog.objects.get(_id=id_conversacion)
        if estado_comunicacion:
            conversacion.estado_comunicacion = {'estado':estado_comunicacion, 'datetime':datetime.now()}
            conversacion.estados_comunicacion_historial.append({'estado':estado_comunicacion, 'datetime':datetime.now()})
        if disposicion_canal:
            conversacion.disposition_canal = disposicion_canal        
        conversacion.save()
        return

    def interaccion_log(self, id_conversacion, id_wassi, hablante, intencion, mensaje, accion, parametros_llamada):

            interaccion = InteraccionLog(
                id_conversacion = id_conversacion,
                id_interaccion=id_wassi,
                nombre_campana = parametros_llamada['nombre_camp'],
                id_campana = parametros_llamada['id_camp'],
                #id_agente = StringField()
                id_bot = parametros_llamada['id_bot'],
                hablante = hablante,
                mensaje = mensaje,
                intencion = intencion,
                inicio_datatime = datetime.now(),
                #fin_datatime = fecha_final,
                #duracion = duracion,
                #id_grabacion = StringField()
                #registros_canal = StringField()
                accion_operador = accion
            )
            interaccion.save()

            return 


