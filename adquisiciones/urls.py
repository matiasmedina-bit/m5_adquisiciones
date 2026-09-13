from django.urls import path
from . import views

app_name = "adquisiciones"

urlpatterns = [
    # Cotizaciones
    path("cotizaciones/", views.cotizacion_bandeja, name="cotizacion_bandeja"),
    path("cotizaciones/sm/<int:pk>/", views.cotizacion_sm, name="cotizacion_sm"),
    # Órdenes de compra
    path("ordenes/", views.orden_lista, name="orden_lista"),
    path("ordenes/<int:pk>/", views.orden_detalle, name="orden_detalle"),
    path("ordenes/<int:pk>/editar/", views.orden_editar, name="orden_editar"),
    path("ordenes/<int:pk>/pdf/", views.orden_pdf, name="orden_pdf"),
    # CU-47 — trazabilidad de material u orden de compra
    path("trazabilidad/", views.trazabilidad_buscar, name="trazabilidad"),
]
