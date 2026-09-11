from django.urls import path
from . import api, views

app_name = "solicitudes"

urlpatterns = [
    # Búsqueda del buscador de materiales (CU-12)
    path("api/materiales/", api.buscar_materiales, name="api_materiales"),
    path("api/proveedores/", api.proveedores_de, name="api_proveedores"),
    path("", views.SolicitudListView.as_view(), name="lista"),
    path("nueva/", views.solicitud_crear, name="crear"),
    path("<int:pk>/", views.solicitud_detalle, name="detalle"),
    path("<int:pk>/editar/", views.solicitud_editar, name="editar"),
    path("detalle/<int:pk>/eliminar/", views.detalle_eliminar, name="detalle_eliminar"),
    path("adjunto/<int:pk>/eliminar/", views.adjunto_eliminar, name="adjunto_eliminar"),
    path("<int:pk>/enviar/", views.solicitud_enviar, name="enviar"),
    path("<int:pk>/resolver/<str:accion>/", views.solicitud_resolver, name="resolver"),
]
