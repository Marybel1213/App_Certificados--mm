"""Punto de entrada de la aplicación web 'App de Certificados de la Academia'.

Inicializa la aplicación Flask, registra los controladores e inicializa
la base de datos con los datos necesarios.
"""

import os
from pathlib import Path
from flask import Flask
from controllers.tablero import tablero_bp
from controllers.certificados import certificados_bp
from models.datos import asegurar_tablas_y_datos

# LADRILLO: VARIABLE con la carpeta del proyecto según la ubicación de este
# archivo (tipo Path). Así las rutas funcionan sin importar desde dónde se
# ejecute la app (doble clic, consola, o servidor como Vercel).
BASE_DIR = Path(__file__).resolve().parent

# Inicialización de la aplicación Flask respetando la arquitectura MVC
app = Flask(__name__, template_folder=str(BASE_DIR / "views"), static_folder=str(BASE_DIR / "static"))
app.secret_key = os.getenv("SECRET_KEY", "academia_certificados_secret_key_2026")

# Registro de Blueprints
app.register_blueprint(tablero_bp)
app.register_blueprint(certificados_bp)

# Asegurar creación de tablas y auto-carga de datos al inicio
try:
    asegurar_tablas_y_datos()
except Exception as err:
    app.logger.error(f"Error al inicializar la base de datos o cargar datos: {err}")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
