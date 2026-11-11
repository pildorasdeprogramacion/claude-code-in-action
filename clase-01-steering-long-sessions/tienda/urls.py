from django.urls import path

from . import views

app_name = "tienda"

urlpatterns = [
    path("", views.home, name="home"),
    path("catalogo/", views.catalogo, name="catalogo"),
    path("producto/<slug:slug>/", views.detalle, name="detalle"),
    path("carrito/", views.ver_carrito, name="carrito"),
    path("carrito/agregar/<int:producto_id>/", views.carrito_agregar, name="carrito_agregar"),
    path("carrito/actualizar/<int:producto_id>/", views.carrito_actualizar, name="carrito_actualizar"),
    path("carrito/quitar/<int:producto_id>/", views.carrito_quitar, name="carrito_quitar"),
]
