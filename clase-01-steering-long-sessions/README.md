# PildoraStore 🛒

Tienda demo en **Django + Bootstrap 5** usada como laboratorio de los lives de
**Claude Code** (Píldoras de Programación).

## Puesta en marcha con uv (3 comandos)

Necesitas [uv](https://docs.astral.sh/uv/) instalado. uv descarga el Python
correcto, crea el `.venv` e instala Django por ti.

```bash
git clone https://github.com/pildorasdeprogramacion/claude-code-in-action.git
cd claude-code-in-action/clase-01-steering-long-sessions
uv sync
uv run python manage.py migrate && uv run python manage.py loaddata productos
uv run python manage.py runserver
```

Abre http://127.0.0.1:8000

Tests: `uv run python manage.py test` (13 tests deben pasar).

## Qué incluye

- Home con hero y productos destacados
- Catálogo con filtro por categoría, búsqueda y paginación
- Detalle de producto con productos relacionados
- Carrito basado en sesión (agregar, actualizar, quitar) con límite por stock
- Admin de Django (`uv run python manage.py createsuperuser`)

## Qué NO incluye (a propósito 😉)

Reseñas, cupones, wishlist y checkout quedan pendientes para implementarlos en
vivo con Claude Code. Ver `CLAUDE.md` y el laboratorio en `laboratorio/`.

## Diapositivas de la clase

[`diapositivas-steering-long-sessions.pdf`](diapositivas-steering-long-sessions.pdf): las 27 diapositivas de la clase (plan mode, `/compact`, rewind y `/goal`).

## Laboratorio: Steering long sessions

`laboratorio/LAB_steering_long_sessions.md` es la guía paso a paso del live:
plan mode, `/compact` (con y sin instrucciones), rewind y `/goal`, todo sobre
este proyecto. `laboratorio/tests_cupones.py` son los tests que usa `/goal`.

Fotos de producto: Unsplash (uso demo).
