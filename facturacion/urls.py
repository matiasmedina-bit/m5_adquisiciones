from django.urls import path
from . import views

app_name = "facturacion"

urlpatterns = [
    path("", views.factura_lista, name="lista"),
    path("nueva/", views.factura_crear, name="crear"),
    path("cuentas-por-pagar/", views.cuentas_por_pagar, name="cuentas_por_pagar"),
    path("exportar.csv", views.factura_export_csv, name="export_csv"),
    path("<int:pk>/", views.factura_detalle, name="detalle"),
    path("<int:pk>/desbloquear/", views.factura_desbloquear, name="desbloquear"),
]
