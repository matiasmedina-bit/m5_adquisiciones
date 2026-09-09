"""URLs raíz del proyecto M5 Adquisiciones."""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from usuarios.views import home, registro_solicitud

urlpatterns = [
    path("admin/", admin.site.urls),
    path("login/", auth_views.LoginView.as_view(template_name="registration/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("registro/", registro_solicitud, name="registro"),
    # Página de inicio (dashboard)
    path("", home, name="home"),
    # Módulos del incremento
    path("usuarios/", include("usuarios.urls")),
    path("proveedores/", include("proveedores.urls")),
    path("proyectos/", include("proyectos.urls")),
    path("inventario/", include("inventario.urls")),
    path("solicitudes/", include("solicitudes.urls")),
    path("adquisiciones/", include("adquisiciones.urls")),
    path("facturacion/", include("facturacion.urls")),
]

# En desarrollo, Django sirve los archivos subidos (RF-17, RF-26, RF-41).
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
