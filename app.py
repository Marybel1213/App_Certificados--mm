"""Punto de entrada de la aplicación web 'App de Certificados de la Academia'.

Inicializa la aplicación Flask, registra los controladores e inicializa
la base de datos con los datos necesarios.
"""

import os
from pathlib import Path
from flask import Flask, flash, redirect, url_for
from controllers.tablero import tablero_bp
from controllers.certificados import certificados_bp
from controllers.auth import auth_bp
from controllers.cargar import cargar_bp
from models.datos import asegurar_tablas_y_datos

# LADRILLO: VARIABLE con la carpeta del proyecto según la ubicación de este
# archivo (tipo Path). Así las rutas funcionan sin importar desde dónde se
# ejecute la app (doble clic, consola, o servidor como Vercel).
BASE_DIR = Path(__file__).resolve().parent

# Inicialización de la aplicación Flask respetando la arquitectura MVC
app = Flask(__name__, template_folder=str(BASE_DIR / "views"), static_folder=str(BASE_DIR / "static"))
# La clave secreta firma la cookie de sesión (login). En producción se lee de
# la variable SECRET_KEY; el valor de respaldo es solo para pruebas locales.
app.secret_key = os.getenv("SECRET_KEY") or "clave-de-demostracion-cambiar-en-produccion"

# Tope de tamaño de la petición completa: 4 MB. Vercel rechaza las peticiones
# de más de 4.5 MB, así que nos quedamos por debajo con margen.
app.config["MAX_CONTENT_LENGTH"] = 4 * 1024 * 1024

# Registro de Blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(tablero_bp)
app.register_blueprint(certificados_bp)
app.register_blueprint(cargar_bp)


@app.errorhandler(413)
def archivo_demasiado_grande(error):
    """Aviso amable cuando la subida supera el tope de 4 MB."""
    flash(
        "El archivo es demasiado grande: el límite es 4 MB por envío. "
        "Reduzca el Excel o divídalo en partes.",
        "error",
    )
    return redirect(url_for("tablero.index"))

# Asegurar creación de tablas y auto-carga de datos al inicio
try:
    asegurar_tablas_y_datos()
except Exception as err:
    app.logger.error(f"Error al inicializar la base de datos o cargar datos: {err}")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
