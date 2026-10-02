from django.urls import path
from . import views

app_name = "usuarios"

urlpatterns = [
    path("", views.UsuarioListView.as_view(), name="lista"),
    path("nuevo/", views.UsuarioCreateView.as_view(), name="crear"),
    path("<int:pk>/", views.UsuarioDetailView.as_view(), name="detalle"),
    path("<int:pk>/editar/", views.UsuarioUpdateView.as_view(), name="editar"),
    path("<int:pk>/estado/", views.usuario_cambiar_estado, name="cambiar_estado"),
    path("<int:pk>/eliminar/", views.usuario_eliminar, name="eliminar"),
    path("<int:pk>/revisar/", views.revisar_solicitud, name="revisar"),
    path("<int:pk>/aprobar/", views.aprobar_registro, name="aprobar"),
    path("<int:pk>/rechazar/", views.rechazar_registro, name="rechazar"),
    path("<int:pk>/reenviar-activacion/", views.reenviar_activacion, name="reenviar_activacion"),
    # Mi perfil: cada usuario administra sus propios datos
    path("mi-perfil/", views.mi_perfil, name="mi_perfil"),
    path("mi-perfil/cambios/<int:pk>/cancelar/", views.cancelar_cambio_perfil,
         name="cancelar_cambio"),
    path("cambios/<int:pk>/resolver/", views.resolver_cambio_perfil,
         name="resolver_cambio"),

    # Parámetros generales del sistema
    path("parametros/", views.parametros_sistema, name="parametros"),
]
