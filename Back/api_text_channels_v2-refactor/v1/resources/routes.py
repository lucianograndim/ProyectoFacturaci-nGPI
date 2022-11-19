from .text_channels.text_messages import TextMessage, TextMessageChatWeb, HealthCheck
#from .text_channels.files_upload import FileUpload

def initialize_routes(api):
    #!Enviar y recibir mensajes
    # Enpoint para api de mensajeria. Recibe y envia mensajes entre canal y bot.
    api.add_resource(TextMessage, '/channel/text_channels/message', endpoint='auth:api_text_channels:send_mge', methods=['POST','GET'])
    api.add_resource(TextMessageChatWeb, '/channel/text_channels/chatWebMessage', endpoint='auth:api_text_channels:send_mge_chatweb', methods=['POST','GET'])
    api.add_resource(HealthCheck, '/healthcheck', methods=['GET'])
    #api.add_resource(FileUpload, '/channel/file_upload/upload', methods=['POST'])
    