# AGENTS.md — App de Certificados de la Academia

## Contexto
- Academia Horizonte: centro de formación que emite un certificado por estudiante al cerrar cada cohorte. Hoy es manual en Excel/Word; se automatiza como app web.

## Cómo trabajar
- Español sencillo (usuario principiante). Explicar cada comando antes de ejecutarlo.
- Código simple y comentado en español, señalando los ladrillos: variables, tipos, condicionales, bucles y funciones.
- Plan corto antes de construir y esperar aprobación. Entregas pequeñas indicando archivos y capa MVC.
- Al cerrar cada entrega: pasar `tester-datos` (cifras de control) y `revisor` (MVC + secretos). Subagentes en `.agents/agents/`.

## Decisiones técnicas (acordadas en análisis, ver `PLAN.md`)
- Excel: **pandas + openpyxl** (promedios y agrupado en pocas líneas; `sheet_name` exacto). Descartado: solo openpyxl (código manual) y xlrd (no lee `.xlsx` modernos).
- Web: **Flask + Jinja** (liviano, ideal para 4 rutas HTML). Descartado: Django (sobredimensionado) y FastAPI (orientado a APIs JSON).
- PDF: **fpdf2** (simple, A4 horizontal sin dependencias). Descartado: ReportLab (más potente pero más complejo).
- Orden de construcción: 1 cruce de datos → 2 backend → 3 interfaz. No se avanza de etapa sin su validación.

## Comandos (uv, nunca pip — Python 3.12 según `.python-version`)
- `uv sync` — instalar dependencias (`pyproject.toml`: flask, pandas, openpyxl, fpdf2, psycopg[binary], python-dotenv).
- `uv run python cargar_datos.py` — carga inicial a la BD y verifica 24 estudiantes / 88 evaluaciones.
- `uv run python app.py` — enciende Flask en puerto 5000.
- No hay tests, lint ni CI. La verificación es el script anterior + cifras de control.

## Arquitectura MVC (estricta, la revisa `revisor`)
- Analogía del equipo: Bodega = `INSUMOS/` (no se modifica) · Cocina = Python/Flask (`app.py`, `models/`, `services/`, `controllers/`: toda la lógica, nunca en la interfaz) · Salón = `views/` (solo muestra, no calcula ni decide).
- `app.py`: crea `app = Flask(__name__, template_folder="views", static_folder="static")`; registra blueprints; llama `asegurar_tablas_y_datos()` al arrancar (auto-carga si tablas vacías).
- `models/datos.py`: ÚNICO archivo con SQL y conexión a BD. No poner SQL en otro lado.
- `models/certificados.py`: reglas R1–R6; constantes `NOTA_MINIMA = 70`, `ASISTENCIA_MINIMA = 80`, `ASISTENCIA_INCONSISTENCIA_LIMITE = 50`.
- `services/carga_excel.py`: lee los 2 Excel con pandas (`sheet_name` exacto) y guarda vía `models/datos.py`.
- `controllers/`: solo rutas que orquestan (sin cálculos ni SQL). Hoy solo existe `controllers/tablero.py` con `/`.
- `views/` + `static/`: solo Jinja/HTML/CSS. Paleta `#14213D` (azul marino) y `#B8923D` (dorado).
- Propiedad por subagente: `backend-flask` no toca `views/`; `disenador-vistas` no toca Python.

## Estado real vs pendiente (no asumir que existe)
- FALTAN: `services/generador_pdf.py` (fpdf2, A4 horizontal) y rutas `/cargar`, `/certificado/<identificacion>/<programa>`, `/descargar-todos` (.zip). Solo `/` funciona.
- Directorio real de datos es `INSUMOS/` (mayúsculas); `buscar_ruta_insumo()` acepta ambas variantes.

## Datos y reglas (fuente ejecutable: `models/certificados.py`, `services/carga_excel.py`)
- `INSUMOS/Maestro_Estudiantes.xlsx` hoja `Estudiantes` / `INSUMOS/Registro_Evaluaciones.xlsx` hoja `Evaluaciones`. NUNCA modificar.
- `Identificacion` siempre texto: `str(...).strip()` y quitar sufijo `.0` de Excel (`limpiar_texto_identificacion`).
- R1 agrupar por (identificacion + programa). R2 promedios de nota/asistencia, redondeo 2 decimales. R3 Aprobación ≥70 y ≥80 (límites incluidos). R4 Participación <70 y ≥80. R5 Sin certificado si asistencia <80. R6 inconsistencias (no se certifican): sin evaluaciones, evaluación sin maestro, asistencia <50.
- Hecho = cifras exactas: 19 Aprobación, 3 Participación, 1 Sin certificado, 3 inconsistencias (304560321 Javier Espinoza sin evaluaciones; 999880777 sin maestro; Fernanda Zúñiga asistencia 36.25). Controles: Camila Rojas Méndez 101230456 = 91.25/96.25 Aprobación; Luis Acuña Blanco = 72.0/81.67 Aprobación.

## BD y secretos
- `models/datos.py`: si `DATABASE_URL` existe usa Supabase/PostgreSQL con `psycopg.connect(..., prepare_threshold=None)` (obligatorio por el pooler); si no, respaldo local `certificados.db` (SQLite). Tablas: `estudiantes(identificacion TEXT PK, ...)` y `evaluaciones(id autoincremental, ...)`.
- NUNCA leer ni mostrar `.env` (está en `.gitignore`; ver formato en `.env.ejemplo`). NUNCA escribir contraseñas/tokens en código.
