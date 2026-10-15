"""Controlador del Tablero Principal de Certificados.

Orquesta la visualización del resumen de estudiantes, cifras de control
e inconsistencias detectadas. No realiza cálculos de reglas de negocio directamente.
"""

from flask import Blueprint, render_template, request
from models.certificados import calcular_resumen

tablero_bp = Blueprint("tablero", __name__)


@tablero_bp.route("/")
def index():
    """Ruta principal: Muestra el tablero con los estudiantes clasificados e inconsistencias."""
    resumen = calcular_resumen()

    totales = resumen["totales"]
    lista_estudiantes = resumen["lista_estudiantes"]
    lista_inconsistencias = resumen["lista_inconsistencias"]

    # LADRILLO: VARIABLE con el programa elegido en el filtro (?programa=...).
    programa_sel = (request.args.get("programa") or "").strip()
    # LADRILLO: lista de programas existentes para el desplegable.
    programas = sorted({e["programa"] for e in lista_estudiantes if e.get("programa")})
    # LADRILLO: CONDICIONAL + BUCLE que filtra solo la tabla (los contadores siguen globales).
    if programa_sel:
        lista_estudiantes = [e for e in lista_estudiantes if e.get("programa") == programa_sel]

    return render_template(
        "tablero.html",
        totales=totales,
        lista_estudiantes=lista_estudiantes,
        estudiantes=lista_estudiantes,
        lista_inconsistencias=lista_inconsistencias,
        inconsistencias=lista_inconsistencias,
        programas=programas,
        programa_sel=programa_sel,
    )
