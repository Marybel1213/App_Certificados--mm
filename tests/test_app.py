"""Pruebas automáticas de la App de Certificados.

Usan el cliente de pruebas de Flask (app.test_client()), que simula un
navegador sin abrir la aplicación de verdad ni el puerto 5000.

Importante: las variables de entorno se definen ANTES de importar la app,
para que las pruebas no dependan del archivo .env de la máquina.
"""

import io
import os
import re
from pathlib import Path

import pandas as pd
import pytest

# ---------------------------------------------------------------------------
# 1) Credenciales SOLO para pruebas. Se escriben antes de crear la app.
# ---------------------------------------------------------------------------
os.environ["ADMIN_CORREO"] = "admin@prueba.cr"
os.environ["ADMIN_CLAVE"] = "clave-admin-prueba"
os.environ["USUARIO_CORREO"] = "usuario@prueba.cr"
os.environ["USUARIO_CLAVE"] = "clave-usuario-prueba"
os.environ["SECRET_KEY"] = "clave-secreta-solo-para-pruebas"

# La app se importa DESPUÉS de definir el entorno (por eso el noqa).
from app import app  # noqa: E402

# Rutas de los Excel originales de la carpeta INSUMOS (nunca se modifican).
BASE_DIR = Path(__file__).resolve().parents[1]
CARPETA_INSUMOS = BASE_DIR / "INSUMOS"


@pytest.fixture()
def cliente():
    """Crea un cliente de pruebas nuevo para cada prueba (navegador limpio)."""
    app.config.update(TESTING=True)
    with app.test_client() as cliente_flask:
        yield cliente_flask


# ---------------------------------------------------------------------------
# PRUEBA 1: sin sesión no se puede ver el tablero.
# ---------------------------------------------------------------------------
def test_sin_sesion_redirige_a_login(cliente):
    """Simula a alguien que escribe la dirección / sin haber entrado.

    Espera una redirección (código 302) hacia la pantalla de entrada /login.
    """
    respuesta = cliente.get("/")

    assert respuesta.status_code == 302
    assert "/login" in respuesta.headers["Location"]


# ---------------------------------------------------------------------------
# PRUEBA 2: una clave equivocada no abre la sesión.
# ---------------------------------------------------------------------------
def test_clave_incorrecta_no_entra(cliente):
    """Simula escribir el correo correcto con una contraseña equivocada.

    Espera quedarse en la pantalla de entrada (código 200) con el aviso rojo
    de error, y que NO se haya guardado ningún correo en la sesión.
    """
    respuesta = cliente.post(
        "/login",
        data={"correo": os.environ["ADMIN_CORREO"], "clave": "clave-equivocada"},
    )

    assert respuesta.status_code == 200
    html = respuesta.get_data(as_text=True)
    assert "Correo o contraseña incorrectos" in html

    # La sesión debe seguir vacía: nadie quedó dentro.
    with cliente.session_transaction() as sesion:
        assert "correo" not in sesion


# ---------------------------------------------------------------------------
# PRUEBA 3: el rol "usuario" no puede entrar al panel de carga.
# ---------------------------------------------------------------------------
def test_usuario_no_puede_cargar(cliente):
    """Simula una sesión ya iniciada con rol "usuario".

    Pide /cargar (la ruta del panel de administrador) y espera un 403,
    que significa "no tiene permiso".
    """
    # LADRILLO: sesión falsa con el rol normal, sin pasar por el login.
    with cliente.session_transaction() as sesion:
        sesion["correo"] = os.environ["USUARIO_CORREO"]
        sesion["rol"] = "usuario"

    respuesta = cliente.post("/cargar")

    assert respuesta.status_code == 403


# ---------------------------------------------------------------------------
# PRUEBA 4: subir un Excel distinto cambia los contadores.
# ---------------------------------------------------------------------------
def test_excel_modificado_cambia_contadores(cliente):
    """Simula a un administrador subiendo las evaluaciones con notas cambiadas.

    A Camila Rojas Méndez (identificación 101230456) se le ponen todas las
    notas en 40. Como su asistencia sigue sobre 80, pasa de Aprobación a
    Participación. El Excel se arma EN MEMORIA: el archivo de INSUMOS no se
    toca. Se esperan 18 Aprobación, 4 Participación y 1 Sin certificado.
    """
    # LADRILLO: sesión falsa con rol admin.
    with cliente.session_transaction() as sesion:
        sesion["correo"] = os.environ["ADMIN_CORREO"]
        sesion["rol"] = "admin"

    # 1) Leemos las evaluaciones originales (sin modificar el archivo).
    evaluaciones = pd.read_excel(
        CARPETA_INSUMOS / "Registro_Evaluaciones.xlsx",
        sheet_name="Evaluaciones",
        dtype={"Identificacion": str},
    )

    # 2) Cambiamos SOLO las notas de Camila a 40.
    # LADRILLO: CONDICIONAL dentro de una máscara de pandas.
    es_camila = evaluaciones["Identificacion"].astype(str).str.strip() == "101230456"
    evaluaciones.loc[es_camila, "Nota"] = 40

    # 3) Guardamos ese Excel modificado en un BytesIO (caja en memoria).
    buffer_evaluaciones = io.BytesIO()
    with pd.ExcelWriter(buffer_evaluaciones, engine="openpyxl") as escritor:
        evaluaciones.to_excel(escritor, sheet_name="Evaluaciones", index=False)
    buffer_evaluaciones.seek(0)

    # 4) El maestro se envía tal cual está en INSUMOS.
    contenido_maestro = (CARPETA_INSUMOS / "Maestro_Estudiantes.xlsx").read_bytes()

    # 5) Enviamos el formulario como lo haría el navegador (multipart/form-data).
    respuesta = cliente.post(
        "/cargar",
        data={
            "accion": "ver",
            "archivo_maestro": (
                io.BytesIO(contenido_maestro),
                "Maestro_Estudiantes.xlsx",
            ),
            "archivo_evaluaciones": (
                buffer_evaluaciones,
                "Registro_Evaluaciones_modificado.xlsx",
            ),
        },
        content_type="multipart/form-data",
    )

    assert respuesta.status_code == 200
    html = respuesta.get_data(as_text=True)

    # LADRILLO: BUCLE/expresión regular que extrae los 3 contadores del HTML.
    contadores = re.findall(r'metric-value">\s*(\d+)\s*<', html)
    assert contadores == ["18", "4", "1"]
    # También debe avisar que son datos subidos y no guardados.
    assert "aviso-verde" in html
