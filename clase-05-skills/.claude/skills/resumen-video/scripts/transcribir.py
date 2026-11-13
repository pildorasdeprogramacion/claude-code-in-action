# /// script
# requires-python = ">=3.10,<3.14"
# dependencies = [
#   "faster-whisper>=1.1.0",
#   "av>=11,<19",  # PyAV 19 quitó el parámetro metadata_errors que usa faster-whisper 1.2.x
# ]
# ///
"""
Transcribe un audio con faster-whisper y deja la transcripción partida en bloques.

Uso:
    uv run transcribir.py AUDIO --salida CARPETA [opciones]

Opciones:
    --modelo          auto, tiny, base, small, medium, large-v3 o turbo
                      (auto = large-v3 en GPU, small en CPU)
    --idioma          código ISO (es, en, pt...) o auto para detectarlo (por defecto: es)
    --minutos-bloque  minutos de audio por bloque (por defecto: 10)
    --dispositivo     auto, cpu o cuda (por defecto: auto)

Archivos que genera dentro de CARPETA:
    transcripcion.md       transcripción completa con timestamps
    bloques/bloque_01.md   la misma transcripción partida cada N minutos
    metadata.json          duración, idioma, modelo, dispositivo y lista de bloques
    progreso.txt           avance en vivo; al final dice "estado: TERMINADO" o "estado: ERROR"
"""

from __future__ import annotations

import argparse
import ctypes
import datetime
import json
import os
import sys
import time
from pathlib import Path

MODELO_GPU = "large-v3"
MODELO_CPU = "small"


# ---------------------------------------------------------------------------
# 1. Consola en UTF-8: en Windows la salida redirigida puede llegar en cp1252
# ---------------------------------------------------------------------------
def configurar_consola() -> None:
    for flujo in (sys.stdout, sys.stderr):
        try:
            flujo.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass


# ---------------------------------------------------------------------------
# 2. Librerías NVIDIA instaladas con pip
#    Solo existen si el comando se ejecutó con:
#    uv run --with nvidia-cublas-cu12 --with "nvidia-cudnn-cu12>=9" ...
# ---------------------------------------------------------------------------
def registrar_librerias_nvidia() -> None:
    try:
        import nvidia  # paquete que crean nvidia-cublas-cu12 y nvidia-cudnn-cu12
    except ImportError:
        return

    pendientes: list[Path] = []
    for base in map(Path, nvidia.__path__):
        for sub in ("cublas", "cudnn"):
            if sys.platform == "win32":
                # Windows: agregar la carpeta de las DLLs a la búsqueda del proceso
                carpeta = base / sub / "bin"
                if carpeta.is_dir():
                    os.add_dll_directory(str(carpeta))
                    os.environ["PATH"] = str(carpeta) + os.pathsep + os.environ.get("PATH", "")
            else:
                # Linux: precargar las .so para que CTranslate2 las encuentre por nombre
                carpeta = base / sub / "lib"
                if carpeta.is_dir():
                    pendientes.extend(sorted(carpeta.glob("lib*.so*")))

    # Algunas librerías dependen de otras: se intenta varias veces hasta que no haya avance
    for _ in range(3):
        fallidas = []
        for libreria in pendientes:
            try:
                ctypes.CDLL(str(libreria), mode=ctypes.RTLD_GLOBAL)
            except OSError:
                fallidas.append(libreria)
        if len(fallidas) == len(pendientes):
            break
        pendientes = fallidas


# ---------------------------------------------------------------------------
# 3. Elegir dispositivo: GPU si existe y sus librerías cargan; si no, CPU
# ---------------------------------------------------------------------------
LIBRERIAS_CUDA = {
    "win32": ["cublas64_12.dll", "cudnn_ops64_9.dll"],
    "linux": ["libcublas.so.12", "libcudnn_ops.so.9"],
}


def cuda_disponible() -> tuple[bool, str]:
    import ctranslate2  # viene instalado con faster-whisper

    try:
        if ctranslate2.get_cuda_device_count() == 0:
            return False, "no hay GPU NVIDIA visible para CTranslate2"
    except Exception as error:  # noqa: BLE001
        return False, f"no se pudo consultar CUDA ({error})"

    plataforma = "win32" if sys.platform == "win32" else "linux"
    for nombre in LIBRERIAS_CUDA[plataforma]:
        try:
            if sys.platform == "win32":
                ctypes.WinDLL(nombre, winmode=0)  # winmode=0: busca también en PATH
            else:
                ctypes.CDLL(nombre)
        except OSError:
            return False, f"falta la librería {nombre} (ver Anexo GPU de la guía)"
    return True, "GPU NVIDIA con cuBLAS y cuDNN disponibles"


def configuracion_cpu(modelo: str, motivo: str) -> dict:
    return {
        "dispositivo": "cpu",
        "compute_type": "int8",
        "modelo": MODELO_CPU if modelo == "auto" else modelo,
        "motivo": motivo,
    }


def elegir_configuracion(dispositivo: str, modelo: str) -> dict:
    if dispositivo == "cpu":
        return configuracion_cpu(modelo, "se pidió CPU con --dispositivo cpu")

    usar_gpu, motivo = cuda_disponible()
    if usar_gpu:
        return {
            "dispositivo": "cuda",
            "compute_type": "float16",
            "modelo": MODELO_GPU if modelo == "auto" else modelo,
            "motivo": motivo,
        }
    if dispositivo == "cuda":
        raise RuntimeError(f"se pidió --dispositivo cuda pero {motivo}")
    return configuracion_cpu(modelo, motivo)


# ---------------------------------------------------------------------------
# 4. Tiempo y progreso
# ---------------------------------------------------------------------------
def formatear_tiempo(segundos: float) -> str:
    total = int(segundos)
    return f"{total // 3600:02d}:{total % 3600 // 60:02d}:{total % 60:02d}"


class Progreso:
    """Escribe el avance en progreso.txt y en stderr, como máximo cada 5 segundos."""

    def __init__(self, archivo: Path):
        self.archivo = archivo
        self.ultimo = 0.0

    def escribir(self, estado: str, detalle: str = "", forzar: bool = False) -> None:
        ahora = time.monotonic()
        if not forzar and ahora - self.ultimo < 5:
            return
        self.ultimo = ahora
        self.archivo.write_text(f"estado: {estado}\n{detalle}\n", encoding="utf-8")
        print(f"[{estado}] {detalle}", file=sys.stderr, flush=True)


# ---------------------------------------------------------------------------
# 5. Transcripción con faster-whisper
# ---------------------------------------------------------------------------
def transcribir(audio: Path, config: dict, idioma: str | None, progreso: Progreso):
    from faster_whisper import WhisperModel

    progreso.escribir(
        "CARGANDO MODELO",
        f"modelo {config['modelo']} en {config['dispositivo']} "
        "(la primera vez se descarga y puede tardar varios minutos)",
        forzar=True,
    )
    modelo = WhisperModel(
        config["modelo"],
        device=config["dispositivo"],
        compute_type=config["compute_type"],
        cpu_threads=min(8, os.cpu_count() or 4),
    )

    segmentos, info = modelo.transcribe(
        str(audio),
        language=idioma,                      # None = detectar el idioma
        vad_filter=True,                      # Silero VAD: quita los silencios
        vad_parameters={"min_silence_duration_ms": 500},
        condition_on_previous_text=False,     # una alucinación no se arrastra al resto
        no_speech_threshold=0.6,              # descarta segmentos sin voz
        compression_ratio_threshold=2.4,      # descarta bucles repetitivos
        temperature=[0.0, 0.2, 0.4],          # reintento progresivo si baja la confianza
    )

    duracion = formatear_tiempo(info.duration)
    resultado: list[tuple[float, str]] = []
    # segmentos es un generador: la transcripción ocurre mientras se recorre
    for segmento in segmentos:
        texto = segmento.text.strip()
        if texto:
            resultado.append((segmento.start, texto))
        porcentaje = segmento.end / info.duration * 100 if info.duration else 0
        progreso.escribir(
            "TRANSCRIBIENDO",
            f"avance {formatear_tiempo(segmento.end)} de {duracion} ({porcentaje:.0f} %)",
        )
    return resultado, info


# ---------------------------------------------------------------------------
# 6. Resultados: transcripción completa, bloques y metadata
# ---------------------------------------------------------------------------
def agrupar_en_bloques(segmentos, minutos_bloque: int) -> list[tuple[int, list]]:
    tamano = minutos_bloque * 60
    bloques: dict[int, list] = {}
    for inicio, texto in segmentos:
        bloques.setdefault(int(inicio // tamano), []).append((inicio, texto))
    return sorted(bloques.items())


def escribir_resultados(segmentos, info, config: dict, audio: Path, salida: Path, minutos_bloque: int) -> dict:
    carpeta_bloques = salida / "bloques"
    carpeta_bloques.mkdir(parents=True, exist_ok=True)
    for viejo in carpeta_bloques.glob("bloque_*.md"):  # limpia corridas anteriores
        viejo.unlink()

    lineas = [f"[{formatear_tiempo(inicio)}] {texto}" for inicio, texto in segmentos]
    encabezado = (
        f"# Transcripción: {audio.name}\n\n"
        f"- Duración: {formatear_tiempo(info.duration)}\n"
        f"- Idioma: {info.language}\n"
        f"- Modelo: {config['modelo']} ({config['dispositivo']})\n\n"
    )
    archivo_transcripcion = salida / "transcripcion.md"
    archivo_transcripcion.write_text(encabezado + "\n".join(lineas) + "\n", encoding="utf-8")

    tamano = minutos_bloque * 60
    rutas_bloques = []
    for numero, (indice, contenido) in enumerate(agrupar_en_bloques(segmentos, minutos_bloque), start=1):
        desde = formatear_tiempo(indice * tamano)
        hasta = formatear_tiempo(min((indice + 1) * tamano, info.duration))
        cuerpo = "\n".join(f"[{formatear_tiempo(inicio)}] {texto}" for inicio, texto in contenido)
        archivo = carpeta_bloques / f"bloque_{numero:02d}.md"
        archivo.write_text(f"# Bloque {numero} ({desde} a {hasta})\n\n{cuerpo}\n", encoding="utf-8")
        rutas_bloques.append(str(archivo))

    metadata = {
        "audio": str(audio),
        "duracion": formatear_tiempo(info.duration),
        "duracion_segundos": round(info.duration, 1),
        "idioma": info.language,
        "probabilidad_idioma": round(info.language_probability, 2),
        "modelo": config["modelo"],
        "dispositivo": config["dispositivo"],
        "motivo_dispositivo": config["motivo"],
        "segmentos": len(segmentos),
        "transcripcion": str(archivo_transcripcion),
        "bloques": rutas_bloques,
        "generado": datetime.datetime.now().isoformat(timespec="seconds"),
    }
    (salida / "metadata.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return metadata


# ---------------------------------------------------------------------------
# 7. Programa principal
# ---------------------------------------------------------------------------
def leer_argumentos() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Transcribe un audio con faster-whisper y lo parte en bloques.")
    parser.add_argument("audio", type=Path, help="ruta del audio (mp3, wav, m4a...)")
    parser.add_argument("--salida", type=Path, required=True, help="carpeta donde se guardan los resultados")
    parser.add_argument("--modelo", default="auto", help="auto, tiny, base, small, medium, large-v3 o turbo")
    parser.add_argument("--idioma", default="es", help="código ISO (es, en, pt...) o auto")
    parser.add_argument("--minutos-bloque", type=int, default=10, help="minutos de audio por bloque")
    parser.add_argument("--dispositivo", choices=["auto", "cpu", "cuda"], default="auto")
    return parser.parse_args()


def main() -> int:
    configurar_consola()
    args = leer_argumentos()
    audio = args.audio.expanduser().resolve()
    salida = args.salida.expanduser().resolve()
    salida.mkdir(parents=True, exist_ok=True)
    progreso = Progreso(salida / "progreso.txt")

    if not audio.is_file():
        progreso.escribir("ERROR", f"no existe el archivo {audio}", forzar=True)
        return 1

    idioma = None if args.idioma == "auto" else args.idioma
    try:
        registrar_librerias_nvidia()
        config = elegir_configuracion(args.dispositivo, args.modelo)
        try:
            segmentos, info = transcribir(audio, config, idioma, progreso)
        except Exception as error:  # noqa: BLE001
            if config["dispositivo"] != "cuda" or args.dispositivo == "cuda":
                raise
            # La GPU falló a mitad de camino (librerías incompletas, memoria...): repetir en CPU
            print(f"La GPU falló ({error}). Se repite en CPU.", file=sys.stderr, flush=True)
            config = configuracion_cpu(args.modelo, f"la GPU falló: {error}")
            segmentos, info = transcribir(audio, config, idioma, progreso)
        metadata = escribir_resultados(segmentos, info, config, audio, salida, args.minutos_bloque)
    except Exception as error:  # noqa: BLE001
        import traceback
        traceback.print_exc()
        progreso.escribir("ERROR", f"{type(error).__name__}: {error}", forzar=True)
        return 1

    progreso.escribir("TERMINADO", f"resultados en {salida}", forzar=True)
    print(json.dumps(metadata, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
