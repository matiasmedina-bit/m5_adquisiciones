from django.urls import path
from . import views

app_name = "reportes"

urlpatterns = [
    path("", views.panel, name="panel"),
    # CU-42 a CU-45. La exportación (CU-46) va como ?formato=xlsx|pdf
    # sobre estas mismas URLs: es el mismo reporte, en otro envase.
    path("consumo/", views.consumo, name="consumo"),
    path("desviacion/", views.desviacion, name="desviacion"),
    path("mermas/", views.mermas, name="mermas"),
    path("compras/", views.compras, name="compras"),
]
