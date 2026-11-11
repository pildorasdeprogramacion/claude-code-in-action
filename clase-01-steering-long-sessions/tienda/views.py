from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .carrito import Carrito
from .models import Categoria, Producto


def home(request):
    destacados = Producto.objects.filter(destacado=True, stock__gt=0)[:4]
    return render(request, "tienda/home.html", {"destacados": destacados})


def catalogo(request):
    productos = Producto.objects.select_related("categoria").all()
    categoria_actual = None

    slug_categoria = request.GET.get("categoria")
    if slug_categoria:
        categoria_actual = get_object_or_404(Categoria, slug=slug_categoria)
        productos = productos.filter(categoria=categoria_actual)

    busqueda = request.GET.get("q", "").strip()
    if busqueda:
        productos = productos.filter(
            Q(nombre__icontains=busqueda) | Q(descripcion__icontains=busqueda)
        )

    paginator = Paginator(productos, 4)  # 4 productos por página
    pagina = paginator.get_page(request.GET.get("page"))

    # querystring con los filtros activos, sin el parámetro page,
    # para reutilizarlo en los enlaces de paginación
    parametros = request.GET.copy()
    parametros.pop("page", None)

    contexto = {
        "productos": pagina,
        "pagina": pagina,
        "parametros": parametros.urlencode(),
        "categoria_actual": categoria_actual,
        "busqueda": busqueda,
    }
    return render(request, "tienda/catalogo.html", contexto)


def detalle(request, slug):
    producto = get_object_or_404(
        Producto.objects.select_related("categoria"), slug=slug
    )
    relacionados = (
        Producto.objects.filter(categoria=producto.categoria)
        .exclude(id=producto.id)[:3]
    )
    contexto = {"producto": producto, "relacionados": relacionados}
    return render(request, "tienda/detalle.html", contexto)


def ver_carrito(request):
    return render(request, "tienda/carrito.html", {"carrito": Carrito(request)})


@require_POST
def carrito_agregar(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id)
    if not producto.disponible:
        messages.warning(request, f"{producto.nombre} está agotado.")
        return redirect(producto.get_absolute_url())

    cantidad = max(1, int(request.POST.get("cantidad", 1)))
    Carrito(request).agregar(producto, cantidad)
    messages.success(request, f"{producto.nombre} se agregó al carrito.")
    return redirect(request.POST.get("siguiente") or "tienda:carrito")


@require_POST
def carrito_actualizar(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id)
    cantidad = int(request.POST.get("cantidad", 1))
    Carrito(request).agregar(producto, cantidad, reemplazar=True)
    return redirect("tienda:carrito")


@require_POST
def carrito_quitar(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id)
    Carrito(request).quitar(producto)
    messages.info(request, f"{producto.nombre} se quitó del carrito.")
    return redirect("tienda:carrito")
