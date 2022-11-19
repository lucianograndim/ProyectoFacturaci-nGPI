from flask import Flask, jsonify
from flask_restful import Api
from flask_jwt_extended import JWTManager
from flask_mongoengine import MongoEngine

from errors import CUSTOM_ERRORS
from config import app


# Flask restful con errores personalizados
api = Api(app, errors=CUSTOM_ERRORS)

# Propiedades del JWB
jwt = JWTManager(app)

@jwt.user_claims_loader
def add_claims_to_jwt(identity):
    return identity

@jwt.expired_token_loader
def expired_token_callback():
    return jsonify({
        'message': 'El token ha expirado.',
        'error': 'token_expired'
    }), 401

# Importando las rutas (endpoints)
from v1.resources.routes import initialize_routes
initialize_routes(api)

# Importando la base de datos.
# import db
db = MongoEngine(app)

if __name__ == '__main__':
    app.run(host='0.0.0.0',port=5050, debug=True)
    