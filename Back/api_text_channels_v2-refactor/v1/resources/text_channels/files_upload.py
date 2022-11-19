from flask_restful import Resource, reqparse
from v1.resources.auth.authorization import Auth
from v1.resources.auth.dbDecorator import dbAccess
from v1.models.text_channels.data_model import FileLog
import werkzeug.datastructures

parametros_input = reqparse.RequestParser()
parametros_input.add_argument('nombre_data', type=str, required=True, location='json', help="...")
parametros_input.add_argument('extention_data', type=str, required=True, location='json', help="...")
parametros_input.add_argument('nombre_campana', type=str, required=True, location='json', help="...")
parametros_input.add_argument('id_campana', type=str, required=True, location='json', help="...")
parametros_input.add_argument('id_interaccion', type=str, required=True, location='json', help="...")
parametros_input.add_argument('id_conversation', type=str, required=False,  location='json', help="...")
parametros_input.add_argument('operator', type=dict, required=False,  location='json', help="...")
parametros_input.add_argument('id_contact', type=str, required=True,  location='json', help="...")
parametros_input.add_argument('file', type=werkzeug.datastructures.FileStorage, location='files')
    

class FilesUpload(Resource):
    @Auth.authenticate    
    @dbAccess.mongoEngineAccess       
    def post(self):
        try:
            file = request.files['file']
            parametros = dict(parametros_input.parse_args())
            nombre = parametros['nombre_data']
            ext = parametros['extention_data']
            nombre_campana = parametros['nombre_campana']
            id_campana = parametros['id_campana']
            id_interaccion = parametros['id_interaccion']
            id_conversation = parametros['id_conversation']
            operator = parametros['operator']
            id_contact = parametros['id_contact']

            user_db = session["dbMongoEngine"]
            with switch_db(FileLog, user_db):
                
                fileLog = FileLog(nombre_data=nombre,
                                extention_data=ext,
                                nombre_campana=nombre_campana,
                                id_campana=id_campana,
                                id_interaccion=id_interaccion,
                                id_conversation=id_conversation, 
                                operator = operator,
                                id_contact = id_contact
                                )

                fileLog.file_data.put(file)
                filelog.save()
            
        except Exception as ex:
            return str(ex)
            