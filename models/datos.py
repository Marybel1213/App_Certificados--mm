"""Capa de datos: Único módulo autorizado para interactuar con la base de datos.

Soporta Supabase (PostgreSQL) cuando DATABASE_URL está definida y SQLite local
(certificados.db) como respaldo automático cuando DATABASE_URL está ausente.
"""

import contextlib
import os
import tempfile
from pathlib import Path
import sqlite3
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv

# Carga de variables de entorno desde .env
load_dotenv()
DATABASE_URL: Optional[str] = os.getenv("DATABASE_URL")
USAR_SQLITE: bool = not DATABASE_URL or not DATABASE_URL.strip()

# Ruta para la base de datos SQLite local.
# OJO Vercel: allá el disco es de solo lectura excepto /tmp, así que en la
# nube la base vive en /tmp (se recarga sola desde INSUMOS en cada arranque).
if os.getenv("VERCEL"):
    DB_PATH = Path(tempfile.gettempdir()) / "certificados.db"
else:
    DB_PATH = Path(__file__).resolve().parent.parent / "certificados.db"

# Import condicional de psycopg para PostgreSQL
if not USAR_SQLITE:
    import psycopg
    from psycopg.rows import dict_row


@contextlib.contextmanager
def get_db_connection():
    """Context manager para obtener una conexión a SQLite o PostgreSQL.
    
    Asegura el cierre adecuado de la conexión al finalizar.
    """
    if USAR_SQLITE:
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    else:
        conn = psycopg.connect(DATABASE_URL, prepare_threshold=None)
        try:
            yield conn
        finally:
            conn.close()


def crear_tablas() -> None:
    """Crea las tablas estudiantes y evaluaciones si no existen."""
    if USAR_SQLITE:
        query_estudiantes = """
        CREATE TABLE IF NOT EXISTS estudiantes (
            identificacion TEXT PRIMARY KEY,
            nombre_completo TEXT,
            correo TEXT,
            programa TEXT,
            cohorte TEXT
        );
        """
        query_evaluaciones = """
        CREATE TABLE IF NOT EXISTS evaluaciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            identificacion TEXT,
            programa TEXT,
            modulo TEXT,
            nota REAL,
            asistencia_pct REAL,
            fecha_cierre TEXT
        );
        """
    else:
        query_estudiantes = """
        CREATE TABLE IF NOT EXISTS estudiantes (
            identificacion TEXT PRIMARY KEY,
            nombre_completo TEXT,
            correo TEXT,
            programa TEXT,
            cohorte TEXT
        );
        """
        query_evaluaciones = """
        CREATE TABLE IF NOT EXISTS evaluaciones (
            id BIGSERIAL PRIMARY KEY,
            identificacion TEXT,
            programa TEXT,
            modulo TEXT,
            nota NUMERIC(5,2),
            asistencia_pct NUMERIC(5,2),
            fecha_cierre DATE
        );
        """

    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute(query_estudiantes)
        cur.execute(query_evaluaciones)
        conn.commit()


def limpiar_tablas() -> None:
    """Vacía las tablas evaluaciones y estudiantes de forma controlada."""
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM evaluaciones;")
        cur.execute("DELETE FROM estudiantes;")
        if USAR_SQLITE:
            try:
                cur.execute("DELETE FROM sqlite_sequence WHERE name = 'evaluaciones';")
            except sqlite3.OperationalError:
                pass
        else:
            cur.execute("ALTER SEQUENCE IF EXISTS evaluaciones_id_seq RESTART WITH 1;")
        conn.commit()


def insertar_estudiantes(estudiantes: List[Dict[str, Any]]) -> int:
    """Inserta una lista de estudiantes en la base de datos.
    
    Asegura que la identificación sea tratada como texto limpio sin espacios.
    """
    if not estudiantes:
        return 0

    registros_limpios = []
    for est in estudiantes:
        registros_limpios.append({
            "identificacion": str(est.get("identificacion", "")).strip(),
            "nombre_completo": (str(est.get("nombre_completo", "")).strip()
                                if est.get("nombre_completo") is not None else None),
            "correo": (str(est.get("correo", "")).strip()
                       if est.get("correo") is not None else None),
            "programa": (str(est.get("programa", "")).strip()
                         if est.get("programa") is not None else None),
            "cohorte": (str(est.get("cohorte", "")).strip()
                        if est.get("cohorte") is not None else None),
        })

    if USAR_SQLITE:
        query = """
        INSERT INTO estudiantes (identificacion, nombre_completo, correo, programa, cohorte)
        VALUES (:identificacion, :nombre_completo, :correo, :programa, :cohorte)
        ON CONFLICT (identificacion) DO UPDATE
        SET nombre_completo = excluded.nombre_completo,
            correo = excluded.correo,
            programa = excluded.programa,
            cohorte = excluded.cohorte;
        """
    else:
        query = """
        INSERT INTO estudiantes (identificacion, nombre_completo, correo, programa, cohorte)
        VALUES (%(identificacion)s, %(nombre_completo)s, %(correo)s, %(programa)s, %(cohorte)s)
        ON CONFLICT (identificacion) DO UPDATE
        SET nombre_completo = EXCLUDED.nombre_completo,
            correo = EXCLUDED.correo,
            programa = EXCLUDED.programa,
            cohorte = EXCLUDED.cohorte;
        """

    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.executemany(query, registros_limpios)
        conn.commit()

    return len(registros_limpios)


def insertar_evaluaciones(evaluaciones: List[Dict[str, Any]]) -> int:
    """Inserta una lista de evaluaciones en la base de datos.
    
    Asegura que la identificación sea tratada como texto limpio sin espacios.
    """
    if not evaluaciones:
        return 0

    registros_limpios = []
    for ev in evaluaciones:
        fecha_cierre = ev.get("fecha_cierre")
        if USAR_SQLITE and fecha_cierre is not None:
            fecha_cierre_val = (fecha_cierre.isoformat()
                                if hasattr(fecha_cierre, "isoformat")
                                else str(fecha_cierre))
        else:
            fecha_cierre_val = fecha_cierre

        registros_limpios.append({
            "identificacion": str(ev.get("identificacion", "")).strip(),
            "programa": (str(ev.get("programa", "")).strip()
                         if ev.get("programa") is not None else None),
            "modulo": (str(ev.get("modulo", "")).strip()
                       if ev.get("modulo") is not None else None),
            "nota": ev.get("nota"),
            "asistencia_pct": ev.get("asistencia_pct"),
            "fecha_cierre": fecha_cierre_val,
        })

    if USAR_SQLITE:
        query = """
        INSERT INTO evaluaciones (identificacion, programa, modulo, nota, asistencia_pct, fecha_cierre)
        VALUES (:identificacion, :programa, :modulo, :nota, :asistencia_pct, :fecha_cierre);
        """
    else:
        query = """
        INSERT INTO evaluaciones (identificacion, programa, modulo, nota, asistencia_pct, fecha_cierre)
        VALUES (%(identificacion)s, %(programa)s, %(modulo)s, %(nota)s, %(asistencia_pct)s, %(fecha_cierre)s);
        """

    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.executemany(query, registros_limpios)
        conn.commit()

    return len(registros_limpios)


def contar_estudiantes() -> int:
    """Retorna el conteo total de filas en la tabla estudiantes."""
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM estudiantes;")
        resultado = cur.fetchone()
        return int(resultado[0]) if resultado else 0


def contar_evaluaciones() -> int:
    """Retorna el conteo total de filas en la tabla evaluaciones."""
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM evaluaciones;")
        resultado = cur.fetchone()
        return int(resultado[0]) if resultado else 0


def obtener_estudiantes() -> List[Dict[str, Any]]:
    """Retorna todos los estudiantes registrados como una lista de diccionarios."""
    query = """
    SELECT identificacion, nombre_completo, correo, programa, cohorte
    FROM estudiantes
    ORDER BY identificacion;
    """
    with get_db_connection() as conn:
        if USAR_SQLITE:
            cur = conn.cursor()
            cur.execute(query)
            return [dict(r) for r in cur.fetchall()]
        else:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(query)
                return [dict(r) for r in cur.fetchall()]


def obtener_evaluaciones() -> List[Dict[str, Any]]:
    """Retorna todas las evaluaciones registradas como una lista de diccionarios."""
    query = """
    SELECT id, identificacion, programa, modulo, nota, asistencia_pct, fecha_cierre
    FROM evaluaciones
    ORDER BY identificacion, id;
    """
    with get_db_connection() as conn:
        if USAR_SQLITE:
            cur = conn.cursor()
            cur.execute(query)
            return [dict(r) for r in cur.fetchall()]
        else:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(query)
                return [dict(r) for r in cur.fetchall()]


def asegurar_tablas_y_datos() -> None:
    """Asegura que las tablas existan y que contengan registros.
    
    Si las tablas están vacías, auto-carga los datos desde los archivos Excel.
    """
    crear_tablas()
    if contar_estudiantes() == 0 or contar_evaluaciones() == 0:
        from services.carga_excel import procesar_y_cargar_datos
        procesar_y_cargar_datos()
