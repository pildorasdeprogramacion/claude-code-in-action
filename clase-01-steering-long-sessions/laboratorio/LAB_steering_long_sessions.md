# Laboratorio · Clase 1 · Steering long sessions con Claude Code

**Proyecto:** PildoraStore (Django + Bootstrap 5, gestionado con uv)
**Duración estimada:** 90–120 min
**Curso:** Claude Code in Action (Píldoras de Programación)
**Qué vamos a practicar:** plan mode → `/compact` sin instrucciones → rewind → `/compact` con instrucciones → `/goal`

> Requiere Claude Code **v2.1.139 o superior** (`/goal` no existe en versiones anteriores).
> Verifícalo con `claude --version`.

La idea del laboratorio no es "terminar features": es **ver con nuestros propios ojos**
qué pasa en una sesión larga y cómo la dirigimos. Por eso cada fase termina con un
"qué observar" y usamos **git como testigo**: antes de cada fase hacemos commit, y
después miramos `git status` / `git diff --stat` para saber exactamente qué cambió.

---

## Fase 0 · Preparación (10 min)

### 0.1 Levantar el proyecto con uv

```bash
git clone https://github.com/pildorasdeprogramacion/claude-code-in-action.git
cd claude-code-in-action/clase-01-steering-long-sessions
uv sync                                   # crea .venv e instala Django
uv run python manage.py migrate
uv run python manage.py loaddata productos
uv run python manage.py test              # deben pasar 13 tests
```

Opcional, para ver la tienda: `uv run python manage.py runserver` → http://127.0.0.1:8000

### 0.2 Git como testigo

```bash
git status            # debe estar limpio
git log --oneline -3
```

Si `git status` muestra cambios, haz `git add -A && git commit -m "punto de partida del laboratorio"`.

> Si descargaste el `.zip` en vez de clonar, la carpeta ya trae su propio repo de git con un commit.
> Si no lo trae, crea uno: `git init && git add -A && git commit -m "punto de partida del laboratorio"`.

### 0.3 Arrancar Claude Code

```bash
claude
```

Dentro de la sesión, dos comandos que vamos a usar todo el rato:

- `/context` → cuánto del context window está ocupado y por qué.
- `/rewind` (o `Esc` `Esc` con el input vacío) → el menú de checkpoints.

Ejecuta `/context` ahora mismo y anota el porcentaje: es el **punto cero**.

---

## Fase 1 · Plan mode: delimitar antes de arrancar (25 min)

**Concepto:** iterar un plan es mucho más barato que limpiar un desastre.
**Feature:** reseñas de productos.

### 1.1 Entrar en plan mode

Pulsa `Shift+Tab` hasta que el indicador diga **plan mode** (o arranca con `claude --permission-mode plan`).
En plan mode Claude investiga y propone, pero **no escribe código**.

### 1.2 El pedido inicial (a propósito, poco delimitado)

Pega esto tal cual:

```
Quiero agregar reseñas de productos a la tienda. Investiga el proyecto y proponme un plan.
```

Deja que Claude lea el repo. Cuando entregue el plan, **léelo a conciencia**.
Casi seguro el plan trae una o varias de estas decisiones que no queremos:

- Un modelo `Resena` con `ForeignKey(User)` → la tienda **no tiene login** (está en `CLAUDE.md`).
- Un `ModelForm` con validaciones que no pedimos, o edición/borrado de reseñas.
- Tocar `base.html` o meter CSS custom.
- Calcular el promedio en la plantilla en vez de en el modelo.

### 1.3 Iterar el plan (mínimo 3 vueltas)

Cada corrección es un mensaje corto. No aprobamos hasta que el plan diga exactamente lo que queremos.

**Vuelta 1 — quitar lo que sobra:**
```
No hay usuarios en la tienda: la reseña lleva un campo `nombre` libre (CharField), un `puntaje` de 1 a 5 y un `comentario`. Sin edición ni borrado. Ajusta el plan.
```

**Vuelta 2 — precisar dónde va cada cosa:**
```
El promedio de puntaje y el número de reseñas van como propiedades del modelo Producto, no se calculan en la plantilla. El formulario va en la página de detalle, debajo de los productos relacionados. Solo clases de Bootstrap.
```

**Vuelta 3 — cerrar con tests y pasos:**
```
Agrega al plan los tests: crear una reseña por POST, el promedio se calcula bien con 2 reseñas, y un puntaje fuera de 1..5 no se guarda. Al final el plan debe listar los archivos exactos que vas a tocar y el orden. Nada más.
```

> **Qué observar:** el plan cambia sin que se haya escrito una sola línea. Cada vuelta
> costó un mensaje. Corregir esto mismo después de implementado costaría rewind + reimplementar.

### 1.4 Aprobar y ejecutar

Cuando el plan esté como quieres, sal de plan mode (`Shift+Tab`) y aprueba:

```
Aprobado. Ejecuta el plan tal cual. Al terminar corre `uv run python manage.py test` y muéstrame el resultado.
```

Cuando termine:

```bash
uv run python manage.py test        # todos en verde (13 + los nuevos)
git status                          # migración 0002, models, views, urls, template, tests
git add -A && git commit -m "feat: reseñas de productos (plan mode)"
```

Ejecuta `/context` y anota el porcentaje. Ya se llenó bastante: exploración + plan + implementación.

---

## Fase 2 · `/compact` sin instrucciones (15 min)

**Concepto:** sin instrucciones, el resumen es genérico y tiende a parafrasear.

### 2.1 Sembrar un dato literal en el contexto

Vamos a meter en la conversación algo que **solo sirve si queda literal**: un error de tests.

```bash
cp laboratorio/tests_cupones.py tienda/tests_cupones.py
```

Y en Claude Code:

```
Acabo de agregar tienda/tests_cupones.py. Corre `uv run python manage.py test tienda.tests_cupones` y muéstrame el error tal cual, sin arreglar nada todavía.
```

El error que debe aparecer (anótalo, lo vamos a usar de referencia):

```
django.urls.exceptions.NoReverseMatch: Reverse for 'carrito_cupon' not found.
'carrito_cupon' is not a valid view function or pattern name.
```

### 2.2 Compactar "a secas"

```
/compact
```

Sin nada más. Cuando termine, mira `/context`: baja bastante.

### 2.3 Las tres preguntas

Hazle estas tres preguntas a Claude, **una por una**, y pídele que responda solo desde lo que recuerda:

```
Sin abrir ningún archivo ni correr nada: ¿cuál es el comando exacto que usamos para correr los tests de cupones?
```
```
Sin abrir archivos: ¿cuál fue el mensaje de error literal, palabra por palabra?
```
```
Sin abrir archivos: lista las rutas exactas de los archivos que tocamos para las reseñas.
```

> **Qué observar:** apunta las tres respuestas en una tabla (las vamos a comparar en la Fase 4).
> Lo típico: el comando sale bien o casi; el error sale **parafraseado** ("faltaba una url de cupón")
> y alguna ruta se pierde o se inventa. No es un fallo de Claude: es que nadie le dijo qué conservar.

| Pregunta | Sin instrucciones (Fase 2) | Con instrucciones (Fase 4) |
|---|---|---|
| comando de tests | | |
| error literal | | |
| rutas tocadas | | |

---

## Fase 3 · Rewind: tomar un camino equivocado y volver (25 min)

**Concepto:** corregir con más prompts deja los intentos fallidos en el contexto; con rewind desaparecen.
**Feature:** wishlist. Vamos a pedirla **mal a propósito** para ver el desvío.

### 3.1 Punto de control con git

```bash
git status     # limpio (excepto tienda/tests_cupones.py que aún no commiteamos)
git add tienda/tests_cupones.py && git commit -m "test: contrato de cupones (aún sin implementar)"
```

Anota en Claude Code el número del prompt que vas a enviar: el rewind lista los prompts, así lo vas a ubicar fácil.

### 3.2 El prompt equivocado (sin plan mode, a propósito)

```
Agrega una wishlist: crea un modelo Wishlist relacionado con User, vistas para agregar y quitar productos protegidas con login_required, la migración, y un enlace "Mi wishlist" en el navbar. Corre makemigrations al terminar.
```

Deja que trabaje. Cuando termine, mira los daños:

```bash
git status
```

Vas a ver algo como: `tienda/models.py`, `tienda/views.py`, `tienda/urls.py`, `base.html`
modificados, y un archivo **nuevo** `tienda/migrations/0003_wishlist.py` (o similar).

Abre la tienda o corre los tests: la wishlist exige login y la tienda no tiene login.
**Ese es el camino equivocado.** Y si seguimos "a punta de prompts" (quita el login… no,
usa la sesión… no, borra el modelo…) cada intento se queda en el contexto.

### 3.3 Volver con rewind

1. Asegúrate de que el input esté **vacío** y pulsa `Esc` `Esc` (o escribe `/rewind`).
2. Selecciona el prompt de la wishlist (el de 3.2).
3. Elige **Restore code and conversation**.

Claude Code deja en el input el texto del prompt original: **bórralo**, no lo reenvíes.

### 3.4 Verificar qué revirtió (y qué no)

```bash
git status
```

> **Qué observar — la limitación en vivo:** los archivos que Claude editó con sus
> herramientas (`models.py`, `views.py`, `urls.py`, `base.html`) **volvieron**.
> Pero la migración `0003_...py` **sigue ahí**: la creó `makemigrations`, es decir, un
> comando bash. Rewind no rastrea cambios hechos por bash. Bórrala a mano:

```bash
rm tienda/migrations/0003_*.py
git status      # ahora sí, limpio
```

Y en la conversación de Claude Code, el desvío completo ya no existe: `/context` debe haber bajado.

### 3.5 El prompt correcto

Ahora sí, desde el punto bueno:

```
Agrega una wishlist guardada en la sesión, igual que el carrito (mira tienda/carrito.py). Sin modelos ni migraciones, sin login. Vistas para agregar y quitar por POST, una página /wishlist/ que liste los productos, y un botón "♡ Guardar" en la card de producto. Dos tests: agregar y quitar. Corre los tests al terminar.
```

```bash
uv run python manage.py test
git add -A && git commit -m "feat: wishlist en sesión (después de rewind)"
```

> **Cierre de la fase:** dos formas de corregir el mismo error. Con prompts hubiéramos
> tenido 3–4 mensajes más y el modelo Wishlist "vivo" en el contexto. Con rewind:
> un menú, un prompt bueno, y el contexto limpio.

---

## Fase 4 · `/compact` con instrucciones (10 min)

**Concepto:** una buena instrucción dice qué conservar, qué descartar y qué debe quedar literal.

### 4.1 Volver a sembrar el dato literal

Los tests de cupones siguen fallando (todavía no existe la feature). Los corremos otra vez para que el error esté en el contexto reciente:

```
Corre `uv run python manage.py test tienda.tests_cupones` y muéstrame el error tal cual. No lo arregles.
```

### 4.2 Compactar con instrucciones

```
/compact Conserva literal: el comando exacto para correr los tests de cupones, el mensaje de error completo palabra por palabra, y las rutas exactas de todos los archivos que hemos modificado en la sesión (reseñas y wishlist). Conserva las convenciones de CLAUDE.md que aplicamos (sin login, todo en sesión, solo Bootstrap). Descarta la exploración inicial del repo y el intento fallido de wishlist con modelo.
```

### 4.3 Las mismas tres preguntas

Repite las tres preguntas de la Fase 2.3 y completa la columna derecha de la tabla.

> **Qué observar:** el error sale palabra por palabra, las rutas están todas.
> El texto después de `/compact` le llegó directo al modelo que hizo el resumen.

---

## Fase 5 · `/goal`: soltar el timón con condiciones (25 min)

**Concepto:** describes "terminado", no los pasos. Otro modelo (pequeño y rápido) decide si se cumplió.
**Feature:** cupones de descuento. **Los tests ya definen la feature** (`tienda/tests_cupones.py`).

### 5.1 Leer el contrato

Abre `tienda/tests_cupones.py` y lee qué exige: dos urls con nombre
(`tienda:carrito_cupon` y `tienda:carrito_cupon_quitar`), el código `PILDORA10`
descuenta 10 %, el mensaje "no es válido", minúsculas aceptadas, el cupón vive en la sesión.

Esto es lo importante: **nosotros no le vamos a decir a Claude cómo hacerlo**. Los
tests son la definición de "terminado".

### 5.2 Escribir la condición (las tres partes)

Antes de enviarla, identifícalas:

- **Estado final medible:** los tests terminan con exit code 0.
- **Prueba explícita:** el comando concreto y su salida en la conversación.
- **Restricciones:** no tocar los tests, no crear modelos ni migraciones.

```
/goal `uv run python manage.py test` termina con exit code 0 e incluye los 5 tests de tienda.tests_cupones en verde; la salida completa del comando aparece en la conversación; `git diff --stat tienda/tests.py tienda/tests_cupones.py` no muestra cambios; y no se creó ningún archivo nuevo en tienda/migrations/. Detente después de 15 turnos si no lo logras.
```

> Nota sobre permisos: `/goal` no cambia tu modo de permisos. En modo manual Claude te va a
> pedir aprobación para correr comandos que no estén permitidos; si quieres verlo correr
> solo, activa auto mode (`Shift+Tab`) antes de lanzar el goal.

### 5.3 Mientras corre

- Arriba aparece el indicador **◎ /goal active**.
- Después de cada turno el evaluador deja su veredicto; pulsa `Ctrl+O` para ver **la razón**.
- `/goal` sin argumentos muestra turnos, tokens y la última razón del evaluador.
- `/goal clear` lo cancela si se te va de las manos.

> **Qué observar:** cuántos turnos necesitó, y **qué dijo el evaluador** en los turnos
> que devolvió "no": normalmente algo como "los tests aún no pasan" o "no se ve la salida
> del comando en la conversación". Esa segunda razón es la clave: el evaluador solo ve
> lo que Claude muestra, no corre nada por su cuenta.

### 5.4 Verificar a mano (siempre)

El evaluador dijo "cumplido". Ahora lo comprobamos nosotros, como si fuera un PR de un compañero:

```bash
uv run python manage.py test               # 18+ tests en verde
git diff --stat tienda/tests.py tienda/tests_cupones.py   # vacío
git status                                 # sin migraciones nuevas
uv run python manage.py runserver          # agrega algo al carrito y prueba PILDORA10
```

```bash
git add -A && git commit -m "feat: cupones de descuento (/goal)"
```

---

## Fase 6 · Cierre (5 min)

Repasen la tabla de la Fase 2/4 y el `git log`:

```bash
git log --oneline
```

Cuatro commits, cuatro hábitos:

| Commit | Hábito | Qué vimos |
|---|---|---|
| reseñas | plan mode | 3 vueltas al plan, cero líneas de código desperdiciadas |
| wishlist | rewind | el desvío desapareció del contexto; la migración por bash no |
| (conversación) | `/compact` | sin instrucciones parafrasea; con instrucciones conserva literal |
| cupones | `/goal` | los tests fueron la definición de "terminado"; otro modelo evaluó |

**La conclusión del capítulo:** cuanto más corriges en el camino, más se alarga todo.
La solución no es corregir más, sino corregir mejor y en el momento correcto.

### Tarea

1. Implementa el checkout (el botón "Ir a pagar") **solo con plan mode + /goal**. Primero
   escribe los tests, después el goal. Sube el `git log` y la condición que usaste.
2. Prueba `/rewind` → **Summarize from here** en una sesión tuya y cuenta cuánto bajó `/context`.

---

## Apéndice · Si algo sale distinto

- **Claude no toma el camino equivocado en la Fase 3** (por ejemplo, avisa que no hay login).
  Insiste: *"Hazlo con User igual, después vemos el login."* El objetivo es tener algo que revertir.
- **El menú de rewind no muestra "Restore code"**: solo aparece si hay ediciones de archivo
  rastreadas después de ese checkpoint. Si Claude hizo todo por bash, solo verás
  "Restore conversation" → usa `git checkout -- .` y `git clean -fd` para el código.
- **`/goal` no existe**: versión anterior a 2.1.139. Actualiza Claude Code.
- **El goal termina "cumplido" pero los tests no pasan**: el evaluador solo mira la
  conversación. Es exactamente la lección de 5.4: verificar siempre a mano. Vuelve a lanzar
  el goal pidiendo que la salida completa del comando aparezca en la conversación.
- **Las respuestas de la Fase 2 salieron perfectas**: pasa. Aun así compara en la Fase 4 la
  *longitud* y *precisión*; y recuerda que el resumen guiado es reproducible, el genérico no.
- **`/compact` no baja `/context` casi nada**: si la sesión es corta el resumen pesa parecido
  al original. Es normal en un laboratorio; en una sesión de 2 horas la diferencia es grande.
