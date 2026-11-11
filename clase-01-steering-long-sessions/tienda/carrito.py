"""Carrito de compras basado en la sesión del usuario.

No requiere autenticación: los items viven en request.session["carrito"]
con la forma {producto_id: cantidad}.
"""
from decimal import Decimal

from .models import Producto

CLAVE_SESION = "carrito"


class Carrito:
    def __init__(self, request):
        self.session = request.session
        carrito = self.session.get(CLAVE_SESION)
        if carrito is None:
            carrito = self.session[CLAVE_SESION] = {}
        self.carrito = carrito

    def _guardar(self):
        self.session.modified = True

    def agregar(self, producto, cantidad=1, reemplazar=False):
        pid = str(producto.id)
        actual = 0 if reemplazar else self.carrito.get(pid, 0)
        # nunca permitir más unidades que el stock disponible
        self.carrito[pid] = min(actual + cantidad, producto.stock)
        if self.carrito[pid] <= 0:
            self.carrito.pop(pid, None)
        self._guardar()

    def quitar(self, producto):
        self.carrito.pop(str(producto.id), None)
        self._guardar()

    def vaciar(self):
        self.session[CLAVE_SESION] = {}
        self.carrito = self.session[CLAVE_SESION]
        self._guardar()

    def __iter__(self):
        productos = Producto.objects.filter(id__in=self.carrito.keys())
        for producto in productos:
            cantidad = self.carrito[str(producto.id)]
            yield {
                "producto": producto,
                "cantidad": cantidad,
                "subtotal": producto.precio * cantidad,
            }

    def __len__(self):
        return sum(self.carrito.values())

    @property
    def total(self):
        return sum(
            (item["subtotal"] for item in self), start=Decimal("0")
        )
