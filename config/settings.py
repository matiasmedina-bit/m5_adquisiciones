"""
Configuración de Django para el proyecto M5 Adquisiciones.
Sistema de Gestión de Adquisiciones e Inventario - Constructora M5 SpA
Incremento 2 - Scrum++
"""
from pathlib import Path
import os
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv("SECRET_KEY", "clave-insegura-solo-para-desarrollo")
DEBUG = os.getenv("DEBUG", "True").lower() == "true"
ALLOWED_HOSTS = [h.strip() for h in os.getenv("ALLOWED_HOSTS", "127.0.0.1,localhost").split(",") if h.strip()]
CSRF_TRUSTED_ORIGINS = [
    o.strip() for o in os.getenv("CSRF_TRUSTED_ORIGINS", "").split(",") if o.strip()
] or [f"http://{h}" for h in ALLOWED_HOSTS if h != "*"]

# Aplicaciones
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Apps del proyecto (un app por módulo del incremento)
    "usuarios",       # CU-50, CU-51, CU-52  (Seguridad y usuarios)
    "proveedores",    # CU-01 a CU-05  + Inc.2: RF-05/06/07 (materiales del proveedor)
    "proyectos",      # CU-06 a CU-10  (Proyecto + Itemizado)  + Inc.2: RF-14
    "inventario",     # Catálogo de materiales  + Inc.2: RF-28 a RF-37 (bodega)
    "solicitudes",    # CU-11..CU-17  + Inc.2: RF-16 (justificación), RF-17 (adjuntos)
    "adquisiciones",  # Inc.2: RF-19 a RF-27, RF-38, RF-39 (cotizaciones y órdenes de compra)
    "facturacion",    # Inc.2: RF-40 a RF-44 (facturación y contabilidad)
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "usuarios.context_processors.pendientes_count",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# Base de datos relacional PostgreSQL
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("DB_NAME", "m5_adquisiciones"),
        "USER": os.getenv("DB_USER", "postgres"),
        "PASSWORD": os.getenv("DB_PASSWORD", "postgres"),
        "HOST": os.getenv("DB_HOST", "127.0.0.1"),
        "PORT": os.getenv("DB_PORT", "5432"),
    }
}

# Modelo de usuario personalizado (entidad Usuario del MERE)
AUTH_USER_MODEL = "usuarios.Usuario"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# Internacionalización (Chile)
LANGUAGE_CODE = "es-cl"
TIME_ZONE = "America/Santiago"
USE_I18N = True
USE_TZ = True

# Archivos estáticos
STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

# Archivos subidos por los usuarios (RF-17 adjuntos de solicitud, RF-26 PDF de OC,
# RF-41 archivo digital de factura). En producción se serviría desde el servidor
# físico de M5; en desarrollo Django los sirve cuando DEBUG=True (ver config/urls.py).
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Redirecciones de autenticación
LOGIN_URL = "/login/"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/login/"

# --- Correo (RF-27 envío de OC al proveedor, RF-33 aviso a Administración) ---
# Por defecto la consola: los correos se imprimen en la terminal del runserver,
# suficiente para la demo. Para envío real, definir EMAIL_* en el .env.
EMAIL_BACKEND = os.getenv(
    "EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend"
)
EMAIL_HOST = os.getenv("EMAIL_HOST", "")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS", "True").lower() == "true"
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "adquisiciones@m5.cl")

# --- Datos de facturación de Constructora M5 SpA (RF-23 autocompletado de la OC) ---
EMPRESA_RAZON_SOCIAL = os.getenv("EMPRESA_RAZON_SOCIAL", "Constructora M5 SpA")
EMPRESA_RUT = os.getenv("EMPRESA_RUT", "76.123.456-7")
EMPRESA_GIRO = os.getenv("EMPRESA_GIRO", "Construcción y habilitación de espacios")
EMPRESA_DIRECCION = os.getenv("EMPRESA_DIRECCION", "Ictinos 716, La Reina, Santiago")

# --- Parámetro de negocio (RF-41): tolerancia % entre el monto de la factura y
# el de la(s) OC asociada(s). Si se excede, la factura queda BLOQUEADA hasta que
# Administración la desbloquee (RF-42). Configurable por .env. ---
FACTURA_TOLERANCIA_PCT = float(os.getenv("FACTURA_TOLERANCIA_PCT", "5"))
