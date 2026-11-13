# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""
Revisa qué herramientas tiene la máquina para el skill resumen-video.

El SKILL.md ejecuta este script con inyección dinámica (!`...`) antes de que
Claude lea las instrucciones. Por eso SIEMPRE termina con código de salida 0:
si terminara con error, Claude Code cancelaría la invocación completa del skill.
"""

import datetime
import platform
import shutil
import subprocess
import sys


def primera_linea(comando: list[str]) -> str | None:
    """Ejecuta un comando y devuelve la primera línea de su salida, o None si falla."""
    try:
        resultado = subprocess.run(comando, capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.TimeoutExpired):
        return None
    if resultado.returncode != 0:
        return None
    lineas = resultado.stdout.strip().splitlines()
    return lineas[0].strip() if lineas else None


def revisar_ffmpeg() -> str:
    if shutil.which("ffmpeg") is None:
        return (
            "NO ENCONTRADO. Instalar con: Windows `winget install --id Gyan.FFmpeg -e` | "
            "macOS `brew install ffmpeg` | Ubuntu/Debian `sudo apt install ffmpeg`. "
            "Después cerrar y volver a abrir la terminal y Claude Code."
        )
    version = primera_linea(["ffmpeg", "-version"]) or "versión desconocida"
    return f"OK ({version})"


def revisar_gpu() -> str:
    if shutil.which("nvidia-smi") is None:
        return "no detectada (se usará CPU)"
    nombre = primera_linea(["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"])
    return nombre or "no detectada (se usará CPU)"


def main() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

    try:
        lineas = [
            f"- Sistema operativo: {platform.system()} {platform.release()} ({platform.machine()})",
            f"- Python usado por uv: {platform.python_version()}",
            f"- ffmpeg: {revisar_ffmpeg()}",
            f"- GPU NVIDIA: {revisar_gpu()}",
            f"- Fecha: {datetime.date.today().isoformat()}",
        ]
    except Exception as error:  # noqa: BLE001 - nunca debe romper la invocación del skill
        lineas = [f"- No se pudo revisar el entorno: {error}"]

    print("\n".join(lineas))


if __name__ == "__main__":
    main()
    sys.exit(0)
