# PLAN.md — App de Certificados de la Academia (modo Plan, sin código aún)

## Orden de construcción (pedido del equipo)
1. **Etapa 1 — Validar el cruce de datos** (sin web todavía).
2. **Etapa 2 — Backend con Flask** (rutas + PDF).
3. **Etapa 3 — Interfaz** (páginas HTML con estilo azul marino y dorado).

No se avanza de etapa sin cumplir su validación.

## Etapa 1 — Validar el cruce de datos
**Qué hacer:**
- Confirmar lectura de `INSUMOS/Maestro_Estudiantes.xlsx` (hoja `Estudiantes`) y `INSUMOS/Registro_Evaluaciones.xlsx` (hoja `Evaluaciones`) con `Identificacion` como texto.
- Confirmar reglas R1–R6 en `models/certificados.py` contra los datos reales.
- Decidir el punto abierto: con estos datos sale **0 Sin certificado** (nadie en asistencia 50–79.99), pero `AGENTS.md` esperaba 1. Opciones: corregir la cifra esperada a 0, o ajustar un dato de prueba.

**Cómo validar (antes de seguir):**
- `uv run python cargar_datos.py` → debe reportar 24 estudiantes / 88 evaluaciones.
- `tester-datos` verifica: 19 Aprobación, 3 Participación, 3 inconsistencias (304560321, 999880777, Fernanda 36.25) + controles Camila 91.25/96.25 y Luis 72.0/81.67.
- `revisor` confirma que solo `models/datos.py` tiene SQL.

## Etapa 2 — Backend con Flask
**Qué hacer (en este orden):**
1. Crear `services/generador_pdf.py` (fpdf2, A4 horizontal): un certificado por (identificacion + programa), solo para Aprobación y Participación.
2. Agregar ruta `/certificado/<identificacion>/<programa>` (devuelve el PDF).
3. Agregar ruta `/cargar` (formulario + recarga de los 2 Excel).
4. Agregar ruta `/descargar-todos` (.zip con los certificados).

**Cómo validar (antes de seguir):**
- `uv run python app.py` enciende en puerto 5000 sin errores.
- Descargar el PDF de Camila (101230456) y el de un Participación: datos y tipo correctos.
- Subir los 2 Excel por `/cargar` y revalidar cifras de la Etapa 1.
- `tester-datos` + `revisor` al cerrar.

## Etapa 3 — Interfaz
**Qué hacer (en este orden):**
1. Tablero `/`: tarjetas de totales, tabla de estudiantes (promedio, asistencia, tipo) y sección de inconsistencias como alertas.
2. Página `/cargar`: formulario de los 2 archivos con mensajes de éxito/error.
3. Estilo `#14213D` / `#B8923D`, limpio y legible (`disenador-vistas`; no toca Python).

**Cómo validar (cierre del proyecto):**
- Recorrido manual: tablero legible, inconsistencias visibles, PDF descargable, recarga funcional.
- `tester-datos` (cifras finales) + `revisor` (MVC, sin secretos, sin tocar `INSUMOS/` ni `.env`).
