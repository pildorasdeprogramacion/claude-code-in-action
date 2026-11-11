from django.db import models
from django.urls import reverse


class Categoria(models.Model):
    nombre = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    icono = models.CharField(
        max_length=50,
        default="tag",
        help_text="Nombre del ícono de Bootstrap Icons (ej: 'laptop', 'bag-heart')",
    )

    class Meta:
        verbose_name = "categoría"
        verbose_name_plural = "categorías"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class Producto(models.Model):
    categoria = models.ForeignKey(
        Categoria, related_name="productos", on_delete=models.CASCADE
    )
    nombre = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    descripcion = models.TextField()
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    imagen = models.CharField(
        max_length=200,
        help_text="Ruta relativa dentro de static/ (ej: 'tienda/img/productos/foto.jpg')",
    )
    stock = models.PositiveIntegerField(default=0)
    destacado = models.BooleanField(default=False)
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-creado"]

    def __str__(self):
        return self.nombre

    def get_absolute_url(self):
        return reverse("tienda:detalle", args=[self.slug])

    @property
    def disponible(self):
        return self.stock > 0

    @property
    def pocas_unidades(self):
        return 0 < self.stock <= 5
