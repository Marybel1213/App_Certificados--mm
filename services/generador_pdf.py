"""Servicio de generación de certificados en PDF con fpdf2.

Este archivo SOLO maqueta el certificado (A4 horizontal). No calcula reglas
de negocio: recibe un estudiante ya procesado por models/certificados.py.
"""

from datetime import date
from fpdf import FPDF

# LADRILLO: CONSTANTES de color (tuplas RGB) de la identidad visual.
AZUL_MARINO = (20, 33, 61)      # #14213D
DORADO = (184, 146, 61)         # #B8923D
GRIS_TEXTO = (90, 98, 112)
BLANCO = (255, 255, 255)
GRIS_CLARO = (240, 242, 245)

# LADRILLO: VARIABLE lista con los meses para la fecha en español.
MESES = [
    "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "setiembre", "octubre", "noviembre", "diciembre",
]

# Ancho y alto de una hoja A4 horizontal en milímetros.
ANCHO = 297
ALTO = 210


def _fecha_larga() -> str:
    """Devuelve la fecha de hoy escrita en español (tipo str)."""
    hoy = date.today()
    return f"{hoy.day} de {MESES[hoy.month - 1]} de {hoy.year}"


def _texto_seguro(valor) -> str:
    """Convierte cualquier dato a texto apto para las fuentes básicas del PDF."""
    texto = "" if valor is None else str(valor)
    # Las fuentes estándar de fpdf2 usan latin-1; cambiamos lo que no exista.
    return (texto.replace("—", "-").replace("–", "-")
                 .replace("≥", ">=").replace("≤", "<="))


class CertificadoPDF(FPDF):
    """Hoja del certificado (sin encabezado ni pie automáticos)."""

    def header(self):
        pass

    def footer(self):
        pass


def generar_certificado_pdf(estudiante: dict) -> bytes:
    """Genera un certificado en PDF y devuelve sus bytes.

    'estudiante' debe traer: identificacion, nombre_completo, programa,
    cohorte, promedio_nota, promedio_asistencia, tipo_certificado y
    cantidad_evaluaciones (tal como lo entrega models/certificados.py).
    """
    # LADRILLO: VARIABLES que toman los datos del estudiante.
    nombre = _texto_seguro(estudiante.get("nombre_completo") or "Sin nombre")
    identificacion = _texto_seguro(estudiante.get("identificacion"))
    programa = _texto_seguro(estudiante.get("programa"))
    cohorte = _texto_seguro(estudiante.get("cohorte") or "-")
    tipo = _texto_seguro(estudiante.get("tipo_certificado") or "")
    promedio = float(estudiante.get("promedio_nota") or 0)
    asistencia = float(estudiante.get("promedio_asistencia") or 0)
    modulos = int(estudiante.get("cantidad_evaluaciones") or 0)

    # LADRILLO: CONDICIONAL que cambia el título y la frase según el tipo.
    if "Aprobación" in tipo:
        titulo = "CERTIFICADO DE APROBACIÓN"
        frase = "por haber aprobado satisfactoriamente el programa"
    else:
        titulo = "CERTIFICADO DE PARTICIPACIÓN"
        frase = "por su participación y cumplimiento en el programa"

    pdf = CertificadoPDF(orientation="L", unit="mm", format="A4")
    pdf.set_auto_page_break(False)
    pdf.add_page()
    pdf.set_margins(0, 0, 0)

    # Fondo blanco.
    pdf.set_fill_color(*BLANCO)
    pdf.rect(0, 0, ANCHO, ALTO, "F")

    # Marco exterior azul marino y marco interior dorado.
    pdf.set_draw_color(*AZUL_MARINO)
    pdf.set_line_width(1.6)
    pdf.rect(8, 8, ANCHO - 16, ALTO - 16)
    pdf.set_draw_color(*DORADO)
    pdf.set_line_width(0.6)
    pdf.rect(13, 13, ANCHO - 26, ALTO - 26)

    # Banda superior azul marino con el nombre de la academia.
    pdf.set_fill_color(*AZUL_MARINO)
    pdf.rect(13, 13, ANCHO - 26, 26, "F")
    pdf.set_text_color(*BLANCO)
    pdf.set_font("Helvetica", "B", 20)
    pdf.set_xy(13, 18)
    pdf.cell(ANCHO - 26, 10, "ACADEMIA HORIZONTE", align="C")
    pdf.set_font("Helvetica", "", 10)
    pdf.set_xy(13, 28)
    pdf.cell(ANCHO - 26, 6, "Formación técnica para empresas", align="C")

    # Título del certificado.
    pdf.set_text_color(*DORADO)
    pdf.set_font("Helvetica", "B", 26)
    pdf.set_xy(20, 48)
    pdf.cell(ANCHO - 40, 12, titulo, align="C")

    # Frase introductoria.
    pdf.set_text_color(*GRIS_TEXTO)
    pdf.set_font("Helvetica", "", 12)
    pdf.set_xy(20, 66)
    pdf.cell(ANCHO - 40, 8, "Se otorga el presente certificado a", align="C")

    # Nombre del estudiante (baja el tamaño si el nombre es muy largo).
    tamano_nombre = 30 if len(nombre) <= 38 else 24
    pdf.set_text_color(*AZUL_MARINO)
    pdf.set_font("Helvetica", "B", tamano_nombre)
    pdf.set_xy(20, 76)
    pdf.cell(ANCHO - 40, 16, nombre, align="C")

    # Línea dorada bajo el nombre.
    pdf.set_draw_color(*DORADO)
    pdf.set_line_width(0.5)
    pdf.line(ANCHO / 2 - 65, 95, ANCHO / 2 + 65, 95)

    # Programa y cohorte.
    pdf.set_text_color(*GRIS_TEXTO)
    pdf.set_font("Helvetica", "", 12)
    pdf.set_xy(20, 100)
    pdf.cell(ANCHO - 40, 7, frase, align="C")
    pdf.set_text_color(*AZUL_MARINO)
    pdf.set_font("Helvetica", "B", 15)
    pdf.set_xy(20, 108)
    pdf.cell(ANCHO - 40, 9, programa, align="C")
    pdf.set_text_color(*GRIS_TEXTO)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_xy(20, 118)
    pdf.cell(ANCHO - 40, 6, f"Cohorte {cohorte}", align="C")

    # Recuadro con el detalle académico (tres columnas).
    caja_y = 130
    pdf.set_fill_color(*GRIS_CLARO)
    pdf.rect(55, caja_y, ANCHO - 110, 20, "F")
    pdf.set_text_color(*AZUL_MARINO)
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_xy(55, caja_y + 3)
    pdf.cell((ANCHO - 110) / 3, 5, "PROMEDIO", align="C")
    pdf.cell((ANCHO - 110) / 3, 5, "ASISTENCIA", align="C")
    pdf.cell((ANCHO - 110) / 3, 5, "MÓDULOS", align="C")
    pdf.set_font("Helvetica", "", 12)
    pdf.set_xy(55, caja_y + 9)
    pdf.cell((ANCHO - 110) / 3, 6, f"{promedio:.2f}", align="C")
    pdf.cell((ANCHO - 110) / 3, 6, f"{asistencia:.2f}%", align="C")
    pdf.cell((ANCHO - 110) / 3, 6, str(modulos), align="C")

    # Pie: fecha, firmas y folio.
    pdf.set_text_color(*GRIS_TEXTO)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_xy(20, 158)
    pdf.cell(ANCHO - 40, 6, f"Emitido el {_fecha_larga()}", align="C")

    pdf.set_draw_color(*AZUL_MARINO)
    pdf.set_line_width(0.4)
    pdf.line(60, 183, 120, 183)
    pdf.line(177, 183, 237, 183)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_xy(60, 185)
    pdf.cell(60, 5, "Rectoría Académica", align="C")
    pdf.set_xy(177, 185)
    pdf.cell(60, 5, "Coordinación Académica", align="C")

    # Folio e identificación en la esquina inferior derecha.
    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(*GRIS_TEXTO)
    pdf.set_xy(ANCHO - 105, 185)
    pdf.cell(90, 4, f"Identificación: {identificacion}", align="R")
    pdf.set_xy(ANCHO - 105, 189)
    pdf.cell(90, 4, f"Folio: AH-{identificacion}-{cohorte}", align="R")

    return bytes(pdf.output())
