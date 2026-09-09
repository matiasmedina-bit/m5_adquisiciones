"""
Modelos del módulo de Seguridad y Usuarios.
Entidad Usuario del MERE, con sus subtipos (Jefe_Proyecto, Encargado_Adquisiciones,
Bodeguero). Cubre los CU-50, CU-51 y CU-52.
"""
from django.contrib.auth.models import AbstractUser
from django.db import models


class Usuario(AbstractUser):
    """
    Entidad Usuario. Hereda de AbstractUser de Django para reutilizar
    el manejo seguro de contraseñas (Contrasena_hash) y la autenticación.
    El campo 'username' se usa como identificador de inicio de sesión.
    """

    class Rol(models.TextChoices):
        ADMIN = "ADMIN", "Administrador"
        JEFE_PROYECTO = "JEFE_PROYECTO", "Jefe de Proyecto"
        ENCARGADO_ADQUISICIONES = "ENCARGADO_ADQUISICIONES", "Encargado de Adquisiciones"
        BODEGUERO = "BODEGUERO", "Bodeguero"
        # Incremento 2: quinto perfil del RBAC (RF-54), necesario para el
        # módulo de Facturación y Contabilidad (RF-40 a RF-44).
        CONTABILIDAD = "CONTABILIDAD", "Contabilidad"

    # Usuario_correo (se usa el email heredado, pero lo hacemos único y obligatorio)
    email = models.EmailField("Correo electrónico", unique=True)
    telefono = models.CharField("Teléfono", max_length=20, blank=True)
    rol = models.CharField("Rol", max_length=30, choices=Rol.choices, default=Rol.BODEGUERO)
    # Estado: True = activo, False = inactivo (CU-51)
    estado = models.BooleanField("Activo", default=True)
    pendiente_aprobacion = models.BooleanField("Pendiente de aprobación", default=False)

    class Meta:
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"
        ordering = ["username"]

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_rol_display()})"

    def save(self, *args, **kwargs):
        # Mantener sincronizado is_active con el campo de negocio 'estado'
        self.is_active = self.estado
        super().save(*args, **kwargs)


class PerfilJefeProyecto(models.Model):
    """Subtipo Jefe_Proyecto del MERE (JP_id, Area)."""
    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE, related_name="perfil_jefe")
    area = models.CharField("Área", max_length=100)

    class Meta:
        verbose_name = "Perfil Jefe de Proyecto"
        verbose_name_plural = "Perfiles Jefe de Proyecto"

    def __str__(self):
        return f"JP: {self.usuario.username} - {self.area}"


class PerfilEncargadoAdquisiciones(models.Model):
    """Subtipo Encargado_Adquisiciones del MERE (EA_id, Nivel_autorizacion)."""
    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE, related_name="perfil_encargado")
    nivel_autorizacion = models.PositiveSmallIntegerField("Nivel de autorización", default=1)

    class Meta:
        verbose_name = "Perfil Encargado de Adquisiciones"
        verbose_name_plural = "Perfiles Encargado de Adquisiciones"

    def __str__(self):
        return f"EA: {self.usuario.username} - Nivel {self.nivel_autorizacion}"


class PerfilBodeguero(models.Model):
    """Subtipo Bodeguero del MERE (Bod_id, Turno)."""
    class Turno(models.TextChoices):
        MANANA = "MANANA", "Mañana"
        TARDE = "TARDE", "Tarde"
        NOCHE = "NOCHE", "Noche"

    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE, related_name="perfil_bodeguero")
    turno = models.CharField("Turno", max_length=10, choices=Turno.choices, default=Turno.MANANA)

    class Meta:
        verbose_name = "Perfil Bodeguero"
        verbose_name_plural = "Perfiles Bodeguero"

    def __str__(self):
        return f"Bod: {self.usuario.username} - {self.get_turno_display()}"
