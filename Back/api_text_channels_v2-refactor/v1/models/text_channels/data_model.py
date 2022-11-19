#from importlib_metadata import requires
from mongoengine import DynamicDocument
from mongoengine import DateTimeField, StringField, ListField, DictField, ObjectIdField, IntField, DecimalField, ImageField,BooleanField
#import PIL

class Users(DynamicDocument):
    meta = {'collection': 'users'}

class CampaignLog(DynamicDocument):
    meta = {'collection': 'campaign_log'}

class CampaignLists(DynamicDocument):
    meta = {'collection': 'campaign_lists'}

class CampaignConfigModel(DynamicDocument):
    meta = {'collection': 'campaign_config'}

class Devices(DynamicDocument):
    meta = {'collection': 'devices'}

class ConversacionLog(DynamicDocument):
    meta = {'collection': 'conversaciones_log',
            'strict': False,            #Este parametro indica si a la coleccion se le pueden agregar o no campos nuevos de forma externa
            'auto_create_index': False, #Deshabilita la creacion de indices por defecto a todos los campos
            "index_background": True,   #Crea indices en segundo plano. Crear indices en primer plano genera problemas de rendimiento.
            'indexes': [{'fields': ['canal', 'canal_cuenta', 'contacto_cuenta', 'nombre_campana', 'tipo_campana','id_contacto', 'id_operador', 
                                    'tipo_operador', 'estado_comunicacion', 'estado_campana'],
                         'name':'conversacionLog',
                         'unique': False}]
            }                  
    canal = StringField(required=True)
    canal_proveedor = StringField(required=True)
    canal_cuenta = StringField(required=True)
    contacto_cuenta = StringField(required=True)
    canal_config = DictField()
    nombre_campana = StringField(required=True)
    tipo_campana = StringField()
    id_campana = StringField(required=True)
    id_contacto = StringField()
    tipo_operador = StringField()
    id_operador = StringField()
    datatime = DateTimeField()
    datatime_fin = DateTimeField()
    duracion = DecimalField()
    duracion_conversacion = DecimalField()
    registros_canal = StringField() #parametros exclusivos del canal (no genericos. Ej:perfil, stt, avatar, etc.)
    estado_campana = StringField()
    estado_comunicacion = StringField()
    estados_comunicacion_historial = ListField(DictField())
    disposicion_canal = StringField()
    conversation_finished = BooleanField(default=False)
    

class InteraccionLog(DynamicDocument):
    meta = {'collection': 'interacciones_log',
            'strict': False,            #Este parametro indica si a la coleccion se le pueden agregar o no campos nuevos de forma externa
            'auto_create_index': False, #Deshabilita la creacion de indices por defecto a todos los campos
            "index_background": True,   #Crea indices en segundo plano. Crear indices en primer plano genera problemas de rendimiento.
            'indexes': [{'fields': ['id_conversacion', 'id_interaccion', 'id_campana', 'nombre_campana', 'id_operador', 'tipo_operador', 
                                    'hablante', 'mensaje', 'tipo_mensaje','accion_hablante', 'canal', 'canal_cuenta','id_contacto'],
                         'name':'interaccionLog',
                         'unique': False}]
            }                  


    id_conversacion = StringField()
    id_interaccion = StringField()
    nombre_campana = StringField()
    id_campana = StringField()
    tipo_campana = StringField()
    id_campana = StringField()
    canal = StringField()
    canal_proveedor = StringField()
    canal_cuenta = StringField()
    hablante = StringField()
    id_contacto = StringField()
    cuenta_contacto =StringField()
    tipo_operador = StringField()
    id_operador = StringField()
    tipo_mensaje = StringField()
    mensaje = StringField()
    id_file = StringField()
    intencion = StringField()
    datatime = DateTimeField()
    duracion = DecimalField()
    id_grabacion = StringField()
    registros_canal = StringField()
    accion_hablante = StringField()
    mensaje_recibido=BooleanField()
    mensaje_recibido=BooleanField()
    mensaje_visto=BooleanField()


class FileLog(DynamicDocument):
    meta = {'collection': 'file_log'}

    #file_data = FileField()         # Datos del Archivo
    extention_data = StringField()  # Extención .png, etc.
    nombre_data = StringField()
    nombre_campana = StringField()  # Campaña que requiere el archivo 
    id_campana = StringField()
    id_interaccion = StringField()  # Interacción donde se subió el archivo
    id_conversation = StringField()
    operator = StringField()
    id_contact = StringField()
    