"""Tests de la feature "cupón de descuento en el carrito".

Estos tests definen el contrato de la feature ANTES de implementarla.
Se usan en el laboratorio con /goal: Claude tiene que hacerlos pasar
sin modificar este archivo.

Contrato que describen:
- POST a la url con nombre "tienda:carrito_cupon" con {"codigo": "..."} aplica un cupón.
- El cupón "PILDORA10" descuenta el 10 % del total del carrito.
- Un código que no existe muestra el mensaje "no es válido" y no cambia el total.
- POST a la url con nombre "tienda:carrito_cupon_quitar" retira el cupón.
- El código se acepta en mayúsculas o minúsculas.
- El cupón vive en la sesión (igual que el carrito): sin modelos nuevos.
"""
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from .models import Categoria, Producto


class CuponesTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.categoria = Categoria.objects.create(
            nombre="Tecnología", slug="tecnologia", icono="cpu"
        )
        cls.producto = Producto.objects.create(
            categoria=cls.categoria,
            nombre="Audífonos Studio",
            slug="audifonos-studio",
            descripcion="Audífonos de prueba",
            precio=Decimal("129.90"),
            imagen="tienda/img/productos/audifonos.jpg",
            stock=10,
        )

    def _agregar(self, cantidad=1):
        return self.client.post(
            reverse("tienda:carrito_agregar", args=[self.producto.id]),
            {"cantidad": cantidad},
        )

    def _aplicar(self, codigo):
        return self.client.post(
            reverse("tienda:carrito_cupon"), {"codigo": codigo}, follow=True
        )

    def test_cupon_valido_descuenta_diez_por_ciento(self):
        self._agregar(2)  # 2 x 129,90 = 259,80
        respuesta = self._aplicar("PILDORA10")
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "PILDORA10")
        self.assertContains(respuesta, "233,82")  # 259,80 - 10 %

    def test_cupon_invalido_muestra_error_y_no_descuenta(self):
        self._agregar(2)
        respuesta = self._aplicar("NOEXISTE")
        self.assertContains(respuesta, "no es válido")
        self.assertContains(respuesta, "259,80")
        self.assertNotContains(respuesta, "233,82")

    def test_cupon_acepta_minusculas(self):
        self._agregar(2)
        respuesta = self._aplicar("pildora10")
        self.assertContains(respuesta, "233,82")

    def test_cupon_se_puede_quitar(self):
        self._agregar(2)
        self._aplicar("PILDORA10")
        respuesta = self.client.post(
            reverse("tienda:carrito_cupon_quitar"), follow=True
        )
        self.assertNotContains(respuesta, "PILDORA10")
        self.assertNotContains(respuesta, "233,82")
        self.assertContains(respuesta, "259,80")

    def test_cupon_sobrevive_entre_peticiones(self):
        self._agregar(2)
        self._aplicar("PILDORA10")
        respuesta = self.client.get(reverse("tienda:carrito"))
        self.assertContains(respuesta, "PILDORA10")
        self.assertContains(respuesta, "233,82")
