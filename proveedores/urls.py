from django.urls import path
from . import views

app_name = "proveedores"

urlpatterns = [
    path("", views.ProveedorListView.as_view(), name="lista"),
    path("nuevo/", views.ProveedorCreateView.as_view(), name="crear"),
    path("<int:pk>/", views.ProveedorDetailView.as_view(), name="detalle"),
    path("<int:pk>/editar/", views.ProveedorUpdateView.as_view(), name="editar"),
    path("<int:pk>/inactivar/", views.proveedor_inactivar, name="inactivar"),
    # Catálogo por Excel
    path("plantilla-catalogo.xlsx", views.catalogo_plantilla, name="catalogo_plantilla"),
    path("<int:pk>/catalogo/cargar/", views.proveedor_catalogo_cargar, name="catalogo_cargar"),
    # RF-05 / RF-06 / RF-07 — materiales del proveedor
    path("<int:proveedor_pk>/materiales/nuevo/", views.proveedor_material_agregar, name="material_agregar"),
    path("materiales/<int:pk>/editar/", views.proveedor_material_editar, name="material_editar"),
    path("materiales/<int:pk>/disponibilidad/", views.proveedor_material_disponibilidad, name="material_disponibilidad"),
]
