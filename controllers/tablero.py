"""Controlador del Tablero Principal de Certificados.

Orquesta la visualización del resumen de estudiantes, cifras de control
e inconsistencias detectadas. No realiza cálculos de reglas de negocio directamente.
"""

from flask import Blueprint, render_template, request, session

from controllers.auth import requiere_login
from models.certificados import calcular_resumen

tablero_bp = Blueprint("tablero", __name__)

# Texto que se muestra en el panel de administrador cuando los datos
# provienen de los Excel de la carpeta INSUMOS.
ORIGEN_FABRICA = "Datos de fábrica (carpeta INSUMOS)"


def construir_contexto(
    resumen: dict,
    programa_sel: str = "",
    origen_datos: str = ORIGEN_FABRICA,
    datos_subidos: bool = False,
) -> dict:
    """Prepara los datos que recibe la plantilla del tablero.

    Lo usan tanto la ruta normal (datos de fábrica) como la carga de Excel,
    para no repetir el armado de la vista en dos lugares.
    """
    # LADRILLO: VARIABLES con las tres listas del resumen.
    totales = resumen["totales"]
    lista_estudiantes = resumen["lista_estudiantes"]
    lista_inconsistencias = resumen["lista_inconsistencias"]

    # LADRILLO: CONDICIONAL. Solo el rol "admin" recibe los datos de
    # inconsistencias. Al usuario normal no se le envían ni en el HTML.
    if session.get("rol") != "admin":
        lista_inconsistencias = []

    # LADRILLO: VARIABLE lista con los programas para el desplegable.
    programas = sorted({e["programa"] for e in lista_estudiantes if e.get("programa")})

    # LADRILLO: CONDICIONAL + BUCLE que filtran solo la tabla.
    if programa_sel:
        lista_estudiantes = [e for e in lista_estudiantes if e.get("programa") == programa_sel]

    return {
        "totales": totales,
        "lista_estudiantes": lista_estudiantes,
        "estudiantes": lista_estudiantes,
        "lista_inconsistencias": lista_inconsistencias,
        "inconsistencias": lista_inconsistencias,
        "programas": programas,
        "programa_sel": programa_sel,
        "origen_datos": origen_datos,
        "datos_subidos": datos_subidos,
    }


@tablero_bp.route("/")
@requiere_login
def index():
    """Ruta principal: muestra el tablero con estudiantes e inconsistencias."""
    resumen = calcular_resumen()

    # LADRILLO: VARIABLE con el programa elegido en el filtro (?programa=...).
    programa_sel = (request.args.get("programa") or "").strip()

    return render_template(
        "tablero.html",
        **construir_contexto(resumen, programa_sel=programa_sel),
    )
