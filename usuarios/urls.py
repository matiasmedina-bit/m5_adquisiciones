from django.urls import path
from . import views

app_name = "usuarios"

urlpatterns = [
    path("", views.UsuarioListView.as_view(), name="lista"),
    path("nuevo/", views.UsuarioCreateView.as_view(), name="crear"),
    path("<int:pk>/", views.UsuarioDetailView.as_view(), name="detalle"),
    path("<int:pk>/editar/", views.UsuarioUpdateView.as_view(), name="editar"),
    path("<int:pk>/estado/", views.usuario_cambiar_estado, name="cambiar_estado"),
    path("<int:pk>/aprobar/", views.aprobar_registro, name="aprobar"),
    path("<int:pk>/rechazar/", views.rechazar_registro, name="rechazar"),
]
