"""
Modelos del módulo de Seguridad y Usuarios.
Entidad Usuario del MERE, con sus subtipos (Jefe_Proyecto, Encargado_Adquisiciones,
Bodeguero). Cubre los CU-50, CU-51 y CU-52.
"""
from django.contrib.auth.models import AbstractUser
from decimal import Decimal
from django.core.validators import MinValueValidator, MaxValueValidator
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
    # Foto de perfil. Opcional: mientras no haya una, la interfaz pinta la
    # inicial del usuario, así que nadie queda obligado a subir nada.
    foto = models.ImageField("Foto de perfil", upload_to="perfiles/", blank=True)
    rol = models.CharField("Rol", max_length=30, choices=Rol.choices, default=Rol.BODEGUERO)
    # Estado: True = activo, False = inactivo (CU-51)
    estado = models.BooleanField("Activo", default=True)
    pendiente_aprobacion = models.BooleanField("Pendiente de aprobación", default=False)

    # `createsuperuser` sólo pregunta por lo que esté acá. Sin `rol`, el primer
    # administrador del sistema quedaba creado como BODEGUERO —el default del
    # campo— y no podía entrar a Usuarios ni a Parámetros. Es el clásico error
    # de día de instalación: el sistema queda arriba y nadie puede administrarlo.
    REQUIRED_FIELDS = ["email", "rol"]

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

    @property
    def iniciales(self):
        """Dos letras para el avatar cuando no hay foto: iniciales del nombre
        y apellido, o la primera del usuario si no tiene nombre cargado."""
        partes = [p for p in (self.first_name, self.last_name) if p]
        if partes:
            return "".join(p[0] for p in partes[:2]).upper()
        return (self.username[:1] or "?").upper()

    def registros_que_impiden_borrarlo(self):
        """
        Cuenta lo que esta cuenta dejó escrito en el sistema.

        Las relaciones hacia Usuario son PROTECT a propósito: una solicitud, una
        orden de compra o un movimiento de bodega tienen que seguir diciendo
        quién los hizo aunque la persona ya no trabaje en M5. Por eso una cuenta
        con historial no se borra, se inactiva.

        Devuelve [(etiqueta, cantidad)] con lo que la retiene, o [] si está
        limpia y se puede eliminar de verdad.
        """
        relaciones = [
            ("solicitudes de material", "solicitudes_emitidas"),
            ("adjuntos de solicitudes", "adjuntos_subidos"),
            ("cotizaciones", "cotizaciones_creadas"),
            ("órdenes de compra emitidas", "ordenes_creadas"),
            ("órdenes de compra aprobadas", "ordenes_aprobadas"),
            ("movimientos de bodega", "movimientos_registrados"),
            ("préstamos recibidos", "prestamos_recibidos"),
            ("préstamos registrados", "prestamos_registrados"),
            ("facturas registradas", "facturas_registradas"),
            ("proyectos a su cargo", "proyectos_a_cargo"),
            ("archivos de proyecto subidos", "archivos_proyecto_subidos"),
        ]
        encontrados = []
        for etiqueta, acceso in relaciones:
            gestor = getattr(self, acceso, None)
            if gestor is None:
                continue
            total = gestor.count()
            if total:
                encontrados.append((etiqueta, total))
        return encontrados


class SolicitudCambioPerfil(models.Model):
    """
    Pedido de un usuario para que le cambien un dato que no puede editar solo.

    El nombre, el teléfono y la foto los cambia cada uno desde su perfil. El
    correo, el nombre de usuario y el rol no: el correo es con lo que se
    recuperan las contraseñas, y el rol decide lo que la persona puede hacer.
    Dejar que cada uno se los cambie solo convierte el control de accesos en
    una sugerencia, así que esos pasan por el administrador.
    """

    class Campo(models.TextChoices):
        EMAIL = "email", "Correo electrónico"
        USERNAME = "username", "Nombre de usuario"
        ROL = "rol", "Rol"

    class Estado(models.TextChoices):
        PENDIENTE = "PENDIENTE", "Pendiente"
        APROBADA = "APROBADA", "Aprobada"
        RECHAZADA = "RECHAZADA", "Rechazada"

    usuario = models.ForeignKey(
        Usuario, on_delete=models.CASCADE, related_name="cambios_solicitados",
        verbose_name="Solicitante",
    )
    campo = models.CharField("Dato a cambiar", max_length=20, choices=Campo.choices)
    valor_actual = models.CharField("Valor actual", max_length=150, blank=True)
    valor_solicitado = models.CharField("Valor solicitado", max_length=150)
    motivo = models.TextField("Motivo", blank=True)
    estado = models.CharField(
        "Estado", max_length=10, choices=Estado.choices, default=Estado.PENDIENTE
    )
    creada = models.DateTimeField("Fecha de solicitud", auto_now_add=True)
    resuelta = models.DateTimeField("Fecha de resolución", null=True, blank=True)
    resuelta_por = models.ForeignKey(
        Usuario, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="cambios_resueltos", verbose_name="Resuelta por",
    )
    comentario = models.CharField("Comentario del administrador", max_length=250, blank=True)

    class Meta:
        verbose_name = "Solicitud de cambio de datos"
        verbose_name_plural = "Solicitudes de cambio de datos"
        ordering = ["-creada"]
        constraints = [
            # Una sola solicitud viva por usuario y campo: si pide dos veces el
            # mismo correo, la segunda reemplaza a la primera en vez de dejarle
            # al administrador dos pendientes que dicen lo mismo.
            models.UniqueConstraint(
                fields=["usuario", "campo"],
                condition=models.Q(estado="PENDIENTE"),
                name="una_solicitud_pendiente_por_campo",
            )
        ]

    def __str__(self):
        return f"{self.usuario.username}: {self.get_campo_display()} → {self.valor_solicitado}"

    @property
    def pendiente(self):
        return self.estado == self.Estado.PENDIENTE


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


def usuarios_asignables(rol=None):
    """
    Usuarios a los que se les puede asignar trabajo: activos y ya aprobados.

    Un usuario que se registró solo (CU-52) queda con pendiente_aprobacion=True
    hasta que un administrador lo acepte. Hasta entonces no debe aparecer en
    ningún selector de asignación: asignarle una obra o una herramienta a
    alguien que todavía no existe formalmente en la empresa deja registros
    apuntando a una cuenta que puede terminar rechazada.
    """
    qs = Usuario.objects.filter(estado=True, pendiente_aprobacion=False)
    if rol:
        qs = qs.filter(rol=rol)
    return qs


def con_seleccion_actual(queryset, instancia, campo):
    """
    Agrega al queryset el valor que ya tenía el registro, aunque hoy no
    cumpla el filtro. Evita que al editar un proyecto antiguo desaparezca
    su jefe asignado (y el formulario lo borre sin querer).
    """
    actual_id = getattr(instancia, f"{campo}_id", None) if instancia else None
    if actual_id and not queryset.filter(pk=actual_id).exists():
        return Usuario.objects.filter(
            models.Q(pk__in=queryset.values("pk")) | models.Q(pk=actual_id)
        )
    return queryset


# ==========================================================================
#  CU-60 (RF-57) — Configurando parámetros generales del sistema
# ==========================================================================

class ParametrosSistema(models.Model):
    """
    Los cuatro valores que Administración tiene que poder cambiar sin tocar
    código ni reiniciar el servidor.

    Antes vivían como constantes en settings.py y en el .env: para subir la
    tolerancia de facturación de 5% a 8% había que entrar por SSH a la VM,
    editar un archivo y reiniciar gunicorn. Eso no es configurable, es
    modificable por el que tenga la llave del servidor.

    Es una fila única (singleton): `ParametrosSistema.actuales()` la crea con
    los valores por defecto la primera vez que alguien la pide, así el sistema
    nunca queda sin parámetros aunque la tabla esté vacía.
    """

    tolerancia_factura_pct = models.DecimalField(
        "Tolerancia de facturación (%)", max_digits=5, decimal_places=2, default=5,
        validators=[MinValueValidator(Decimal("0")), MaxValueValidator(Decimal("100"))],
        help_text="Diferencia máxima aceptada entre el monto de la factura y el "
                  "total de la orden de compra antes de bloquearla.",
    )
    stock_minimo_defecto = models.DecimalField(
        "Stock mínimo por defecto", max_digits=12, decimal_places=2, default=0,
        validators=[MinValueValidator(Decimal("0"))],
        help_text="Valor que toma el stock mínimo de un material nuevo cuando no "
                  "se indica otro. Alimenta la alerta de materiales críticos.",
    )
    umbral_archivo_mb = models.PositiveIntegerField(
        "Umbral de tamaño de archivo (MB)", default=10,
        validators=[MinValueValidator(1), MaxValueValidator(500)],
        help_text="Sobre este tamaño el sistema advierte antes de completar la carga.",
    )

    actualizado = models.DateTimeField("Última modificación", auto_now=True)
    actualizado_por = models.ForeignKey(
        "usuarios.Usuario", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="parametros_actualizados", verbose_name="Modificado por",
    )

    class Meta:
        verbose_name = "Parámetros del sistema"
        verbose_name_plural = "Parámetros del sistema"

    def __str__(self):
        return "Parámetros generales del sistema"

    def save(self, *args, **kwargs):
        # Una sola fila, siempre. Si alguien crea otra por el admin o por la
        # shell, se escribe encima de la que ya existe en vez de dejar dos
        # configuraciones compitiendo.
        self.pk = 1
        kwargs.pop("force_insert", None)
        # Con la pk fijada y `adding` en False, Django intenta UPDATE y, si no
        # había fila, cae solo al INSERT. Sin esto un `objects.create()` revienta
        # contra la clave primaria en vez de reemplazar la configuración.
        self._state.adding = False
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """No se borra: el sistema quedaría sin parámetros a mitad de operación."""
        return (0, {})

    @classmethod
    def actuales(cls):
        """La configuración vigente, creándola con los valores por defecto si falta."""
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    @property
    def umbral_archivo_bytes(self):
        return self.umbral_archivo_mb * 1024 * 1024
