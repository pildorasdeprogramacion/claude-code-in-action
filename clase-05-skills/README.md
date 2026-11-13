# Clase 5: Skills

Material de la clase de **skills** del curso Claude Code in Action: las diapositivas
y la skill completa que se construyó en el laboratorio, `/resumen-video`.

Un skill es una carpeta con un `SKILL.md` que le enseña a Claude a hacer una tarea
a tu manera. Claude solo carga el `name` y la `description`; el resto entra al
contexto cuando la tarea lo amerita o cuando la invocas con `/nombre`.

## Diapositivas de la clase

[`diapositivas-skills.pdf`](diapositivas-skills.pdf): qué es un skill, estructura
mínima, `name` y `description`, carga progresiva, alcances (empresa, usuario y
proyecto), cómo crear uno en tres pasos y la diferencia entre skills, MCP y hooks.

## La skill del laboratorio: `/resumen-video`

Toma un video, extrae el MP3 con ffmpeg, lo transcribe **en tu máquina** con
faster-whisper y le pide a Claude solo el resumen. La transcripción no gasta
tokens: Claude lee el texto ya transcrito, por bloques.

```
.claude/skills/resumen-video/
├── SKILL.md                    frontmatter + instrucciones paso a paso
├── scripts/
│   ├── verificar_entorno.py    revisa ffmpeg y GPU al invocar la skill
│   └── transcribir.py          faster-whisper, transcripción partida en bloques
└── templates/
    ├── corto.md
    ├── detallado.md
    └── capitulos.md            capítulos con timestamps para YouTube
```

### Requisitos

- [Claude Code](https://docs.claude.com/en/docs/claude-code) actualizado (`claude --version`).
- [uv](https://docs.astral.sh/uv/): ejecuta los scripts e instala sus dependencias solo.
- ffmpeg en el PATH: Windows `winget install --id Gyan.FFmpeg -e`, macOS `brew install ffmpeg`, Ubuntu/Debian `sudo apt install ffmpeg`.
- GPU NVIDIA, opcional. Con GPU usa el modelo `large-v3`; sin GPU usa `small` en CPU y tarda bastante más.

### Usarla

La skill está a nivel de proyecto, así que basta con abrir Claude Code en esta carpeta:

```bash
git clone https://github.com/pildorasdeprogramacion/claude-code-in-action.git
cd claude-code-in-action/clase-05-skills
claude
```

```
/resumen-video "C:\ruta\a\mi clase.mp4" capitulos
```

El segundo argumento es `corto`, `detallado` (por defecto) o `capitulos`.

Para tenerla en todos tus proyectos, copia la carpeta `resumen-video` a
`~/.claude/skills/` (en Windows, `C:\Users\<usuario>\.claude\skills\`).

### Qué genera

Junto al video:

- `<nombre>.mp3`
- `<nombre>_resumen/transcripcion.md`: transcripción completa con timestamps.
- `<nombre>_resumen/bloques/`: la misma transcripción partida cada 10 minutos.
- `<nombre>_resumen/metadata.json`: duración, idioma, modelo y dispositivo.
- `<nombre>_resumen/resumen-<tipo>.md`: el resumen.

### Qué mirar en el `SKILL.md`

- `description`: decide cuándo Claude invoca la skill por su cuenta.
- `argument-hint` y `arguments`: los argumentos llegan como `$video` y `$tipo`.
- `allowed-tools`: Bash acotado a `ffmpeg *` y `uv run *`, nunca Bash sin restricciones.
- `context: fork` y `agent`: la skill corre en un subagente y no llena tu conversación.
- La línea que empieza con `!` ejecuta `verificar_entorno.py` antes de que Claude lea las instrucciones.

## Antes de instalar un skill ajeno

Un skill puede traer scripts e instrucciones que se ejecutan en tu máquina. Lee
el `SKILL.md` y cada script antes de instalarlo, este incluido, y desconfía de
repositorios recién creados o sin historial.

Dudas: canal de Discord de Píldoras de Programación (sección Anthropic).
