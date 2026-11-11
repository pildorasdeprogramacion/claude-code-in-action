from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from .models import Categoria, Producto


class BaseTienda(TestCase):
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
            destacado=True,
        )
        cls.agotado = Producto.objects.create(
            categoria=cls.categoria,
            nombre="Producto Agotado",
            slug="producto-agotado",
            descripcion="Sin stock",
            precio=Decimal("50.00"),
            imagen="tienda/img/productos/audifonos.jpg",
            stock=0,
        )


class ModelosTests(BaseTienda):
    def test_disponible_y_pocas_unidades(self):
        self.assertTrue(self.producto.disponible)
        self.assertFalse(self.producto.pocas_unidades)
        self.assertFalse(self.agotado.disponible)

        self.producto.stock = 3
        self.assertTrue(self.producto.pocas_unidades)

    def test_url_absoluta(self):
        self.assertEqual(
            self.producto.get_absolute_url(), "/producto/audifonos-studio/"
        )


class VistasTests(BaseTienda):
    def test_home_muestra_destacados(self):
        respuesta = self.client.get(reverse("tienda:home"))
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "Audífonos Studio")

    def test_catalogo_filtra_por_categoria(self):
        url = reverse("tienda:catalogo")
        respuesta = self.client.get(url, {"categoria": "tecnologia"})
        self.assertContains(respuesta, "Audífonos Studio")

        respuesta = self.client.get(url, {"categoria": "no-existe"})
        self.assertEqual(respuesta.status_code, 404)

    def test_catalogo_busqueda(self):
        respuesta = self.client.get(reverse("tienda:catalogo"), {"q": "audífonos"})
        self.assertContains(respuesta, "Audífonos Studio")
        self.assertNotContains(respuesta, "Producto Agotado")

    def test_catalogo_pagina_de_a_cuatro(self):
        for i in range(6):  # + los 2 del fixture = 8 productos -> 2 páginas
            Producto.objects.create(
                categoria=self.categoria,
                nombre=f"Producto extra {i}",
                slug=f"producto-extra-{i}",
                descripcion="Extra",
                precio=Decimal("10.00"),
                imagen="tienda/img/productos/audifonos.jpg",
                stock=5,
            )
        url = reverse("tienda:catalogo")

        p1 = self.client.get(url)
        self.assertEqual(len(p1.context["productos"]), 4)  # 4 por página
        self.assertEqual(p1.context["pagina"].paginator.num_pages, 2)

        # la paginación preserva el filtro de categoría
        p2 = self.client.get(url, {"categoria": "tecnologia", "page": 2})
        self.assertEqual(p2.status_code, 200)
        self.assertContains(p2, "categoria=tecnologia")  # los enlaces conservan el filtro

    def test_catalogo_paginacion_preserva_busqueda(self):
        for i in range(6):
            Producto.objects.create(
                categoria=self.categoria,
                nombre=f"Audífono extra {i}",
                slug=f"audifono-extra-{i}",
                descripcion="Audífonos de prueba",
                precio=Decimal("10.00"),
                imagen="tienda/img/productos/audifonos.jpg",
                stock=5,
            )
        respuesta = self.client.get(
            reverse("tienda:catalogo"), {"q": "audífono", "page": 2}
        )
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "q=aud")  # los enlaces de página conservan la búsqueda

    def test_catalogo_pagina_invalida_no_rompe(self):
        # get_page() normaliza páginas fuera de rango / no numéricas a una página válida
        respuesta = self.client.get(reverse("tienda:catalogo"), {"page": "999"})
        self.assertEqual(respuesta.status_code, 200)

    def test_detalle_producto(self):
        respuesta = self.client.get(self.producto.get_absolute_url())
        self.assertEqual(respuesta.status_code, 200)
        # con LANGUAGE_CODE="es" Django localiza el decimal con coma
        self.assertContains(respuesta, "129,90")


class CarritoTests(BaseTienda):
    def _agregar(self, producto, cantidad=1):
        return self.client.post(
            reverse("tienda:carrito_agregar", args=[producto.id]),
            {"cantidad": cantidad},
        )

    def test_agregar_y_ver_carrito(self):
        self._agregar(self.producto, 2)
        respuesta = self.client.get(reverse("tienda:carrito"))
        self.assertContains(respuesta, "Audífonos Studio")
        self.assertContains(respuesta, "259,80")  # subtotal 2 x 129,90 (formato es)

    def test_no_supera_el_stock(self):
        self._agregar(self.producto, 99)
        respuesta = self.client.get(reverse("tienda:carrito"))
        # el carrito limita la cantidad al stock disponible (10)
        self.assertContains(respuesta, 'value="10"')

    def test_producto_agotado_no_se_agrega(self):
        self._agregar(self.agotado)
        respuesta = self.client.get(reverse("tienda:carrito"))
        self.assertContains(respuesta, "Tu carrito está vacío")

    def test_quitar_del_carrito(self):
        self._agregar(self.producto)
        self.client.post(
            reverse("tienda:carrito_quitar", args=[self.producto.id])
        )
        respuesta = self.client.get(reverse("tienda:carrito"))
        self.assertContains(respuesta, "Tu carrito está vacío")
