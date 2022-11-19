import os
import socket
from flask import Flask

app = Flask(__name__)

app.config['JSON_SORT_KEYS'] = False
app.config['JSON_AS_ASCII']  = False
default_datetime_format = '%Y-%m-%d %H:%M:%S'

#!Configuracion para keycloak y database
app.secret_key =""+str(os.urandom(12))


#!CONFIGURACIONES PARA API CHANNEL WHATSAPP

app.config['API_MENSAJES_WHATSAPP_ENDPOINT'] = os.environ.get("DNS_API_WHATSAPP")+"/canal/chat/whatsapp/message"
app.config['API_BOT_TALK_ENDPOINT']     = os.environ.get("DNS_API_BOTS")+"/bots/talk"
#FIXME No puede haber ninguna llamada directa a wassi.
app.config['API_WASSI_SEND_MESSAGE']    =  os.environ.get("API_WASSI_SEND_MESSAGE")

app.config['DNS_API_WHATSAPP'] = os.environ.get("DNS_API_WHATSAPP")
app.config['DNS_API_WHATSAPP_GUPSHUP'] = os.environ.get("DNS_API_WHATSAPP_GUPSHUP")
app.config['DNS_API_CHATWEB'] = os.environ.get("DNS_API_CHATWEB")
app.config['DNS_API_AGENTS'] = os.environ.get("DNS_AGENTS_API")+"/message"
app.config['DNS_API_AGENTS2'] = os.environ.get("DNS_AGENTS_API")
app.config['DNS_API_BOTS']=os.environ.get("DNS_API_BOTS")
app.config['DNS_API_TEXT']=os.environ.get("DNS_API_TEXT")
app.config['DNS_API_MESSENGER']=os.environ.get("DNS_API_MESSENGER")

#!CONFIG SENTRY.IO
app.config['SENTRY_DSN'] = os.environ['SENTRY_DSN']
app.config['SENTRY_ENV'] = os.environ['SENTRY_ENV']
app.config['SENTRY_TRACE_RATE'] = float(os.environ['SENTRY_TRACE_RATE'])
