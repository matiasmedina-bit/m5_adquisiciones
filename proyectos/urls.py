from django.urls import path
from . import views

app_name = "proyectos"

urlpatterns = [
    path("", views.ProyectoListView.as_view(), name="lista"),
    path("nuevo/", views.ProyectoCreateView.as_view(), name="crear"),
    path("<int:pk>/", views.ProyectoDetailView.as_view(), name="detalle"),
    path("<int:pk>/editar/", views.ProyectoUpdateView.as_view(), name="editar"),
    path("<int:proyecto_pk>/itemizado/nuevo/", views.itemizado_crear, name="itemizado_crear"),
    path("itemizado/<int:pk>/editar/", views.itemizado_editar, name="itemizado_editar"),
]
