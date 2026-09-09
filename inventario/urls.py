from django.urls import path
from . import views

app_name = "inventario"

urlpatterns = [
    # Catálogo
    path("", views.MaterialListView.as_view(), name="lista"),
    path("nuevo/", views.MaterialCreateView.as_view(), name="crear"),
    path("<int:pk>/editar/", views.MaterialUpdateView.as_view(), name="editar"),
    # Bodega (Incremento 2)
    path("bodega/", views.bodega_panel, name="bodega_panel"),
    path("bodega/movimientos/", views.movimiento_lista, name="movimiento_lista"),
    path("bodega/entrada/", views.entrada_crear, name="entrada_crear"),
    path("bodega/salida/", views.salida_crear, name="salida_crear"),
    path("bodega/merma/", views.merma_crear, name="merma_crear"),
    path("bodega/devolucion-proveedor/", views.devolucion_proveedor_crear, name="devolucion_proveedor_crear"),
    path("bodega/prestamos/", views.prestamo_lista, name="prestamo_lista"),
    path("bodega/prestamos/nuevo/", views.prestamo_crear, name="prestamo_crear"),
    path("bodega/prestamos/<int:pk>/devolver/", views.prestamo_devolver, name="prestamo_devolver"),
]
