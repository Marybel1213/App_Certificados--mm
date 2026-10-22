"""Controlador de entrada y salida: /login, /salir y el protector de rutas.

Solo orquesta: lee los datos del formulario, pide la validación al servicio
de autenticación y guarda el usuario en la sesión de Flask.
"""

from functools import wraps

from flask import (
    Blueprint,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from services.autenticacion import obtener_configuracion, verificar_credenciales

auth_bp = Blueprint("auth", __name__)


def requiere_login(vista):
    """DECORADORA: deja pasar solo si hay sesión iniciada.

    Si no hay nadie en la sesión, redirige a /login y guarda la ruta que la
    persona quería ver para volver a ella después de entrar.
    """

    @wraps(vista)
    def envoltura(*args, **kwargs):
        # LADRILLO: CONDICIONAL. session es un diccionario que Flask guarda
        # firmado en una cookie; aquí revisamos si tiene el correo.
        if not session.get("correo"):
            return redirect(url_for("auth.login", next=request.path))
        return vista(*args, **kwargs)

    return envoltura


def solo_admin(vista):
    """DECORADORA: exige sesión con rol 'admin'. Si no, responde 403."""
    @wraps(vista)
    def envoltura(*args, **kwargs):
        # LADRILLO: CONDICIONAL. Sin sesión, primero mandamos a la entrada.
        if not session.get("correo"):
            return redirect(url_for("auth.login", next=request.path))
        # LADRILLO: CONDICIONAL. Con sesión pero sin rol admin, error 403.
        if session.get("rol") != "admin":
            return render_template("sin_permiso.html"), 403
        return vista(*args, **kwargs)

    return envoltura


def _destino_seguro(valor: str) -> str:
    """Evita que el parámetro 'next' mande a un sitio externo."""
    # LADRILLO: CONDICIONAL. Solo aceptamos rutas internas que empiezan con /.
    if valor and valor.startswith("/") and not valor.startswith("//"):
        return valor
    return url_for("tablero.index")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """Muestra el formulario y valida el correo y la contraseña."""
    # LADRILLO: VARIABLE con los usuarios y el aviso de modo demostración.
    configuracion = obtener_configuracion()
    error = None
    correo_escrito = ""

    # LADRILLO: CONDICIONAL. Solo validamos cuando el formulario se envía.
    if request.method == "POST":
        correo_escrito = (request.form.get("correo") or "").strip()
        clave = request.form.get("clave") or ""

        # LADRILLO: llamada a la FUNCIÓN del servicio que valida.
        usuario = verificar_credenciales(correo_escrito, clave)

        # LADRILLO: CONDICIONAL. Si el usuario existe, abrimos la sesión.
        if usuario:
            session.clear()  # Borra cualquier resto de una sesión anterior.
            session["correo"] = usuario["correo"]
            session["rol"] = usuario["rol"]
            return redirect(_destino_seguro(request.args.get("next", "")))

        error = "Correo o contraseña incorrectos. Intente de nuevo."

    return render_template(
        "login.html",
        error=error,
        correo=correo_escrito,
        modo_demo=configuracion["modo_demo"],
        usuarios_demo=configuracion["usuarios_demo"],
    )


@auth_bp.route("/salir")
def salir():
    """Borra la sesión y devuelve a la pantalla de entrada."""
    # LADRILLO: FUNCIÓN de Flask que vacía la sesión (cierra la sesión).
    session.clear()
    return redirect(url_for("auth.login"))
