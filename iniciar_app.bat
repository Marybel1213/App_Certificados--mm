@echo off
REM Arranca la App de Certificados de Academia Horizonte con doble clic.
REM Para detenerla: cierre esta ventana o pulse Ctrl + C.
cd /d "%~dp0"
uv run python app.py
pause
