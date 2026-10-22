"""Servicio de autenticación: valida correo y contraseña sin base de datos.

Los dos usuarios (administrador y usuario normal) se leen de variables de
entorno con os.environ.get. Si esas variables no existen, se usan valores de
demostración y la pantalla de entrada lo avisa. NUNCA se escriben claves
reales en el código.
"""

import hmac
import os
from typing import Dict, List, Optional

from dotenv import load_dotenv

# LADRILLO: carga el archivo .env de la máquina local (en Vercel se usan las
# variables configuradas en el panel del proyecto).
load_dotenv()

# LADRILLO: CONSTANTES con los datos de DEMOSTRACIÓN. Solo se usan cuando la
# variable de entorno correspondiente no está definida.
ADMIN_CORREO_DEMO = "admin@academia.cr"
ADMIN_CLAVE_DEMO = "admin123"
USUARIO_CORREO_DEMO = "usuario@academia.cr"
USUARIO_CLAVE_DEMO = "usuario123"


def _leer_variable(nombre: str) -> Optional[str]:
    """Devuelve la variable de entorno sin espacios, o None si no existe."""
    # LADRILLO: VARIABLE de tipo str o None.
    valor = os.environ.get(nombre)
    return valor.strip() if valor and valor.strip() else None


def obtener_configuracion() -> Dict:
    """Arma los dos usuarios y dice si alguno quedó en modo demostración."""
    # LADRILLO: VARIABLES que leen cada dato desde el entorno.
    admin_correo = _leer_variable("ADMIN_CORREO")
    admin_clave = _leer_variable("ADMIN_CLAVE")
    usuario_correo = _leer_variable("USUARIO_CORREO")
    usuario_clave = _leer_variable("USUARIO_CLAVE")

    # LADRILLO: CONDICIONAL. Si falta al menos una variable, avisamos en la
    # pantalla de entrada que estamos en modo demostración.
    modo_demo = not (admin_correo and admin_clave and usuario_correo and usuario_clave)

    # LADRILLO: VARIABLE lista (tipo list) con los dos usuarios permitidos.
    usuarios: List[Dict[str, str]] = [
        {
            "correo": admin_correo or ADMIN_CORREO_DEMO,
            "clave": admin_clave or ADMIN_CLAVE_DEMO,
            "rol": "admin",
        },
        {
            "correo": usuario_correo or USUARIO_CORREO_DEMO,
            "clave": usuario_clave or USUARIO_CLAVE_DEMO,
            "rol": "usuario",
        },
    ]

    return {"usuarios": usuarios, "modo_demo": modo_demo}


def verificar_credenciales(correo: str, clave: str) -> Optional[Dict[str, str]]:
    """Busca un usuario que coincida; devuelve su correo y rol, o None."""
    correo_limpio = (correo or "").strip().lower()
    clave = clave or ""

    # LADRILLO: BUCLE que recorre los usuarios configurados.
    for usuario in obtener_configuracion()["usuarios"]:
        # LADRILLO: CONDICIONAL. El correo se compara sin mayúsculas.
        if usuario["correo"].strip().lower() != correo_limpio:
            continue
        # LADRILLO: CONDICIONAL. Compara la clave en tiempo constante.
        if hmac.compare_digest(usuario["clave"], clave):
            return {"correo": usuario["correo"], "rol": usuario["rol"]}

    return None
