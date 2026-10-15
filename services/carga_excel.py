"""Servicio de lectura, validación y carga de archivos Excel hacia la base de datos."""

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import pandas as pd

from models.datos import insertar_estudiantes, insertar_evaluaciones, limpiar_tablas


COLUMNAS_MAESTRO_REQUERIDAS = [
    "Identificacion",
    "Nombre_Completo",
    "Correo",
    "Programa",
    "Cohorte",
]

COLUMNAS_EVALUACIONES_REQUERIDAS = [
    "Identificacion",
    "Programa",
    "Modulo",
    "Nota",
    "Asistencia_Pct",
    "Fecha_Cierre",
]


def buscar_ruta_insumo(nombre_archivo: str) -> Path:
    """Busca un archivo dentro del directorio INSUMOS o insumos."""
    raiz_proyecto = Path(__file__).resolve().parent.parent
    posibles_directorios = [
        raiz_proyecto / "INSUMOS",
        raiz_proyecto / "insumos",
        Path("INSUMOS"),
        Path("insumos"),
        Path("."),
    ]
    for directorio in posibles_directorios:
        ruta = directorio / nombre_archivo
        if ruta.exists():
            return ruta
    raise FileNotFoundError(f"No se encontró el archivo {nombre_archivo} en las carpetas de insumos.")


def limpiar_texto_identificacion(valor: Any) -> str:
    """Convierte la identificación en texto limpio sin espacios ni decimales flotantes."""
    if pd.isna(valor) or valor is None:
        return ""
    texto = str(valor).strip()
    if texto.endswith(".0"):
        texto = texto[:-2]
    return texto.strip()


def limpiar_fecha(valor: Any):
    """Convierte un valor de fecha a un objeto date estándar o None si es inválido/nulo."""
    if pd.isna(valor) or valor is None:
        return None
    try:
        dt = pd.to_datetime(valor, errors="coerce")
        if pd.isna(dt):
            return None
        return dt.date()
    except Exception:
        return None


def leer_y_validar_maestro(ruta_archivo: Path | str) -> List[Dict[str, Any]]:
    """Lee y valida el archivo Excel Maestro_Estudiantes.xlsx."""
    ruta = Path(ruta_archivo)
    if not ruta.exists():
        raise FileNotFoundError(f"El archivo maestro no existe: {ruta}")

    # Leemos la hoja 'Estudiantes' asegurando Identificacion como string
    df = pd.read_excel(ruta, sheet_name="Estudiantes", dtype={"Identificacion": str})

    # Validar columnas
    columnas_faltantes = [col for col in COLUMNAS_MAESTRO_REQUERIDAS if col not in df.columns]
    if columnas_faltantes:
        raise ValueError(f"El archivo maestro carece de las siguientes columnas requeridas: {columnas_faltantes}")

    estudiantes: List[Dict[str, Any]] = []
    for _, fila in df.iterrows():
        identificacion = limpiar_texto_identificacion(fila.get("Identificacion"))
        if not identificacion:
            continue  # Ignorar filas vacías

        estudiantes.append({
            "identificacion": identificacion,
            "nombre_completo": str(fila.get("Nombre_Completo", "")).strip() if pd.notna(fila.get("Nombre_Completo")) else None,
            "correo": str(fila.get("Correo", "")).strip() if pd.notna(fila.get("Correo")) else None,
            "programa": str(fila.get("Programa", "")).strip() if pd.notna(fila.get("Programa")) else None,
            "cohorte": str(fila.get("Cohorte", "")).strip() if pd.notna(fila.get("Cohorte")) else None,
        })

    return estudiantes


def leer_y_validar_evaluaciones(ruta_archivo: Path | str) -> List[Dict[str, Any]]:
    """Lee y valida el archivo Excel Registro_Evaluaciones.xlsx."""
    ruta = Path(ruta_archivo)
    if not ruta.exists():
        raise FileNotFoundError(f"El archivo de evaluaciones no existe: {ruta}")

    # Leemos la hoja 'Evaluaciones' asegurando Identificacion como string
    df = pd.read_excel(ruta, sheet_name="Evaluaciones", dtype={"Identificacion": str})

    # Validar columnas
    columnas_faltantes = [col for col in COLUMNAS_EVALUACIONES_REQUERIDAS if col not in df.columns]
    if columnas_faltantes:
        raise ValueError(f"El archivo de evaluaciones carece de las columnas: {columnas_faltantes}")

    evaluaciones: List[Dict[str, Any]] = []
    for _, fila in df.iterrows():
        identificacion = limpiar_texto_identificacion(fila.get("Identificacion"))
        if not identificacion:
            continue  # Ignorar filas vacías

        nota = fila.get("Nota")
        nota_val = float(nota) if pd.notna(nota) else None

        asistencia = fila.get("Asistencia_Pct")
        asistencia_val = float(asistencia) if pd.notna(asistencia) else None

        fecha_val = limpiar_fecha(fila.get("Fecha_Cierre"))

        evaluaciones.append({
            "identificacion": identificacion,
            "programa": str(fila.get("Programa", "")).strip() if pd.notna(fila.get("Programa")) else None,
            "modulo": str(fila.get("Modulo", "")).strip() if pd.notna(fila.get("Modulo")) else None,
            "nota": nota_val,
            "asistencia_pct": asistencia_val,
            "fecha_cierre": fecha_val,
        })

    return evaluaciones


def procesar_y_cargar_datos(
    ruta_maestro: Optional[Path | str] = None,
    ruta_evaluaciones: Optional[Path | str] = None,
) -> Tuple[int, int]:
    """Carga los datos de ambos Excel en la base de datos Supabase, reemplazando los existentes.
    
    Retorna una tupla con (conteo_estudiantes, conteo_evaluaciones).
    """
    if ruta_maestro is None:
        ruta_maestro = buscar_ruta_insumo("Maestro_Estudiantes.xlsx")
    if ruta_evaluaciones is None:
        ruta_evaluaciones = buscar_ruta_insumo("Registro_Evaluaciones.xlsx")

    # 1. Leer y validar en memoria
    estudiantes = leer_y_validar_maestro(ruta_maestro)
    evaluaciones = leer_y_validar_evaluaciones(ruta_evaluaciones)

    # 2. Limpiar tablas existentes en base de datos
    limpiar_tablas()

    # 3. Insertar registros limpios
    insertar_estudiantes(estudiantes)
    insertar_evaluaciones(evaluaciones)

    return len(estudiantes), len(evaluaciones)
