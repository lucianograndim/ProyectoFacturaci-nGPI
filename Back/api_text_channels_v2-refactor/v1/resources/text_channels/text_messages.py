from datetime import datetime
from bson import ObjectId
import requests, json
from flask import session
from mongoengine.context_managers import switch_db
from v1.resources.auth.authorization import Auth
from v1.resources.auth.dbDecorator import dbAccess
from flask import jsonify
from flask_restful import Resource, reqparse
from config import app
from v1.models.text_channels.data_model import ConversacionLog, InteraccionLog, CampaignLog, CampaignLists, CampaignConfigModel
import logging
from threading import Thread
from v1.utils.tasks import task1

#parametros de entrada de la api
parametros_input = reqparse.RequestParser()
parametros_input.add_argument('transmitter', type=str, required=True, choices=['contact', 'agent', 'bot', 'outbound_campaign'], location='json', help="...")
parametros_input.add_argument('id_contact', type=str, required=True,  location='json', help="...")
parametros_input.add_argument('contact_account', type=str, required=True,  location='json', help="...")
parametros_input.add_argument('contact_details', type=dict, required=False,  location='json', help="...")
parametros_input.add_argument('contact_message', type=str, required=False,  location='json', help="...")
parametros_input.add_argument('contact_message_event', type=str, required=False,  location='json', help="...")
parametros_input.add_argument('contact_message_action', type=str, required=False,  location='json', help="...")
parametros_input.add_argument('contact_message_metadata', type=dict, required=False,  location='json', help="...")
parametros_input.add_argument('channel', type=str, required=True,  location='json', help="...")
parametros_input.add_argument('channel_provaider', type=str, required=False, default="", location='json', help="...")
parametros_input.add_argument('channel_account', type=str, required=True,  location='json', help="...")
parametros_input.add_argument('channel_settings', type=dict, required=False,  location='json', help="...")
parametros_input.add_argument('id_campaign', type=str, required=False,  location='json', help="...")
parametros_input.add_argument('campaign_name', type=str, required=False,  location='json', help="...")
parametros_input.add_argument('campaign_type', type=str, required=False,  location='json', help="...")
parametros_input.add_argument('id_conversation', type=str, required=False,  location='json', help="...")
parametros_input.add_argument('operator', type=dict, required=False,  location='json', help="...")
parametros_input.add_argument('type_message', type=str, required=True,  location='json', help="...")
parametros_input.add_argument('operator_message', type=str, required=False,  location='json', help="...")
parametros_input.add_argument('mensaje_unico', type=str, required=False,  location='json', help="...")
parametros_input.add_argument('id_file', type=str, required=False, default="", location='json', help="...")
parametros_input.add_argument('id_conversation', type=str, required=False,  location='json', help="...")
parametros_input.add_argument('talker', type=str, required=False,  location='json', help="...")
parametros_input.add_argument('typeMedia', type=str, required=False,  location='json', help="...")


class HealthCheck(Resource):
    def get(self):
        return 'OK', 200

class TextMessage(Resource):
    @Auth.authenticate
    @dbAccess.mongoEngineAccess
    def get(self):
        #Alias de base de datos para mongoengine
        #user_db = session["dbMongoEngine"]
        session='ok'
        logging.info('ok get')
        return jsonify({"message":"request ok.", "session":session, "status":200})

    @Auth.authenticate
    @dbAccess.mongoEngineAccess
    def post(self):
        #Alias de base de datos para mongoengine
        user_db = session["dbMongoEngine"]
        token_api = session["token"]
        #Parametros de entrada de la api
        parametros = dict(parametros_input.parse_args());         
        message_origin = parametros['transmitter']
        id_contact = parametros['id_contact']
        contact_account = parametros['contact_account']
        contact_details = parametros['contact_details']
        channel = parametros['channel']
        channel_provaider = parametros['channel_provaider']
        channel_account = parametros['channel_account']
        bot_responds=False
        logging.debug(f'API REQUEST INPUT: {parametros}')
        logging.debug(f'ORIGEN DEL MENSAJE: {message_origin}')
        logging.debug(f'CONTACTO: {contact_account} - {id_contact}')
        logging.debug(f'CANAL: {channel} - proveedor: {channel_provaider} - cuenta: {channel_account}')

        if message_origin in ['outbound_campaign', 'agent', 'bot']:
            id_campaign = parametros['id_campaign']
            campaign_name = parametros['campaign_name']  
            campaign_type = parametros['campaign_type']            
            logging.debug(f'CAMPAÑA: {campaign_name} - TIPO: {campaign_type} - ID CAMPAÑA: {id_campaign}')
            #!Cuando mensaje viene desde el contacto se debe obtener operador desde list_campaign (lista de contactos de la campaña)                      
            operator_type = parametros['operator']['tipo_operador']
            id_operator = parametros['operator']['id_operador']
            logging.debug(f'OPERADOR: {operator_type} - {id_operator}')

        #Se determina origen del mensaje
        #!CAMPAÑA ====>> CONTACTO
        #INICIO DE CONVERSACION POR UNA CAMPAÑA
        #MENSAJE INICIADO POR UNA CAMPAÑA OUTBOUND. DESTINO = CONTACTO
        if message_origin=='outbound_campaign':
            #!Crear log de conversacion en conversaciones_log
            logging.info("NUEVA CONVERSACION...")
            id_conversacion = conversacion_log(user_db, parametros, campaign_name, campaign_type, id_campaign, operator_type, id_operator)
            logging.debug(f'id_conversacion: {id_conversacion}')
            #Si es un mensaje estatico
            tipo_mensaje_unico = parametros['type_message']
            logging.debug(f'TIPO DE MENSAJE: {tipo_mensaje_unico}')
            #!CAMPAÑA ====>> MENSAJE UNICO ====>> CONTACTO
            if tipo_mensaje_unico:
                #Recuperar mensaje
                mensaje_unico = parametros['mensaje_unico']
                if tipo_mensaje_unico!='text':
                    id_file = parametros['id_file']
                else:
                    id_file = ''
                message_origin = "static_message"
        #!CAMPAÑA ====>> OPERADOR ====>> CONTACTO
        if message_origin == 'bot':
            #!Crear log de conversacion en conversaciones_log
            id_conversacion = conversacion_log(user_db, parametros, campaign_name, campaign_type, id_campaign, operator_type, id_operator)  
            logging.info("NUEVA CONVERSACION...")
            logging.debug(f'ID CONVERSACION: {id_conversacion}')
            #!Si operador es solo bot
            if operator_type == 'bot':
                #!Iniciar bot
                #LLAMADA INICIAL A BOT            
                logging.info("REQUEST A API BOT...")
                respuesta_apibot = call_bot(token_api, "", channel, channel_provaider, channel_account, id_operator, contact_account, contact_account, 
                                            contact_details, id_campaign, campaign_name, campaign_type, id_conversacion, 
                                            id_interaccion_channel='', type_message='', message='', id_file='', contact_message_event='', 
                                            channel_to_bot_action="iniciar_conversacion")
                logging.debug(f'RESPUESTA APIBOT: {respuesta_apibot}')
            #!Enviar mensaje a contacto a traves de api canal
            
        #RECEPCION DE MENSAJES DE LOS CONTACTOS
        #MENSAJE ENVIADO POR UN CONTACTO. DESTINO = AGENTE, BOT
        #! CONTACTO
        if message_origin == 'contact':
            type_message = parametros["type_message"]
            contact_message = parametros["contact_message"]
            contact_message_event = parametros["contact_message_event"]
            logging.debug(f'EVENTO MENSAJE: {contact_message_event}')
            logging.debug(f"TIPO DE MENSAJE: {type_message}")
            logging.debug(f"MENSAJE CONTACTO: {contact_message}")
            #!Se obtiene campaña asociada a cuenta de canal
            with switch_db(CampaignLog, user_db):
                logging.debug(f"BASE DE DATOS USER_DB: {user_db}")
                channel_provider = channel_provaider if channel_provaider else ""
                logging.info('BUSCANDO CAMPAÑA ASOCIADA...')
                logging.debug(f"PARAMETROS DE BUSQUEDA => CANAL: {channel} {channel_provaider}; ID CUENTA CANAL: {channel_account}")
                try:
                    campaign_log = CampaignLog.objects.get(canal=channel, proveedor_canal=channel_provaider, id_cuenta_canal=channel_account, estado_camp__in=['activa','ejecutando']) #, estado_camp__in=['activa','ejecutando'])
                except CampaignLog.DoesNotExist:
                    campaign_log = CampaignLog.objects.get(canal=channel, id_cuenta_canal=channel_account, estado_camp__in=['activa','ejecutando']) #, estado_camp__in=['activa','ejecutando'])
                
            id_campaign = str(campaign_log.id)
            campaign_name = campaign_log["nombre_camp"]
            campaign_type = campaign_log["tipo_camp"]
            logging.debug(f'NOMBRE CAMPAÑA: {campaign_name} - ID_CAMP: {id_campaign} - TIPO CAMPAÑA: {campaign_type}')

            #Encontrar ultimo registro de conversacion            
            with switch_db(ConversacionLog, user_db):
                logging.info('BUSCANDO CONVERSACION...')
                conversacion=None
                logging.debug(f'PARAMETROS DE BUSQUEDA => estado_campana: activa - canal: {channel} - canal_cuenta: {channel_account} - contacto_cuenta: {contact_account} - id_campana: {id_campaign}')
                try:
                    conversacion = ConversacionLog.objects(canal=channel, canal_cuenta=channel_account, contacto_cuenta=contact_account, id_campana=id_campaign,conversation_finished=False).order_by('-id').first()
                except ConversacionLog.DoesNotExist:
                    conversacion = ConversacionLog.objects(canal=channel, canal_cuenta=channel_account, contacto_cuenta=contact_account, id_campana=id_campaign).order_by('-id').first()

            if conversacion:
                new_conversation = False
                logging.info("CONVERSACION ENCONTRADA...")
                id_conversacion = conversacion.id
                
            #!Si conversacion no existe significa que es una campaña inbound y la conversacion es nueva
            #!En ese caso se debe obtener la campaña a traves de campañas log y crear el log de conversacion y el log de contacto en campaigns_list
            if not conversacion:
                logging.info('CONVERSACION NO ENCONTRADA')
                new_conversation = True
                operador = campaign_log.operadores
                id_operator = operador["id_operador"]
                operator_type = operador["tipo_operador"]           

                if campaign_type == 'outbound':
                    logging.warning(f"Mensaje de contacto {contact_account} - {id_contact} fuera de Campaña")
                    return 'Mensaje fuera de Campaña', 200
                
                #!Agregar contacto a campaigns_list
                campaignList={
                    "name_campaign": campaign_log["nombre_camp"],
                    "id_campaign": ObjectId(campaign_log["id"]),
                    "operador": campaign_log["operadores"],
                    "channel_type": "text",
                    "channel": channel,
                    'channel_provaider':channel_provaider,
                    "channel_id": channel_account,
                    "id_contact": contact_account,
                    "id_phone": contact_account,
                    "dialed_phone": False,
                    "conversation_started": False,
                    "dispositions":campaign_log["disposiciones"],
                    "contact_details": [] }
                with switch_db(CampaignLists, user_db):
                    campaignList=CampaignLists(**campaignList)
                    campaignList.save()
                    
                #!Se registra conversacion nueva
                logging.info("SE REGISTRA NUEVA CONVERSACION...")
                id_conversacion = conversacion_log(user_db, parametros, campaign_name, campaign_type, id_campaign, operator_type, id_operator)  
                
            with switch_db(ConversacionLog, user_db):
                conversacion = ConversacionLog.objects.get(_id=ObjectId(id_conversacion))
                logging.debug(f'ID CONVERSACION: {conversacion.id}')

            #!Se utiliza coleccion CampaignList para saber que operador tiene tomada la conversacion
            with switch_db(CampaignLists, user_db): 
                logging.info("BUSCANDO OPERADOR DE CONVERSACION...")
                contact_list = CampaignLists.objects(id_campaign=ObjectId(id_campaign), id_phone=contact_account).order_by('-id').first()

            operador = contact_list.operador            
            operator_type = operador["tipo_operador"]            
            if "dispositions" in contact_list:
                dispositions = contact_list["dispositions"]            
                        
            #!CONTACTO ====>> BOT
            #!Si el operador es un bot:
            if operator_type=='bot' and conversacion["tipo_operador"]=="bot":
                #!Registrar interaccion en coleccion conversaciones e interacciones.
                #!Tambien si la interaccion es una notificacion de lectura u otro evento similar
                #!Enviar mensaje a api_agentes
                id_bot = operador["id_operador"]        
                logging.debug(f'OPERADOR: {operator_type} - {id_bot}')
                id_interaccion_channel = parametros["contact_message_metadata"]["id_interaccion"]
                action_contact = ""      
                id_file = ""
                #!Si la interaccion es un mensaje
                if contact_message_event=='new_message':
                    #!Enviar mensaje a bot
                    if contact_message is None:
                        contact_message = "Multimedia"
                    logging.info('ENVIANDO MENSAJE DE CONTACTO A BOT...')
                    if new_conversation:
                        action_bot = 'iniciar_conversacion'
                    else:
                        action_bot = 'hablar'
                    logging.debug(f'ACCION BOT: {action_bot}')
                    respuesta_apibot = call_bot(token_api, "", channel, channel_provaider, channel_account, id_bot, id_contact, contact_account, 
                                                contact_details, id_campaign, campaign_name, campaign_type, id_conversacion, 
                                                id_interaccion_channel, type_message, contact_message, id_file, 
                                                contact_message_event, channel_to_bot_action=action_bot)             

                    logging.debug(f"RESPUESTA API BOT: {respuesta_apibot}")
                    MetaDataBot = respuesta_apibot["metadata_bot"]
                    logging.debug(f"METADATA BOT: {MetaDataBot}")
                    logging.debug(f'COMANDO A CANAL: {MetaDataBot["comandoAcanal"]}')
                    if MetaDataBot["comandoAcanal"] in ["TRANSFERIR_CONVERSACION","TRANSFERIR CONVERSACION"]:
                        with switch_db(ConversacionLog, user_db):
                            conversacion["tipo_operador"] = "agent"
                            conversacion["id_operador"] = " "
                            conversacion["transferred"] = True
                            estado_com = {'estado':"transferred", 
                                'tipo_operador': 'agent', 
                                'id_operador': "",
                                'equipo': "default",
                                'id_equipo': "",
                                'datetime':datetime.now()
                            }
                            conversacion["estados_comunicacion_historial"].append(estado_com)
                            conversacion["estado_comunicacion"] = "transferred"
                            conversacion.save()
                        # [aqui se hace la transferencia al agente y debería iniciar el "timer" del timeout]
                        # Agregar la verificación de la DB para correr esta tarea
                        with switch_db(CampaignConfigModel, user_db):
                            config = CampaignConfigModel.objects.get(_id=conversacion['nombre_campana'])
                            logging.debug(f"config campaña de id:{conversacion['nombre_campana']}")
                        if "queued_tasks" in config:
                            logging.debug(f"config :{config['queued_tasks']}")
                            for key in config["queued_tasks"].keys():
                                queued_tasks = config["queued_tasks"][key]
                                logging.debug(f"queued task :{queued_tasks}")
                                if queued_tasks["event"] == "transferred":
                                    logging.debug(f"thread de: {int(queued_tasks['time']*60)} segundos")
                                    task = Thread(target=task1,args=(str(id_conversacion),queued_tasks["action"]["act_args"],queued_tasks["time"],user_db,),daemon=False)
                                    task.start()
                    else:      
                        #!Registrar interaccion del contacto en coleccion conversaciones e interacciones.
                        intencionContacto = respuesta_apibot["metadata_bot"]["intencionContacto"]                        
                        #!Guardar interaccion                        
                        interaccion_log(user_db, id_conversacion, id_interaccion_channel, 'contact', campaign_name, campaign_type, id_campaign, 
                                        channel, channel_provaider, channel_account, id_contact, contact_account, operator_type, id_bot, type_message, 
                                        contact_message, id_file, contact_message_event, intencionContacto, True)  
                                          
                    #self.update_conversacion_log(id_conversacion, estado_comunicacion=estado_interaccion, disposicion_canal='CONVERSACION_INICIADA')
                    #!Enviar respuesta de bot (codigo mas abajo)
                    message_origen = 'bot'
                    if respuesta_apibot['mensaje_bot'] != "":
                        bot_responds=True
                #!Tambien registrar si la interaccion es una notificacion de lectura u otro evento similar y no es necesario enviar a bot.
            if type_message=='read_notification':                
                #update_conversacion_log
                notification = contact_message_event
                logging.info(notification)  
                try:
                    id_interaccion_channel = parametros["contact_message_metadata"]["id_interaccion"]
                    id_nteraccion = update_interaccion_log(user_db, id_interaccion_channel, notification)
                except Exception as ex:
                    logging.error("error al recibir read: "+str(ex))
            #! CONTACTO ==>> AGENTE
            #!Si el operador es un agente (libre o identificado)            
            if operator_type=='agent' or conversacion["tipo_operador"] =="agent":
                logging.info('entro a agente s')
                logging.debug(f'3.3 Operador = {operator_type}')
                
                #!Registrar inagenteteraccion en coleccion conversaciones e interacciones.
                #!Tambien si la interaccion es una notificacion de lectura u otro evento similar
                #!Enviar mensaje a api_agentes
                id_agent = operador["id_operador"]           
                id_file = parametros['id_file']     
                
                id_interaccion_channel = parametros["contact_message_metadata"]["id_interaccion"]
                action_contact = ""
                logging.debug('type_message: '+str(type_message))
                id_interaccion = None
                if type_message=='text_message' or type_message=='' or type_message=='text':
                    if operator_type != "agent" and conversacion["tipo_operador"] == "agent":
                        id_agent =""
                    logging.debug('entro a text_message: '+str(contact_message))
                    id_interaccion = interaccion_log(user_db, id_conversacion, id_interaccion_channel, 'contact', campaign_name, campaign_type, id_campaign, 
                                                    channel, channel_provaider, channel_account, id_contact, contact_account, operator_type, id_agent,
                                                    type_message, contact_message, id_file, contact_message_event, action_contact)     
                    logging.debug(f"id_interaccion: {id_interaccion}")
                elif type_message=='voice_call':
                    if contact_message_event=='missed_call':
                        id_interaccion = False
                        if 'eventos' in dispositions:
                            eventos = dispositions['eventos']
                            for evento in eventos:
                                if evento['tipo_evento']=='missed_call':
                                    tipo_mensaje_unico = evento["tipo_respuesta"]
                                    if tipo_mensaje_unico=='text':
                                        logging.info(10)     
                                        mensaje_unico = evento["respuesta"]
                                        id_file = ''
                                    logging.info('LLAMADA PERDIDA')
                                    data_request = send_message_to_channel(token_api, channel, channel_provaider, channel_account, contact_account, tipo_mensaje_unico, mensaje_unico, id_file)
                                    '''
                                    interaccion_log(user_db, id_conversacion, id_interaccion_channel, 'contact', campaign_name, campaign_type, id_campaign, 
                                                    channel, channel_account, id_contact, contact_account, operator_type, id_agent,
                                                    type_message, contact_message, id_file, contact_message_event, action_contact)    
                                    '''
                                    
                elif type_message=='read_notification':
                    logging.debug('entro a read_notification: '+str(contact_message_event))
                    #update_conversacion_log
                    notification = contact_message_event
                    logging.debug(notification)
                    id_interaccion = update_interaccion_log(user_db, id_interaccion_channel, notification)

                if id_interaccion:
                    if("transferred" in conversacion):
                        transfer = conversacion["transferred"]
                    else:
                        transfer = False
                    logging.info("Ingresará a send_message_to_agent")
                    respuesta = send_message_to_agents( token_api, id_interaccion, channel, channel_provaider, channel_account, id_agent, id_contact, contact_account, 
                                                        contact_details, id_campaign, campaign_name, campaign_type, id_conversacion, 
                                                        id_interaccion_channel, type_message, contact_message, id_file, contact_message_event, 
                                                        channel_to_bot_action=action_contact,transferred=transfer)
                    logging.info(f"{respuesta}")
                else:
                    logging.debug("\n\n\nNOTIFICACION\n\n\n", id_interaccion_channel, contact_message_event)
                    respuesta = 'Mensaje no enviado'
                
                if "transferred" not in conversacion:
                    return jsonify(respuesta)
            
        #! AGENTE ==>> CONTACTO
        #MENSAJE ENVIADO POR UN AGENTE. DESTINO = CONTACTO
        if message_origin=='agent':
            logging.debug(f'origen =  {message_origin}')
            id_agent = parametros["operator"]["id_operador"] 
            operator_type = parametros["operator"]["tipo_operador"] 
            agent_message = parametros['operator_message']
            type_message = parametros['type_message']
            
            id_file = parametros["id_file"]
            
            action_agent = ''
            #Agente responde en conversacion iniciada por campaña outbound o mensaje inbound.
            id_conversation = parametros['id_conversation']
            logging.info('\n\nMENSAJE AGENTE')
            logging.debug(f'555. ID_CONVERSACION: {id_conversation}')
            #Agente inicia conversacion de forma manual. Campaña outbound.
            #!Si conversacion es nueva crear y guardar en conversaciones_log y list_campaign
            #!(esto es cuando un agente elige un contacto manual e inicia la conversacion)
            if not id_conversation:
                logging.info('conversacion nueva iniciada por agente. Se debe guardar log de conversacion.')       
               
            
            #!Enviar mensaje a contacto a traves de api_canal
            data_request = send_message_to_channel(token_api, channel, channel_provaider, channel_account, contact_account, type_message, 
                                                    agent_message, id_file)
            id_interaccion_channel = data_request['id']
            #!Guardar interaccion
            logging.debug('id_conversacion: '+str(id_conversation))
            if(id_file!=""):
                id_file={
                    "type":parametros["typeMedia"],
                    "resource":id_file
                }
                id_file=str(id_file)
            id_interaccion = interaccion_log(user_db, id_conversation, id_interaccion_channel, 'agent', campaign_name, campaign_type, id_campaign, 
                            channel, channel_provaider, channel_account, id_contact, contact_account, operator_type, id_agent,
                            type_message, agent_message, id_file, '', action_agent)  

            logging.info('RESPUESTA WASSI')
            logging.debug(data_request)
            
            return jsonify({"message": "Mensaje ha sido enviado."})

        try:
            if("transferred" in conversacion):
                transfer = conversacion["transferred"]
            else:
                transfer = False
        except:
            transfer = False

        #! BOT ==>> CONTACTO        
        if message_origin == 'bot' or bot_responds or transfer :
            if "respuesta_apibot" not in locals() and "respuesta_apibot" not in globals():
                logging.info("Mensaje ok")
                return {"resp":"ok"},200
            #Recuperar respuesta de bot
            mensaje_bot = respuesta_apibot["mensaje_bot"]
            intencionBot = respuesta_apibot["metadata_bot"]["intencionBot"]
            comando_botAcanal = respuesta_apibot["metadata_bot"]["comandoAcanal"]
            mje_print=mensaje_bot.replace("\n"," ")
            logging.debug(f'MENSAJE BOT: {mje_print}')
            logging.debug(f'INTENCION BOT: {intencionBot}')
            logging.debug(f'COMANDO BOT A CANAL: {comando_botAcanal}')
            tipo_mensaje = 'text'
            id_file = ''
            
            #!Enviar mensaje a contacto a traves de api canal
            logging.debug(f'ENVIANDO MENSAJE DEL BOT A CANAL {channel} {channel_provaider} AL CONTACTO {contact_account}')
            resultado = send_message_to_channel(token_api, channel, channel_provaider, channel_account, contact_account, tipo_mensaje, mensaje_bot, id_file, comando_botAcanal, str(id_conversacion))
            logging.debug(f"RESPUESTA API {channel} {channel_provaider}: {resultado}")
            id_interaccion = resultado['id'] if "id" in resultado else ""
            estado_interaccion = resultado['estado'] if "estado" in resultado else ""
            
            try:
                id_bot = id_operator
            except: 
                pass
        
            #!Guardar interaccion
            id_interaccion = interaccion_log(user_db, id_conversacion, id_interaccion, 'bot', campaign_name, campaign_type, id_campaign, 
                            channel, channel_provaider, channel_account, id_contact, contact_account, operator_type, id_bot, tipo_mensaje, 
                            mensaje_bot, id_file, comando_botAcanal, intencionBot)    
            #self.update_conversacion_log(id_conversacion, disposicion_canal='CONVERSACION_INICIADA')
                   
        #! CAMPAÑA OUTBOUND ==>> CONTACTO
        #MENSAJE ESTATICO ENVIADO POR CAMPAIGN. DESTINO = CONTACTO
        if message_origin=='static_message':
            logging.info('entro a static_message')
            logging.debug(f'4. origen = {message_origin}')
            #!Enviar mensaje a contacto a traves de api canal
            data_request = send_message_to_channel(token_api, channel, channel_provaider, channel_account, contact_account, tipo_mensaje_unico, mensaje_unico, id_file)
            logging.info("5. Respuesta Api Canal Whatsapp")
            logging.debug(data_request)
            #!Recurar data de api canal
            id_interaccion = data_request['id']
            #!Guardar interaccion

            if(id_file!=""):
                id_file={
                    "type":parametros["type_message"],
                    "resource":id_file
                }
                id_file=str(id_file)
            id_interaccion = interaccion_log(user_db, id_conversacion, id_interaccion, 'campaign_message', campaign_name, campaign_type, id_campaign, 
                            channel, channel_provaider, channel_account, id_contact, contact_account, operator_type, id_operator,
                            tipo_mensaje_unico, mensaje_unico, id_file, 'start_talking', 'message_unique')
            return 'ok mensaje unico'
    
        logging.warning("Mensaje sin respuesta controlada")
        return '', 200
            
def send_message_to_channel(token_api, channel, channel_provider, channel_account, contact_account, type_message, message, id_file, comando_botAcanal='', id_conversacion=''):
    
    payload = { 'channel_account':channel_account,
                "contact_account":contact_account,
                "type_message":type_message,
                "message":message,
                "id_file":id_file,
                "comando_botAcanal":comando_botAcanal,
                "id_conversacion":id_conversacion}
    logging.debug(f'PAYLOAD API {channel} {channel_provider}: {payload}')
    if channel=='whatsapp':
        if channel_provider in ["wassi","","alloxentric"]:
            endpoint_send_message = app.config['DNS_API_WHATSAPP']+f"/channel/{channel}/message".format(channel)
        elif channel_provider=='gupshup':            
            endpoint_send_message = app.config['DNS_API_WHATSAPP_GUPSHUP']+"/channel/gupshup/message"
    elif channel=='chatweb':
        logging.debug(f'DNS_API_CHATWEB {app.config["DNS_API_CHATWEB"]}')
        endpoint_send_message = app.config['DNS_API_CHATWEB']+f"/channel/{channel}/message".format(channel)
    elif channel=='messenger':
        if channel_provider == 'alloxentric':
            endpoint_send_message = app.config["DNS_API_MESSENGER"]+f"/channel/{channel}/message".format(channel)
    headers = {"Content-Type": "application/json", 'Authorization':'Bearer '+token_api}
    logging.debug(f'ENDPOINT API {channel} {channel_provider}: {endpoint_send_message}')
    logging.debug(f"ENVIANDO REQUEST A API {channel} {channel_provider}...")
    response = requests.request("POST", endpoint_send_message, data=json.dumps(payload), headers=headers)    
    logging.debug(f"RESPUESTA API: {response.status_code}")
    respuesta = response.json()
    return respuesta

def send_message_to_agents( token_api, id_interaccion, channel, channel_provider, channel_account, id_agent, id_contact, contact_account, 
                            contact_details, id_campaign, campaign_name, campaign_type, id_conversacion, 
                            id_interaccion_channel, type_message, message, id_file, contact_message_event, channel_to_bot_action,transferred):

    payload = { "channel":channel,
                "channel_provider":channel_provider,
                "channel_account":channel_account,
                "agent_group":"",
                "id_interaccion":id_interaccion,
                "id_agent":id_agent,
                "id_contact":id_contact,
                "contact_account":contact_account,
                "contact_details":contact_details,
                "id_campaign":id_campaign,
                "campaign_name":campaign_name,
                "campaign_type":campaign_type,
                "id_conversacion":str(id_conversacion),
                "id_interaccion_channel":id_interaccion_channel,
                "type_message":type_message,
                "message":message,
                "contact_message_event":contact_message_event,
                "id_file":id_file,
                "channel_to_bot_command":channel_to_bot_action,
                "transferred":transferred
                }

    try:
        logging.info("payload a api agents:")
        logging.debug(payload)
        endpoint_send_message = app.config['DNS_API_AGENTS']
        headers = {"Content-Type": "application/json", 'Authorization':'Bearer '+token_api}
        response = requests.request("POST", endpoint_send_message, data=json.dumps(payload), headers=headers)
        respuesta = response.json()
        print('Respuesta api agents: ', respuesta)
    except Exception as error:
        logging.error(error)
        logging.error(payload)
        respuesta = {'status': 400}
    #respuesta = payload
    return respuesta

def call_bot(   token_api, id_interaccion, channel, channel_provider, channel_account, id_bot, id_contact, contact_account, 
                contact_details, id_campaign, campaign_name, campaign_type, id_conversacion, 
                id_interaccion_channel, type_message, message, id_file, contact_message_event, channel_to_bot_action):

    payload={"id_bot":id_bot, "id_contacto":id_contact, "cuenta_contacto":contact_account,"nombre_camp":campaign_name, 
            "id_camp":id_campaign, "tipo_camp":campaign_type, "canal":channel, "canal_proveedor":channel_provider,"cuenta_canal":channel_account, 
            "id_conversacion_canal":str(id_conversacion), "comando_canalAbot":channel_to_bot_action, "tipo_mensaje":type_message,
            "mensaje":message, "datos_contacto":contact_details,"accion_contacto":contact_message_event}
    logging.debug(f'PAYLOAD API BOT: {payload}')
    endpoint_api_bot = app.config['DNS_API_BOTS']+'/bots/talk'
    logging.debug(f'ENDPOINT API BOT: {endpoint_api_bot}')
    headers = {"Content-Type": "application/json", 'Authorization':'Bearer '+token_api}
    logging.info("ENVIANDO REQUEST A API BOT...")
    response = requests.request("POST", endpoint_api_bot, data=json.dumps(payload), headers=headers)
    logging.debug(f"RESPUESTA API BOT: {response.status_code}")
    respuesta_apibot = response.json()
    return respuesta_apibot

def conversacion_log(user_db, parametros, campaign_name, campaign_type, id_campaign, tipo_operador, id_operador, equipo='default', id_equipo=''):
    conversacion = ConversacionLog(
        canal = parametros['channel'],
        canal_proveedor = parametros["channel_provaider"],
        canal_cuenta = parametros['channel_account'],
        canal_config = parametros["channel_settings"],
        nombre_campana = campaign_name,
        tipo_campana = campaign_type,
        id_campana = id_campaign,
        id_contacto = parametros['id_contact'],
        datos_contacto = parametros['contact_details'],
        contacto_cuenta = parametros['contact_account'],
        tipo_operador = tipo_operador,
        id_operador = id_operador,
        datatime = datetime.now(),
        estado_campana = 'activa',
        estado_comunicacion = 'start',
        estados_comunicacion_historial = [{'estado':'start', 
                'tipo_operador': tipo_operador,
                'id_operador': id_operador,
                'equipo': equipo,
                'id_equipo': id_equipo,
                'datetime':datetime.now()
            }]
    )
    with switch_db(ConversacionLog, user_db):  
        conversacion.save()
    id_conversacion = str(conversacion.id)

    return id_conversacion

def update_conversacion_log(id_conversacion, estado_comunicacion, disposicion_canal='', tipo_operador='', id_operador='', equipo='default', id_equipo=''):
        id_conversacion = ObjectId('',id_conversacion)
        conversacion = ConversacionLog.objects.get(_id=id_conversacion)
        if estado_comunicacion:
            conversacion.estado_comunicacion = estado_comunicacion
            estado_com = {'estado':estado_comunicacion, 
                'tipo_operador': tipo_operador,
                'id_operador': id_operador,
                'equipo': equipo,
                'id_equipo': id_equipo,
                'datetime':datetime.now()
            }
            conversacion.estados_comunicacion_historial.append(estado_com)
        if disposicion_canal:
            conversacion.disposition_canal = disposicion_canal        
        conversacion.save()
        return

def update_interaccion_log(user_db, id_interaccion_channel, notification):
    with switch_db(InteraccionLog, user_db):        
        try:
            interaccion = InteraccionLog.objects.get(id_interaccion_channel=id_interaccion_channel)
            id_interaccion = str(interaccion.id)
            interaccion.mensaje_recibido=True
            interaccion.mensaje_visto=True
            interaccion.save()
        except InteraccionLog.DoesNotExist:
            id_interaccion = None
    return id_interaccion

def interaccion_log(user_db, id_conversacion, id_interaccion_channel, hablante, 
        campaign_name, campaign_type, id_campaign, channel, channel_provider,
        channel_account, id_contact, contact_account, 
        operator_type, id_operator, tipo_mensaje, mensaje, id_file, accion_hablante, intencion='', recibido=False):


        interaccion = InteraccionLog(
            id_conversacion = str(id_conversacion),
            id_interaccion_channel= id_interaccion_channel,            
            nombre_campana = campaign_name,
            tipo_campana = campaign_type,
            id_campana = id_campaign,
            canal = channel,
            canal_proveedor = channel_provider,
            cuenta_canal = channel_account,
            hablante = hablante,
            id_contacto = id_contact,
            cuenta_contacto = contact_account,
            tipo_operador = operator_type,
            id_operador = id_operator,
            tipo_mensaje = tipo_mensaje,
            mensaje = mensaje,
            mensaje_recibido = recibido,
            mensaje_visto = recibido,
            id_file = id_file,
            intencion = intencion,
            datatime = datetime.now(),
            accion_hablante = str(accion_hablante)
        )
        with switch_db(InteraccionLog, user_db):  
            interaccion.save()
            id_interaccion = str(interaccion.id)
        return id_interaccion



class TextMessageChatWeb(Resource):
    @Auth.authenticate    
    @dbAccess.mongoEngineAccess
    def post(self):
        ChatWebParser = reqparse.RequestParser()
        ChatWebParser.add_argument('idCampaign', type=str, required=True, location='json', help="...")
        ChatWebParser.add_argument('idContact', type=str, required=True, location='json', help="...")
        ChatWebParser.add_argument('idConversation', type=str, default=None, required=False, location='json', help="...")
        ChatWebParser.add_argument('message', type=str, required=True, location='json', help="...")
        #ChatWebParser.add_argument('idCuentaCanal', type=str, required=True, location='json', help="...")
        ChatWebParser.add_argument('idInteraction', type=str, required=True, location='json', help="...")
        ChatWebParser.add_argument('actionContacto', type=str, required=True, location='json', help="...")
        ChatWebParser.add_argument('commandToBot', type=str, required=True, location='json', help="...")
        
        Data = ChatWebParser.parse_args()
        IdCampaign = Data['idCampaign']
        IdContact = Data["idContact"]
        IdConversation = Data["idConversation"]
        Message = Data["message"]
        IdInteraction=Data["idInteraction"]
        #IdCuentaCanal = Data["idCuentaCanal"]
        ActionContacto = Data["actionContacto"]
        CommandToBot = Data["commandToBot"]
        with switch_db(CampaignLog, session["dbMongoEngine"]):  
            try:
                campaign = CampaignLog.objects.get(id=ObjectId(IdCampaign))
            except CampaignLog.DoesNotExist:
                return {'message':'Campaign not found'}, 404

        CampaignName = campaign["nombre_camp"]
        CampaignType = campaign["tipo_camp"]
        IdCampaign = str(campaign["id"])
        ChannelAccount = campaign["id_cuenta_canal"]
        Operator = campaign["operadores"]
        OperatorType = Operator["tipo_operador"]
        OperatorId = Operator["id_operador"]
        if IdConversation is None:
            Parametros = {}
            Parametros['channel_account'] = ChannelAccount
            Parametros["channel_settings"] = None
            Parametros["id_contact"] = IdContact
            Parametros["contact_details"] = [],
            Parametros["contact_account"] = IdContact
            Parametros["channel"] = "chatweb"
            
            IdConversation = conversacion_log(session["dbMongoEngine"], Parametros,
                                              CampaignName, CampaignType, IdCampaign, OperatorType, OperatorId)
        
        
           #contactando con bot
            BotResponse = call_bot(session["token"], IdInteraction, "chatweb", ChannelAccount,
                                   OperatorId, IdContact, IdContact, [], IdCampaign, CampaignName,
                                   CampaignType, IdConversation, None, "text", Message, "", ActionContacto,
                                   CommandToBot)

            #interacion de contacto
            # IdInteractionContact = interaccion_log(session["dbMongoEngine"], IdConversation, None, "contact", CampaignName,
            #                 CampaignType, IdCampaign, "chatweb", None, IdContact, IdContact,
            #                 OperatorType, OperatorId, "text", Message, "", BotResponse["accion_contacto"],
            #                 BotResponse["metadata_bot"]["intencionContacto"], True )  
            #interaccion de bot
            IdInteractionBot = interaccion_log(session["dbMongoEngine"], IdConversation, None, "bot", CampaignName, CampaignType,
                            IdCampaign, "chatweb", None, IdContact, IdContact, OperatorType, OperatorId, "text",
                            BotResponse["mensaje_bot"], "", BotResponse["accion_contacto"],
                            BotResponse["metadata_bot"]["intencionBot"], True )  
            
            BotResponse["id_conversacion"] = IdConversation #se añade id de conversacion a la respuesta
            BotResponse["id_campaña"] = IdCampaign #se añade id de conversacion a la respuesta
            BotResponse["id_interaction_Contact"]=""
            BotResponse["id_interaction_Bot"]=IdInteractionBot
        else:
            #contactando con bot
            BotResponse = call_bot(session["token"], IdInteraction, "chatweb", ChannelAccount,
                                   OperatorId, IdContact, IdContact, [], IdCampaign, CampaignName,
                                   CampaignType, IdConversation, None, "text", Message, "", ActionContacto,
                                   CommandToBot)

            #interacion de contacto
            IdInteractionContact = interaccion_log(session["dbMongoEngine"], IdConversation, None, "contact", CampaignName,
                            CampaignType, IdCampaign, "chatweb", None, IdContact, IdContact,
                            OperatorType, OperatorId, "text", Message, "", BotResponse["accion_contacto"],
                            BotResponse["metadata_bot"]["intencionContacto"], True )  
            #interaccion de bot
            IdInteractionBot = interaccion_log(session["dbMongoEngine"], IdConversation, None, "bot", CampaignName, CampaignType,
                            IdCampaign, "chatweb", None, IdContact, IdContact, OperatorType, OperatorId, "text",
                            BotResponse["mensaje_bot"], "", BotResponse["accion_contacto"],
                            BotResponse["metadata_bot"]["intencionBot"], True )  
            
            BotResponse["id_conversacion"] = IdConversation #se añade id de conversacion a la respuesta
            BotResponse["id_campaña"] = IdCampaign #se añade id de conversacion a la respuesta
            BotResponse["id_interaction_Contact"]=IdInteractionContact
            BotResponse["id_interaction_Bot"]=IdInteractionBot

            
            

        return BotResponse
                
                
    



        
        




        
