# Claude Code in Action

Proyectos y laboratorios del curso **Claude Code in Action** de Píldoras de Programación.
Cada clase con laboratorio tiene su propia carpeta, autocontenida: se clona el repo,
se entra a la carpeta de la clase y se sigue su guía.

| Clase | Tema | Carpeta | Diapositivas |
|---|---|---|---|
| 1 | Steering long sessions: plan mode, `/compact` y rewind | [`clase-01-steering-long-sessions`](clase-01-steering-long-sessions/) | [PDF](clase-01-steering-long-sessions/diapositivas-steering-long-sessions.pdf) |
| 5 | Skills: `SKILL.md`, carga progresiva y la skill `/resumen-video` | [`clase-05-skills`](clase-05-skills/) | [PDF](clase-05-skills/diapositivas-skills.pdf) |

## Requisitos

- [uv](https://docs.astral.sh/uv/) (descarga el Python correcto y crea el entorno de cada proyecto).
- [Claude Code](https://docs.claude.com/en/docs/claude-code) actualizado (`claude --version`).
- git.

## Empezar

```bash
git clone https://github.com/pildorasdeprogramacion/claude-code-in-action.git
cd claude-code-in-action/clase-01-steering-long-sessions
uv sync
```

Y luego la guía de la clase: `laboratorio/LAB_steering_long_sessions.md`.

La clase 5 no necesita `uv sync`: se entra a `clase-05-skills`, se abre `claude` y se sigue su README.

Dudas: canal de Discord de Píldoras de Programación (sección Anthropic).
