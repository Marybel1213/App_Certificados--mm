"""Reglas del negocio para la emisión de certificados de la Academia.

Implementa estrictamente las reglas R1 a R6 descritas en AGENTS.md.
"""

from collections import defaultdict
from typing import Any, Dict, List, Optional

from models.datos import obtener_estudiantes, obtener_evaluaciones

# Constantes fijas de negocio según AGENTS.md
NOTA_MINIMA: float = 70.0
ASISTENCIA_MINIMA: float = 80.0
ASISTENCIA_INCONSISTENCIA_LIMITE: float = 50.0


def calcular_resumen(
    estudiantes_db: Optional[List[Dict[str, Any]]] = None,
    evaluaciones_db: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """Calcula el resumen completo de certificaciones e inconsistencias.

    Los parámetros son OPCIONALES: si no se pasan, se leen de la base de datos
    (comportamiento normal de la app). Si se pasan listas, se calcula sobre
    esos datos, por ejemplo los Excel que un administrador sube en memoria.
    
    Aplica las reglas R1 a R6:
    - R1: Agrupa por identificación + programa.
    - R2: Promedio de notas y asistencia con redondeo a 2 decimales.
    - R3: Aprobación cuando promedio >= 70 y asistencia >= 80.
    - R4: Participación cuando promedio < 70 y asistencia >= 80.
    - R5: Sin certificado cuando asistencia < 80 (incluye asistencia < 50).
    - R6: Inconsistencias (además de su clasificación): estudiante sin evaluaciones, evaluaciones de estudiante
          inexistente en el maestro, o asistencia < 50%.
    
    Retorna un diccionario con:
    - totales: dict con conteos ('aprobacion', 'participacion', 'sin_certificado', 'inconsistencias')
    - lista_estudiantes: lista de diccionarios de estudiantes certificados/clasificados
    - lista_inconsistencias: lista de diccionarios de inconsistencias detectadas
    """
    estudiantes_db = estudiantes_db if estudiantes_db is not None else obtener_estudiantes()
    evaluaciones_db = evaluaciones_db if evaluaciones_db is not None else obtener_evaluaciones()

    # Mapeo del maestro de estudiantes por (identificacion, programa)
    # y conjunto de identificaciones registradas en el maestro
    maestro_map: Dict[tuple, Dict[str, Any]] = {}
    ids_maestro = set()

    for est in estudiantes_db:
        ident = str(est.get("identificacion", "")).strip()
        prog = str(est.get("programa", "")).strip()
        if ident:
            maestro_map[(ident, prog)] = est
            ids_maestro.add(ident)

    # Agrupar evaluaciones por (identificacion, programa)
    evals_por_clave: Dict[tuple, List[Dict[str, Any]]] = defaultdict(list)
    for ev in evaluaciones_db:
        ident = str(ev.get("identificacion", "")).strip()
        prog = str(ev.get("programa", "")).strip()
        if ident:
            evals_por_clave[(ident, prog)].append(ev)

    lista_estudiantes: List[Dict[str, Any]] = []
    lista_inconsistencias: List[Dict[str, Any]] = []

    # R6 Caso B: Evaluaciones de estudiante inexistente en el maestro
    for (ident, prog), evals in evals_por_clave.items():
        if (ident, prog) not in maestro_map and ident not in ids_maestro:
            notas = [float(ev["nota"]) for ev in evals if ev.get("nota") is not None]
            asists = [float(ev["asistencia_pct"]) for ev in evals if ev.get("asistencia_pct") is not None]
            prom_nota = round(sum(notas) / len(notas), 2) if notas else None
            prom_asist = round(sum(asists) / len(asists), 2) if asists else None

            lista_inconsistencias.append({
                "identificacion": ident,
                "nombre_completo": "No registrado en maestro",
                "programa": prog,
                "motivo": "Evaluación sin registro en el maestro",
                "descripcion": (
                    f"La identificación {ident} tiene evaluaciones en '{prog}', "
                    f"pero no existe en el maestro de estudiantes."
                ),
                "promedio_nota": prom_nota,
                "promedio_asistencia": prom_asist,
            })

    # Procesar estudiantes del maestro
    for (ident, prog), est in maestro_map.items():
        evals = evals_por_clave.get((ident, prog), [])

        # R6 Caso A: Estudiante del maestro sin evaluaciones
        if not evals:
            lista_inconsistencias.append({
                "identificacion": ident,
                "nombre_completo": est.get("nombre_completo") or "Sin nombre",
                "programa": prog,
                "motivo": "Estudiante sin evaluaciones",
                "descripcion": (
                    f"El estudiante {est.get('nombre_completo', '')} ({ident}) está en el maestro "
                    f"pero no tiene ninguna evaluación registrada."
                ),
                "promedio_nota": None,
                "promedio_asistencia": None,
            })
            continue

        # R2: Cálculo de promedios con redondeo a 2 decimales
        notas = [float(ev["nota"]) for ev in evals if ev.get("nota") is not None]
        asists = [float(ev["asistencia_pct"]) for ev in evals if ev.get("asistencia_pct") is not None]

        prom_nota = round(sum(notas) / len(notas), 2) if notas else 0.0
        prom_asist = round(sum(asists) / len(asists), 2) if asists else 0.0

        # LADRILLO: CONDICIONAL de alerta R6 Caso C: asistencia menor a 50%.
        # OJO: es solo una alerta, NO salta la clasificación: el estudiante
        # igual se clasifica abajo (caerá en "Sin certificado" por R5).
        if prom_asist < ASISTENCIA_INCONSISTENCIA_LIMITE:
            lista_inconsistencias.append({
                "identificacion": ident,
                "nombre_completo": est.get("nombre_completo") or "Sin nombre",
                "programa": prog,
                "motivo": f"Asistencia crítica ({prom_asist}%)",
                "descripcion": (
                    f"El estudiante {est.get('nombre_completo', '')} tiene una asistencia de "
                    f"{prom_asist}%, inferior al umbral mínimo del 50%."
                ),
                "promedio_nota": prom_nota,
                "promedio_asistencia": prom_asist,
            })

        # LADRILLO: CONDICIONALES que deciden el tipo de certificado (R3, R4, R5).
        if prom_asist >= ASISTENCIA_MINIMA and prom_nota >= NOTA_MINIMA:
            tipo_certificado = "Aprobación"
        elif prom_asist >= ASISTENCIA_MINIMA and prom_nota < NOTA_MINIMA:
            tipo_certificado = "Participación"
        else:
            tipo_certificado = "Sin certificado"

        lista_estudiantes.append({
            "identificacion": ident,
            "nombre_completo": est.get("nombre_completo") or "",
            "correo": est.get("correo") or "",
            "programa": prog,
            "cohorte": est.get("cohorte") or "",
            "promedio_nota": prom_nota,
            "promedio_asistencia": prom_asist,
            "tipo_certificado": tipo_certificado,
            "cantidad_evaluaciones": len(evals),
        })

    # Ordenar listas para presentación ordenada
    lista_estudiantes.sort(key=lambda x: (x["nombre_completo"] or x["identificacion"]).lower())
    lista_inconsistencias.sort(key=lambda x: (x["identificacion"]))

    # Conteo de totales para cifras de control
    conteo_aprobacion = sum(1 for e in lista_estudiantes if e["tipo_certificado"] == "Aprobación")
    conteo_participacion = sum(1 for e in lista_estudiantes if e["tipo_certificado"] == "Participación")
    conteo_sin_certificado = sum(1 for e in lista_estudiantes if e["tipo_certificado"] == "Sin certificado")
    conteo_inconsistencias = len(lista_inconsistencias)

    totales = {
        "aprobacion": conteo_aprobacion,
        "participacion": conteo_participacion,
        "sin_certificado": conteo_sin_certificado,
        "inconsistencias": conteo_inconsistencias,
        "total_estudiantes": len(lista_estudiantes),
    }

    return {
        "totales": totales,
        "lista_estudiantes": lista_estudiantes,
        "lista_inconsistencias": lista_inconsistencias,
    }


def obtener_estudiante_procesado(identificacion: str, programa: str) -> Optional[Dict[str, Any]]:
    """Busca un estudiante procesado por su identificación y programa.

    Las comparaciones se hacen SIEMPRE como texto: en algunas bases (por
    ejemplo PostgreSQL) la identificación puede volver como número, y la URL
    siempre la entrega como texto. Sin esta conversión, la búsqueda fallaba
    en el servidor aunque el tablero mostrara los datos.
    """
    resumen = calcular_resumen()
    ident_limpia = str(identificacion).strip()
    prog_limpio = str(programa).strip()

    for est in resumen["lista_estudiantes"]:
        # LADRILLO: CONDICIONAL con comparación de texto en ambos lados.
        est_ident = str(est.get("identificacion", "")).strip()
        est_prog = str(est.get("programa", "")).strip()
        if est_ident == ident_limpia and est_prog == prog_limpio:
            return est

    return None
