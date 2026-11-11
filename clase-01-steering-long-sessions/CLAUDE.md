# PildoraStore — instrucciones del proyecto

## Sobre el proyecto
Tienda demo construida con Django 5+ y Bootstrap 5.3 (vía CDN). Base de datos SQLite.
Es el laboratorio de los lives de Claude Code (workflow Explore → Plan → Code → Commit
y, en esta entrega, Steering long sessions: plan mode, /compact, rewind y /goal).

## Entorno
El proyecto usa **uv**. Nunca uses `pip install` ni `python` a secas: todo va con `uv run`.

## Comandos
- Instalar/sincronizar dependencias: `uv sync`
- Ejecutar tests: `uv run python manage.py test`
- Ejecutar solo un módulo de tests: `uv run python manage.py test tienda.tests_cupones`
- Levantar servidor: `uv run python manage.py runserver`
- Migraciones: `uv run python manage.py makemigrations && uv run python manage.py migrate`
- Cargar datos de ejemplo: `uv run python manage.py loaddata productos`

## Convenciones
- Todo el código, comentarios y nombres de plantillas en español.
- UI solo con clases de Bootstrap; evitar CSS custom salvo lo mínimo en `base.html`.
- Las imágenes de productos viven en `tienda/static/tienda/img/productos/` y los
  modelos guardan la ruta relativa (campo `imagen`), no ImageField.
- El carrito vive en la sesión (`tienda/carrito.py`); no crear modelos de orden todavía.
- No hay autenticación de usuarios en la tienda (el admin de Django no cuenta):
  ninguna feature de cara al cliente debe depender de `request.user`.
- Toda vista nueva debe tener al menos un test en `tienda/tests.py`.
- Antes de hacer commit, ejecutar los tests.

## Pendientes conocidos (para implementar en vivo)
- Reseñas de productos.
- Cupones de descuento (los tests ya existen en `laboratorio/tests_cupones.py`).
- Wishlist.
- Checkout (el botón "Ir a pagar" está deshabilitado a propósito).
