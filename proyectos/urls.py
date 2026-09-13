from django.urls import path
from . import views

app_name = "proyectos"

urlpatterns = [
    path("", views.ProyectoListView.as_view(), name="lista"),
    path("nuevo/", views.ProyectoCreateView.as_view(), name="crear"),
    path("<int:pk>/", views.ProyectoDetailView.as_view(), name="detalle"),
    path("<int:pk>/editar/", views.ProyectoUpdateView.as_view(), name="editar"),
    path("<int:pk>/pdf/", views.proyecto_pdf, name="pdf"),
    path("<int:proyecto_pk>/itemizado/nuevo/", views.itemizado_crear, name="itemizado_crear"),
    path("itemizado/<int:pk>/editar/", views.itemizado_editar, name="itemizado_editar"),
    # CU-54 — archivos del proyecto clasificados por tipo de documento
    path("<int:proyecto_pk>/archivos/subir/", views.archivo_subir, name="archivo_subir"),
    path("archivo/<int:pk>/eliminar/", views.archivo_eliminar, name="archivo_eliminar"),
    path("tipos-documento/", views.TipoDocumentoListView.as_view(), name="tipos_documento"),
    path("tipos-documento/nuevo/", views.tipo_documento_crear, name="tipo_documento_crear"),
]
