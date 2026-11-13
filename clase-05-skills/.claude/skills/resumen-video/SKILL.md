---
name: resumen-video
description: Extrae el audio MP3 de un video, lo transcribe en local con faster-whisper y genera un resumen en Markdown (corto, detallado o capítulos con timestamps para YouTube). Úsala cuando el usuario pida resumir un video, una clase grabada, un live, un stream, una reunión o un webinar, o sacar los capítulos, los timestamps o el MP3 de un archivo .mp4, .mkv, .mov o .webm.
argument-hint: "<ruta-del-video> [corto|detallado|capitulos]"
arguments: [video, tipo]
allowed-tools: Bash(ffmpeg *), Bash(uv run *), Read, Write, Glob
context: fork
agent: general-purpose
background: false
---

# Resumen de video

Convierte un video en tres resultados: el MP3, la transcripción y un resumen en Markdown.
Sigue los pasos en orden. Si un paso falla, detente y explica el error; no improvises otra ruta.

## Entorno detectado al invocar el skill

!`uv run "${CLAUDE_SKILL_DIR}/scripts/verificar_entorno.py"`

## Entrada

- Video: $video
- Tipo de resumen: $tipo
- Texto completo de la invocación: $ARGUMENTS

## Paso 1. Validar la entrada

1. Si en "Entorno detectado" la línea de ffmpeg dice NO ENCONTRADO, detente y responde con las instrucciones de instalación de esa línea.
2. Si "Video" está vacío, detente y pide la ruta del video.
3. Convierte la ruta del video en absoluta: expande `~` y resuelve las rutas relativas desde el directorio actual. Verifica con Glob que el archivo existe. Si no existe, revisa el texto completo de la invocación: puede ser una ruta con espacios que llegó sin comillas. Si aun así no existe, detente e informa la ruta que buscaste.
4. El tipo de resumen debe ser `corto`, `detallado` o `capitulos`. Si está vacío, usa `detallado`. Si es otro valor, usa `detallado` y avísalo en la respuesta final.
5. Define estos valores y úsalos en el resto de pasos:
   - CARPETA: carpeta donde está el video.
   - NOMBRE: nombre del video sin la extensión.
   - MP3: CARPETA/NOMBRE.mp3
   - SALIDA: CARPETA/NOMBRE_resumen

## Paso 2. Extraer el MP3

Ejecuta, reemplazando los valores entre `< >`:

```bash
ffmpeg -hide_banner -loglevel error -y -i "<ruta absoluta del video>" -vn -ac 1 -c:a libmp3lame -q:a 4 "<MP3>"
```

Si ffmpeg termina con error, muestra el mensaje y detente.

## Paso 3. Transcribir

Ejecuta con un timeout de 600000 ms:

```bash
uv run "${CLAUDE_SKILL_DIR}/scripts/transcribir.py" "<MP3>" --salida "<SALIDA>"
```

- Si en "Entorno detectado" la línea de GPU NVIDIA muestra el nombre de una tarjeta, agrega estas opciones justo después de `uv run`: `--with nvidia-cublas-cu12 --with "nvidia-cudnn-cu12>=9"`
- Si el texto de la invocación dice que el video está en otro idioma, agrega `--idioma <código ISO>` (por ejemplo `--idioma en`). Si dice que no se sabe el idioma, agrega `--idioma auto`.
- El script escribe su avance en `<SALIDA>/progreso.txt`. Si Claude Code pasa el comando a segundo plano por tiempo, no lo relances: lee `progreso.txt` hasta que diga `estado: TERMINADO` o `estado: ERROR`.
- Si termina en ERROR, muestra el contenido de `progreso.txt` y detente.

Al terminar, lee `<SALIDA>/metadata.json`. De ahí salen la duración, el idioma, el modelo, el dispositivo y la lista `bloques`.
Si `bloques` está vacía, el audio no tiene voz detectable: informa eso y detente.

## Paso 4. Leer la transcripción por bloques

Lee con Read cada archivo de la lista `bloques`, en orden. Por cada bloque anota los temas, los conceptos explicados, los comandos o herramientas mencionadas y las preguntas o tareas, cada uno con su timestamp.
No leas `transcripcion.md` completa: en videos largos supera el límite de lectura.

## Paso 5. Escribir el resumen

1. Lee la plantilla del tipo elegido:
   - corto: `${CLAUDE_SKILL_DIR}/templates/corto.md`
   - detallado: `${CLAUDE_SKILL_DIR}/templates/detallado.md`
   - capitulos: `${CLAUDE_SKILL_DIR}/templates/capitulos.md`
2. Llénala respetando sus secciones y las indicaciones de los comentarios `<!-- -->`. Los comentarios no van en el resultado.
3. Reemplaza los marcadores `{{...}}`: ARCHIVO es el nombre del video; DURACION, IDIOMA, MODELO y DISPOSITIVO salen de `metadata.json`; TITULO, TEMA y CAPITULO los defines tú a partir de la transcripción.
4. Guarda el resultado con Write en `<SALIDA>/resumen-<tipo>.md`.

## Paso 6. Responder

Responde con:

1. Las rutas del MP3, de `transcripcion.md` y del resumen.
2. Duración, idioma, modelo y dispositivo usados.
3. El resumen completo.

## Reglas

- Usa solo información que esté en la transcripción. No completes con conocimiento propio.
- Todo timestamp que escribas debe existir en la transcripción.
- Escribe el resumen en el idioma del video.
- Deja los términos técnicos en inglés tal como se dijeron (pipeline, commit, branch); no los traduzcas.
- Si un tramo de la transcripción no se entiende, dilo en vez de rellenarlo.
