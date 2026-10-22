"""Controlador de certificados: entrega un PDF individual o un ZIP con todos.

Solo orquesta: pide los datos al modelo, llama al servicio de PDF y devuelve
el archivo. No calcula reglas de negocio ni arma el PDF aquí.
"""

import io
import unicodedata
import zipfile

from flask import Blueprint, abort, send_file

from controllers.auth import requiere_login, solo_admin
from models.certificados import calcular_resumen, obtener_estudiante_procesado
from services.generador_pdf import generar_certificado_pdf

certificados_bp = Blueprint("certificados", __name__)

# LADRILLO: CONSTANTE tupla con los únicos tipos que reciben certificado.
TIPOS_CON_CERTIFICADO = ("Aprobación", "Participación")


def _nombre_archivo(estudiante: dict) -> str:
    """Arma un nombre de archivo seguro: sin tildes, sin espacios raros."""
    nombre = f"{estudiante.get('nombre_completo', '')} {estudiante.get('identificacion', '')}"
    # LADRILLO: BUCLE sobre cada carácter para quitar tildes (normalización).
    sin_tildes = "".join(
        c for c in unicodedata.normalize("NFKD", nombre)
        if not unicodedata.combining(c)
    )
    limpio = "".join(c if c.isalnum() else "_" for c in sin_tildes).strip("_")
    return f"{limpio or 'certificado'}.pdf"


@certificados_bp.route("/certificado/<identificacion>/<path:programa>")
@requiere_login
def certificado(identificacion: str, programa: str):
    """Devuelve el PDF de un estudiante certificado."""
    # LADRILLO: VARIABLE con el estudiante ya procesado (o None si no existe).
    estudiante = obtener_estudiante_procesado(identificacion, programa)

    # LADRILLO: CONDICIONAL que corta con 404 si no corresponde acreditarlo.
    if estudiante is None:
        abort(404, description="No se encontró un estudiante con esa identificación y programa.")
    if estudiante.get("tipo_certificado") not in TIPOS_CON_CERTIFICADO:
        abort(404, description="Este estudiante no tiene derecho a certificado.")

    # LADRILLO: llamada al SERVICIO que arma el PDF.
    pdf_bytes = generar_certificado_pdf(estudiante)

    return send_file(
        io.BytesIO(pdf_bytes),
        mimetype="application/pdf",
        download_name=_nombre_archivo(estudiante),
        as_attachment=False,
    )


@certificados_bp.route("/descargar-todos")
@solo_admin
def descargar_todos():
    """Devuelve un ZIP con los certificados de Aprobación y Participación."""
    resumen = calcular_resumen()
    buffer = io.BytesIO()

    # LADRILLO: BUCLE que genera un PDF por estudiante certificado.
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archivo_zip:
        for estudiante in resumen["lista_estudiantes"]:
            # LADRILLO: CONDICIONAL que excluye a quien no tiene certificado.
            if estudiante.get("tipo_certificado") not in TIPOS_CON_CERTIFICADO:
                continue
            archivo_zip.writestr(
                _nombre_archivo(estudiante),
                generar_certificado_pdf(estudiante),
            )

    buffer.seek(0)
    return send_file(
        buffer,
        mimetype="application/zip",
        download_name="certificados_academia_horizonte.zip",
        as_attachment=True,
    )
