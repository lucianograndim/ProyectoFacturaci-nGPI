# FLASK_API
Para el desarrollo se recomienda instalar un entorno virtual de python [(info)](https://packaging.python.org/guides/installing-using-pip-and-virtual-environments/):
```python3
pip3 install virtualenv
```
Para crear un entorno virtual:
```python3
virtualenv nombre_del_env --python=python3
```
Ingresando al entorno virtual:

| Mac y Linux | Windows |
| ------------- | ------------- |
| source nombre_del_env/bin/activate  | ./nombre_del_env/Scripts/activate.bat  |

Una vez dentro podemos instalar las librerias necesarias:
```python3
pip3 install -r requirements.txt
```
# Para iniciar el servidor flask
 ```python3
python3 app.py
```

# Para ejecutar desde docker
 ```python3
docker-compose build
docker-compose up -d
```

# En la carpeta V1 se encuentran 3 carpetas:

- models: Van las clases, métodos, funciones que se utilizaran en los recursos.
- errors: Van los errores personalizados de los recursos.
- resources: Se agregan todos los recursos de la API y se definen los endpoints

# En la ruta principal se encuentran los archivos:

- app.py: Aplicacion principal, donde se define la ip/port del servidor flask, se configura el JWB, etc.
- db.py: Conexion para mongo y sus colecciones.
- errors.py: Definicion de errores.

# Documentación Auth

https://drive.google.com/file/d/1dqz0PhAS-ZJuBiJyRl81MowUgqgYgezO/view?usp=sharing