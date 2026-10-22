"""Servicio que arma un archivo Excel con los resultados, todo en memoria.

No calcula reglas de negocio: recibe el resumen que ya calculó
models/certificados.py y solo lo da formato de hoja de cálculo.
"""

import io

import pandas as pd


def generar_excel_resultados(resumen: dict) -> bytes:
    """Devuelve los bytes de un .xlsx con resumen, resultados e inconsistencias."""
    # LADRILLO: VARIABLES diccionario con los datos ya calculados.
    totales = resumen.get("totales", {})
    estudiantes = resumen.get("lista_estudiantes", [])
    inconsistencias = resumen.get("lista_inconsistencias", [])

    # Hoja 1: contadores generales.
    df_resumen = pd.DataFrame([
        {"Indicador": "Certificados de Aprobación", "Cantidad": totales.get("aprobacion", 0)},
        {"Indicador": "Certificados de Participación", "Cantidad": totales.get("participacion", 0)},
        {"Indicador": "Sin derecho a certificado", "Cantidad": totales.get("sin_certificado", 0)},
        {"Indicador": "Inconsistencias detectadas", "Cantidad": totales.get("inconsistencias", 0)},
        {"Indicador": "Total de estudiantes certificables", "Cantidad": totales.get("total_estudiantes", 0)},
    ])

    # Hoja 2: una fila por estudiante.
    # LADRILLO: BUCLE que convierte cada diccionario en una fila.
    df_estudiantes = pd.DataFrame([
        {
            "Identificación": e.get("identificacion", ""),
            "Nombre completo": e.get("nombre_completo", ""),
            "Correo": e.get("correo", ""),
            "Programa": e.get("programa", ""),
            "Cohorte": e.get("cohorte", ""),
            "Módulos cursados": e.get("cantidad_evaluaciones", 0),
            "Promedio": e.get("promedio_nota", 0),
            "Asistencia (%)": e.get("promedio_asistencia", 0),
            "Certificado": e.get("tipo_certificado", ""),
        }
        for e in estudiantes
    ])

    # Hoja 3: una fila por inconsistencia.
    df_inconsistencias = pd.DataFrame([
        {
            "Identificación": i.get("identificacion", ""),
            "Nombre completo": i.get("nombre_completo", ""),
            "Programa": i.get("programa", ""),
            "Motivo": i.get("motivo", ""),
            "Descripción": i.get("descripcion", ""),
            "Promedio": i.get("promedio_nota"),
            "Asistencia (%)": i.get("promedio_asistencia"),
        }
        for i in inconsistencias
    ])

    # LADRILLO: BytesIO es la "caja" en memoria donde pandas escribe el Excel.
    buffer = io.BytesIO()

    # LADRILLO: BUCLE de escritura de las tres hojas en el mismo archivo.
    with pd.ExcelWriter(buffer, engine="openpyxl") as escritor:
        df_resumen.to_excel(escritor, sheet_name="Resumen", index=False)
        df_estudiantes.to_excel(escritor, sheet_name="Resultados", index=False)
        df_inconsistencias.to_excel(escritor, sheet_name="Inconsistencias", index=False)

    return buffer.getvalue()
