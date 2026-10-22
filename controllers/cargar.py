"""Controlador del panel de administrador: subir Excel y exportar resultados.

Solo orquesta: valida los archivos, los lee en memoria con el servicio,
reutiliza el cálculo de models/certificados.py y entrega la vista o el Excel.
"""

import io

from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    send_file,
    url_for,
)

from controllers.auth import solo_admin
from controllers.tablero import construir_contexto
from models.certificados import calcular_resumen
from services.carga_excel import leer_desde_memoria
from services.exportador_excel import generar_excel_resultados

cargar_bp = Blueprint("cargar", __name__)

# LADRILLO: CONSTANTE con el límite de 4 MB por archivo (Vercel corta en 4.5 MB).
MAX_BYTES = 4 * 1024 * 1024
EXTENSION_VALIDA = ".xlsx"
TIPO_EXCEL = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def _tamano_en_bytes(archivo) -> int:
    """Mide el archivo en memoria sin gastar disco."""
    archivo.stream.seek(0, io.SEEK_END)
    tamano = archivo.stream.tell()
    archivo.stream.seek(0)
    return tamano


def _validar_archivo(archivo, etiqueta: str):
    """Devuelve un mensaje de error entendible, o None si el archivo sirve."""
    # LADRILLO: CONDICIONAL. Falta el archivo o viene vacío.
    if archivo is None or not archivo.filename:
        return f"Falta el archivo de {etiqueta}. Seleccione los dos archivos Excel."

    # LADRILLO: CONDICIONAL. Debe ser un Excel moderno (.xlsx).
    if not archivo.filename.lower().endswith(EXTENSION_VALIDA):
        return f"El archivo de {etiqueta} debe ser un Excel con extensión .xlsx."

    # LADRILLO: CONDICIONAL. Tope de 4 MB por archivo.
    if _tamano_en_bytes(archivo) > MAX_BYTES:
        return f"El archivo de {etiqueta} pesa más de 4 MB. Divídalo o reduzca los datos."

    return None


def _tablero_con_datos_de_fabrica():
    """Vuelve a mostrar el tablero normal (datos de INSUMOS)."""
    return render_template(
        "tablero.html",
        **construir_contexto(calcular_resumen()),
    )


@cargar_bp.route("/cargar", methods=["GET", "POST"])
@solo_admin
def cargar():
    """Atiende el panel: en GET vuelve al tablero; en POST procesa los Excel."""
    # LADRILLO: CONDICIONAL. El formulario vive en el tablero; aquí solo se envía.
    if request.method == "GET":
        return redirect(url_for("tablero.index"))

    # LADRILLO: VARIABLES con lo que eligió la persona en el panel.
    accion = request.form.get("accion") or "ver"
    archivo_maestro = request.files.get("archivo_maestro")
    archivo_evaluaciones = request.files.get("archivo_evaluaciones")

    # LADRILLO: BUCLE que valida los dos archivos con el mismo criterio.
    for archivo, etiqueta in (
        (archivo_maestro, "maestro de estudiantes"),
        (archivo_evaluaciones, "registro de evaluaciones"),
    ):
        problema = _validar_archivo(archivo, etiqueta)
        # LADRILLO: CONDICIONAL. Si hay problema, avisamos en rojo y no seguimos.
        if problema:
            flash(problema, "error")
            return _tablero_con_datos_de_fabrica()

    try:
        # LADRILLO: leemos los bytes de cada archivo (nada se guarda en disco).
        contenido_maestro = archivo_maestro.read()
        contenido_evaluaciones = archivo_evaluaciones.read()

        # LADRILLO: el servicio envuelve esos bytes en BytesIO y los lee con pandas.
        estudiantes, evaluaciones = leer_desde_memoria(
            contenido_maestro, contenido_evaluaciones
        )

        # LADRILLO: reutilizamos el MISMO cálculo de la app, sin base de datos.
        resumen = calcular_resumen(estudiantes, evaluaciones)

    except Exception:
        # LADRILLO: CONDICIONAL de error. Nunca dejamos la página en blanco.
        flash(
            "No pudimos leer uno de los Excel. Verifique que el maestro tenga la "
            "hoja 'Estudiantes' y el registro la hoja 'Evaluaciones', con sus columnas.",
            "error",
        )
        return _tablero_con_datos_de_fabrica()

    # LADRILLO: texto que muestra de dónde salieron los datos en pantalla.
    origen = (
        f"Archivos subidos: {archivo_maestro.filename} y {archivo_evaluaciones.filename}"
    )

    # LADRILLO: CONDICIONAL. Según el botón, mostramos la tabla o bajamos Excel.
    if accion == "excel":
        datos_excel = generar_excel_resultados(resumen)
        return send_file(
            io.BytesIO(datos_excel),
            mimetype=TIPO_EXCEL,
            download_name="resultados_certificados.xlsx",
            as_attachment=True,
        )

    return render_template(
        "tablero.html",
        **construir_contexto(
            resumen,
            origen_datos=origen,
            datos_subidos=True,
        ),
    )


@cargar_bp.route("/descargar-resultados")
@solo_admin
def descargar_resultados():
    """Descarga un Excel con los resultados de los datos de fábrica (INSUMOS)."""
    datos_excel = generar_excel_resultados(calcular_resumen())
    return send_file(
        io.BytesIO(datos_excel),
        mimetype=TIPO_EXCEL,
        download_name="resultados_datos_fabrica.xlsx",
        as_attachment=True,
    )
