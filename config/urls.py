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
    # --- CU-56 (RF-53) Recuperación de contraseña y CU-52 (RF-49) activación ---
    # Las dos usan el mismo mecanismo de token firmado de un solo uso; lo que
    # cambia es el texto de la pantalla, no la seguridad de fondo.
    path("clave/", auth_views.PasswordResetView.as_view(
        template_name="registration/password_reset_form.html",
        email_template_name="registration/password_reset_email.txt",
        subject_template_name="registration/password_reset_subject.txt",
        success_url="/clave/enviado/"), name="password_reset"),
    path("clave/enviado/", auth_views.PasswordResetDoneView.as_view(
        template_name="registration/password_reset_done.html"), name="password_reset_done"),
    path("clave/<uidb64>/<token>/", auth_views.PasswordResetConfirmView.as_view(
        template_name="registration/password_reset_confirm.html",
        success_url="/clave/listo/"), name="password_reset_confirm"),
    path("clave/listo/", auth_views.PasswordResetCompleteView.as_view(
        template_name="registration/password_reset_complete.html"), name="password_reset_complete"),
    # Cambio de contraseña con la sesión abierta: el usuario ya demostró quién
    # es, así que no tiene por qué esperar un correo para cambiarla.
    path("clave/cambiar/", auth_views.PasswordChangeView.as_view(
        template_name="registration/password_change_form.html",
        success_url="/clave/cambiada/"), name="password_change"),
    path("clave/cambiada/", auth_views.PasswordChangeDoneView.as_view(
        template_name="registration/password_change_done.html"), name="password_change_done"),
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
    path("auditoria/", include("auditoria.urls")),
    path("reportes/", include("reportes.urls")),
]

# En desarrollo, Django sirve los archivos subidos (RF-17, RF-26, RF-41).
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
