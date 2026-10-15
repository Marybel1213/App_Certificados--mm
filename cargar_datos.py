"""Script de carga inicial de datos desde Excel hacia Supabase.

Crea las tablas necesarias si no existen y puebla las tablas
'estudiantes' y 'evaluaciones' a partir de los archivos de insumos.
"""

import sys
from models.datos import crear_tablas, contar_estudiantes, contar_evaluaciones
from services.carga_excel import procesar_y_cargar_datos


def main():
    print("Iniciando proceso de configuración y carga de datos...")
    
    try:
        # Paso 1: Asegurar creación de tablas
        print("1. Creando tablas en Supabase (si no existen)...")
        crear_tablas()
        print("   Tablas verificadas correctamente.")

        # Paso 2: Cargar datos desde los archivos Excel
        print("2. Procesando y cargando archivos Excel...")
        cargados_est, cargados_eval = procesar_y_cargar_datos()
        print(f"   Procesados desde Excel: {cargados_est} estudiantes y {cargados_eval} evaluaciones.")

        # Paso 3: Verificar conteo final en base de datos
        print("3. Verificando conteo de registros en la base de datos...")
        total_estudiantes = contar_estudiantes()
        total_evaluaciones = contar_evaluaciones()

        print("--------------------------------------------------")
        print("RESULTADO DE LA CARGA:")
        print(f"Total filas en tabla 'estudiantes': {total_estudiantes}")
        print(f"Total filas en tabla 'evaluaciones': {total_evaluaciones}")
        print("--------------------------------------------------")

        if total_estudiantes == 24 and total_evaluaciones == 88:
            print("Verificación exitosa: Coincide exactamente con los insumos esperados.")
        else:
            print(f"Aviso: Se esperaban 24 estudiantes y 88 evaluaciones. Se registraron {total_estudiantes} y {total_evaluaciones}.")

    except Exception as e:
        print(f"Error durante el proceso de carga: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
