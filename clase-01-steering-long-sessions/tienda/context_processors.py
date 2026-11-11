from .carrito import Carrito
from .models import Categoria


def tienda_global(request):
    """Datos disponibles en todas las plantillas: navbar y contador del carrito."""
    return {
        "categorias_nav": Categoria.objects.all(),
        "carrito_items": len(Carrito(request)),
    }
