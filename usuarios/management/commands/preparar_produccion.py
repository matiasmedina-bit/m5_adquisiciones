"""
Deja el sistema listo para entregar: borra los datos de demostración y crea
el primer administrador real.

Es el paso más delicado de la instalación y el más fácil de hacer a medias.
Por eso va en un comando y no en una lista de instrucciones: borrar la demo a
mano significa acordarse del orden de las tablas —las claves foráneas no
perdonan— y crear el administrador con `createsuperuser` deja la cuenta sin
teléfono y sin nombre completo si nadie se acuerda de completarlos después.

    python manage.py preparar_produccion

Pide confirmación escrita antes de borrar nada. Si algo falla a mitad de camino
no queda medio borrado: todo corre dentro de una transacción.
"""
from django.core.management.base import BaseCommand, CommandError
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from getpass import getpass

from usuarios.models import Usuario, ParametrosSistema

CONFIRMACION = "BORRAR DEMO"


class Command(BaseCommand):
    help = ("Borra los datos de demostración y crea el administrador real. "
            "Se usa una sola vez, antes de entregar el sistema al cliente.")

    def add_arguments(self, parser):
        parser.add_argument(
            "--sin-confirmar", action="store_true",
            help="No pedir la frase de confirmación (para scripts). Úsalo con cuidado.")
        parser.add_argument(
            "--conservar-catalogo", action="store_true",
            help="No borrar materiales, proveedores ni tipos de documento. "
                 "Útil si el catálogo de la demo ya se depuró a mano.")

    # ------------------------------------------------------------------
    def handle(self, *args, **opciones):
        self.stdout.write(self.style.MIGRATE_HEADING(
            "\nPreparar el sistema para producción — Constructora M5 SpA\n"))

        self._mostrar_inventario_actual()

        if not opciones["sin_confirmar"]:
            self.stdout.write(self.style.WARNING(
                f"\nEsto borra TODOS los datos de demostración y no se puede deshacer.\n"
                f"Si no tienes un respaldo de la base, sal ahora y hazlo primero.\n"))
            respuesta = input(f'Escribe "{CONFIRMACION}" para continuar: ').strip()
            if respuesta != CONFIRMACION:
                raise CommandError("Cancelado. No se borró nada.")

        datos_admin = self._pedir_datos_admin()

        with transaction.atomic():
            borrados = self._borrar_demo(opciones["conservar_catalogo"])
            admin = self._crear_admin(**datos_admin)
            ParametrosSistema.actuales()

        self.stdout.write("")
        for etiqueta, cantidad in borrados.items():
            self.stdout.write(f"  Borrados {cantidad:>4} · {etiqueta}")
        self.stdout.write(self.style.SUCCESS(
            f"\n  Administrador creado: {admin.username} ({admin.email})"))

        self._checklist_final()

    # ------------------------------------------------------------------
    def _mostrar_inventario_actual(self):
        from proyectos.models import Proyecto
        from proveedores.models import Proveedor
        from solicitudes.models import SolicitudMaterial
        from inventario.models import Material

        self.stdout.write("Lo que hay hoy en la base:")
        for etiqueta, modelo in [
            ("usuarios", Usuario), ("proyectos", Proyecto),
            ("proveedores", Proveedor), ("solicitudes", SolicitudMaterial),
            ("materiales", Material),
        ]:
            self.stdout.write(f"  {modelo.objects.count():>5} {etiqueta}")

    # ------------------------------------------------------------------
    def _pedir_datos_admin(self):
        """Se piden ANTES de borrar: si el operador se arrepiende, no perdió nada."""
        self.stdout.write(self.style.MIGRATE_HEADING(
            "\nDatos del administrador real de M5\n"))

        username = self._texto("Nombre de usuario", obligatorio=True)
        if Usuario.objects.filter(username__iexact=username).exclude(
                username__in=self._usuarios_demo()).exists():
            raise CommandError(f"Ya existe una cuenta real con el usuario «{username}».")

        nombre = self._texto("Nombre", obligatorio=True)
        apellido = self._texto("Apellido", obligatorio=True)
        email = self._email()
        telefono = self._texto("Teléfono (opcional)", obligatorio=False)
        password = self._password(username, email)

        return {"username": username, "first_name": nombre, "last_name": apellido,
                "email": email, "telefono": telefono, "password": password}

    def _texto(self, etiqueta, obligatorio):
        while True:
            valor = input(f"  {etiqueta}: ").strip()
            if valor or not obligatorio:
                return valor
            self.stderr.write("    Este dato es obligatorio.")

    def _email(self):
        while True:
            valor = input("  Correo institucional: ").strip().lower()
            try:
                validate_email(valor)
            except ValidationError:
                self.stderr.write("    Eso no parece un correo válido.")
                continue
            if Usuario.objects.filter(email__iexact=valor).exclude(
                    username__in=self._usuarios_demo()).exists():
                self.stderr.write("    Ese correo ya está en otra cuenta real.")
                continue
            return valor

    def _password(self, username, email):
        while True:
            clave = getpass("  Contraseña: ")
            if not clave:
                self.stderr.write("    La contraseña no puede quedar vacía.")
                continue
            if clave != getpass("  Repítela: "):
                self.stderr.write("    No coinciden. Intenta de nuevo.")
                continue
            tentativo = Usuario(username=username, email=email)
            try:
                validate_password(clave, tentativo)
            except ValidationError as exc:
                for mensaje in exc.messages:
                    self.stderr.write(f"    {mensaje}")
                continue
            return clave

    @staticmethod
    def _usuarios_demo():
        """Las cuentas que crea seed_demo y que van a desaparecer."""
        return ["admin", "jefe", "encargado", "bodega", "contador"]

    # ------------------------------------------------------------------
    def _borrar_demo(self, conservar_catalogo):
        """
        Borra en orden inverso a las dependencias. Django hace CASCADE en
        muchas relaciones, pero varias son PROTECT a propósito (no se borra un
        material que tiene movimientos), así que el orden importa.
        """
        from adquisiciones.models import (Cotizacion, CotizacionLinea,
                                          OrdenCompra, OrdenCompraLinea)
        from auditoria.models import RegistroAuditoria
        from facturacion.models import Factura
        from inventario.models import (Material, MovimientoInventario,
                                       PrestamoHerramienta)
        from proveedores.models import Proveedor, ProveedorMaterial
        from proyectos.models import ArchivoProyecto, Itemizado, Proyecto, TipoDocumento
        from solicitudes.models import (SolicitudAdjunto, SolicitudDetalle,
                                        SolicitudMaterial)

        borrados = {}

        def borrar(etiqueta, queryset):
            cantidad = queryset.count()
            queryset.delete()
            if cantidad:
                borrados[etiqueta] = cantidad

        # 1. Documentos y movimientos (las hojas del árbol)
        borrar("facturas", Factura.objects.all())
        borrar("movimientos de bodega", MovimientoInventario.objects.all())
        borrar("préstamos de herramienta", PrestamoHerramienta.objects.all())
        borrar("líneas de orden de compra", OrdenCompraLinea.objects.all())
        borrar("órdenes de compra", OrdenCompra.objects.all())
        borrar("líneas de cotización", CotizacionLinea.objects.all())
        borrar("cotizaciones", Cotizacion.objects.all())
        borrar("adjuntos de solicitud", SolicitudAdjunto.objects.all())
        borrar("líneas de solicitud", SolicitudDetalle.objects.all())
        borrar("solicitudes de material", SolicitudMaterial.objects.all())

        # 2. Archivos y estructura de proyecto
        for archivo in ArchivoProyecto.objects.all():
            archivo.archivo.delete(save=False)
        borrar("archivos de proyecto", ArchivoProyecto.objects.all())
        borrar("partidas de itemizado", Itemizado.objects.all())
        borrar("proyectos", Proyecto.objects.all())

        # 3. Catálogos, si se pidió limpiarlos
        if not conservar_catalogo:
            borrar("ítems de catálogo de proveedor", ProveedorMaterial.objects.all())
            borrar("proveedores", Proveedor.objects.all())
            borrar("materiales y herramientas", Material.objects.all())
            borrar("tipos de documento", TipoDocumento.objects.all())

        # 4. La bitácora de la demo: son acciones que nunca ocurrieron en M5
        borrar("registros de auditoría", RegistroAuditoria.objects.all())

        # 5. Las cuentas, al final: todo lo anterior las referenciaba
        borrar("cuentas de usuario", Usuario.objects.all())

        return borrados

    # ------------------------------------------------------------------
    def _crear_admin(self, password, **datos):
        admin = Usuario(rol=Usuario.Rol.ADMIN, estado=True,
                        pendiente_aprobacion=False,
                        is_staff=True, is_superuser=True, **datos)
        admin.set_password(password)
        admin.save()
        return admin

    # ------------------------------------------------------------------
    def _checklist_final(self):
        parametros = ParametrosSistema.actuales()
        self.stdout.write(self.style.MIGRATE_HEADING("\nLo que falta antes de entregar\n"))
        pendientes = [
            "Rotar la contraseña de PostgreSQL y actualizarla en el .env",
            "Poner el RUT, giro y dirección reales de M5 en el .env "
            "(salen impresos en cada orden de compra)",
            "Configurar EMAIL_* en el .env, o los correos de activación no saldrán",
            f"Revisar los parámetros: tolerancia {parametros.tolerancia_factura_pct}%, "
            f"stock mínimo {parametros.stock_minimo_defecto}, "
            f"umbral {parametros.umbral_archivo_mb} MB",
            "Cargar el catálogo de tipos de documento (sin él no se suben archivos)",
            "Crear las cuentas del resto del equipo de M5 desde Usuarios",
        ]
        for i, linea in enumerate(pendientes, 1):
            self.stdout.write(f"  {i}. {linea}")
        self.stdout.write("")
