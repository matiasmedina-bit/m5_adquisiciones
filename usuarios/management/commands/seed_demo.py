"""
Comando para poblar la base de datos con datos de demostración.
Uso:  python manage.py seed_demo
Crea un usuario por cada rol (clave: demo12345), proveedores con su catálogo,
un proyecto con itemizado, materiales, solicitudes, cotizaciones, órdenes de
compra, movimientos de bodega y una factura. Ideal para el video y la demo.
"""
from datetime import date, timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from usuarios.models import Usuario
from proveedores.models import Proveedor, ProveedorMaterial
from proyectos.models import Proyecto, Itemizado, TipoDocumento
from inventario.models import Material, MovimientoInventario, PrestamoHerramienta
from solicitudes.models import SolicitudMaterial, SolicitudDetalle
from adquisiciones.models import Cotizacion, CotizacionLinea, OrdenCompra, OrdenCompraLinea
from facturacion.models import Factura
from auditoria.models import RegistroAuditoria, registrar


class Command(BaseCommand):
    help = "Carga datos de demostración para los Incrementos 1 y 2."

    def handle(self, *args, **options):
        # --- Usuarios (uno por rol) ---
        usuarios = {
            "admin":    ("ADMIN", "Administrador General"),
            "jefe":     ("JEFE_PROYECTO", "Jefa de Proyecto"),
            "encargado":("ENCARGADO_ADQUISICIONES", "Encargado de Adquisiciones"),
            "bodega":   ("BODEGUERO", "Bodeguero Turno Mañana"),
            "contador": ("CONTABILIDAD", "Analista de Contabilidad"),
        }
        for username, (rol, nombre) in usuarios.items():
            if not Usuario.objects.filter(username=username).exists():
                u = Usuario.objects.create_user(
                    username=username, password="demo12345",
                    email=f"{username}@m5.cl", rol=rol, first_name=nombre)
                if rol == "ADMIN":
                    u.is_staff = True
                    u.is_superuser = True
                    u.save()
                self.stdout.write(f"  Usuario creado: {username} / demo12345 ({rol})")

        # --- Nómina ampliada: varios usuarios por rol ---
        # Refleja la realidad de la sede/obras (varios encargados y bodegueros)
        # y permite probar el seccionado, la búsqueda y los filtros del listado.
        # (nombre, apellido, rol, activo)
        nomina = [
            ("Camila",   "Rojas",     "JEFE_PROYECTO", True),
            ("Diego",    "Fuentes",   "JEFE_PROYECTO", True),
            ("Valentina","Soto",      "JEFE_PROYECTO", True),
            ("Ignacio",  "Vega",      "ENCARGADO_ADQUISICIONES", True),
            ("Paula",    "Herrera",   "ENCARGADO_ADQUISICIONES", True),
            ("Rodrigo",  "Cáceres",   "ENCARGADO_ADQUISICIONES", True),
            ("Fernanda", "Muñoz",     "ENCARGADO_ADQUISICIONES", False),
            ("Sebastián","Araya",     "BODEGUERO", True),
            ("María",    "Contreras", "BODEGUERO", True),
            ("Jorge",    "Pizarro",   "BODEGUERO", True),
            ("Antonia",  "Reyes",     "BODEGUERO", True),
            ("Cristóbal","Núñez",     "BODEGUERO", True),
            ("Daniela",  "Espinoza",  "BODEGUERO", True),
            ("Matías",   "Torres",    "BODEGUERO", True),
            ("Josefa",   "Salinas",   "BODEGUERO", False),
        ]
        creados = 0
        for nombre, apellido, rol, activo in nomina:
            username = f"{nombre}.{apellido}".lower().replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u")
            if not Usuario.objects.filter(username=username).exists():
                Usuario.objects.create_user(
                    username=username, password="demo12345",
                    email=f"{username}@m5.cl", rol=rol,
                    first_name=nombre, last_name=apellido,
                    telefono="+56 9 8000 0000", estado=activo)
                creados += 1
        if creados:
            self.stdout.write(f"  Nómina ampliada: {creados} usuarios adicionales creados (clave: demo12345)")

        # --- Proveedores ---
        proveedores = [
            ("Ferretería El Constructor SpA",   "11111111-1", "30_DIAS",  True),
            ("Aceros y Fierros del Sur Ltda",   "12345678-5", "60_DIAS",  True),
            ("Hormigones Bío-Bío S.A.",         "76543210-9", "30_DIAS",  True),
            ("Maderas y Terciados Pucón Ltda",  "77888999-8", "CONTADO",  True),
            ("Áridos y Transportes Maipo SpA",  "78123456-7", "90_DIAS",  True),
            ("Eléctricos Industriales Andes",   "79234567-4", "60_DIAS",  True),
            ("Pinturas y Revestimientos ProSur","76345678-3", "30_DIAS",  False),
            ("Arriendo de Maquinaria Costa",    "77456789-K", "CONTADO",  True),
            ("Gasfitería y Riego Aconcagua",    "78567890-6", "30_DIAS",  True),
            ("Seguridad y EPP Trabajo Seguro",  "79678901-2", "60_DIAS",  False),
        ]
        prov_objs = {}
        for nombre, rut, cond, estado in proveedores:
            p, _ = Proveedor.objects.get_or_create(
                rut=rut.replace(".", "").replace("-", ""),
                defaults={"nombre": nombre, "condicion_pago": cond, "estado": estado,
                          "correo": f"contacto@{nombre.split()[0].lower()}.cl",
                          "telefono": "+56 2 2345 6789"})
            prov_objs[nombre] = p

        # --- RF-05: catálogo de materiales de algunos proveedores ---
        catalogos = {
            "Ferretería El Constructor SpA": [
                ("FC-CEM25", "Cemento Portland 25 kg", "saco", True),
                ("FC-TORN1", "Tornillo autoperforante 1\"", "caja", True),
                ("FC-DISCO7", "Disco de corte metal 7\"", "unidad", False),
            ],
            "Aceros y Fierros del Sur Ltda": [
                ("AF-F12", "Fierro estriado 12 mm", "barra", True),
                ("AF-F8", "Fierro estriado 8 mm", "barra", True),
            ],
        }
        for nombre_prov, items in catalogos.items():
            prov = prov_objs.get(nombre_prov)
            if not prov:
                continue
            for codigo, desc, um, disp in items:
                ProveedorMaterial.objects.get_or_create(
                    proveedor=prov, codigo=codigo,
                    defaults={"descripcion": desc, "unidad_medida": um, "disponible": disp})

        # --- Proyecto + itemizado (RF-14: centro de costo) ---
        jefe_user = Usuario.objects.get(username="jefe")
        proyecto, _ = Proyecto.objects.get_or_create(
            nombre="Edificio Residencial Las Condes",
            defaults={"mandante": "Inmobiliaria Aurora", "centro_costo": "CC-2026-014",
                      "fecha_inicio": date(2026, 6, 1),
                      "fecha_termino": date(2026, 12, 1), "estado": "EJECUCION",
                      "jefe_proyecto": jefe_user,
                      "presupuesto_total": 850000000})
        if not proyecto.centro_costo:
            proyecto.centro_costo = "CC-2026-014"
            proyecto.save(update_fields=["centro_costo"])
        it1, _ = Itemizado.objects.get_or_create(proyecto=proyecto, codigo_partida="OG-01",
            defaults={"descripcion": "Hormigón armado", "unidad_medida": "m3",
                      "cant_presupuestada": 1200, "cant_ejecutada": 300})
        it2, _ = Itemizado.objects.get_or_create(proyecto=proyecto, codigo_partida="OG-02",
            defaults={"descripcion": "Albañilería", "unidad_medida": "m2",
                      "cant_presupuestada": 800, "cant_ejecutada": 780})  # saldo 20 -> dispara RF-16

        # --- CU-54: catálogo de tipos de documento ---
        # Sin catálogo la ficha del proyecto bloquea la carga de archivos
        # (Excepción 1 del CU-54); la demo parte con los tipos de una obra real.
        for nombre_tipo, desc_tipo in [
            ("Plano", "Planimetría de arquitectura, estructura o especialidades"),
            ("Contrato", "Contrato de obra, subcontratos y anexos"),
            ("Permiso municipal", "Permisos de edificación y recepción municipal"),
            ("Cotización", "Cotizaciones recibidas de proveedores"),
            ("Factura", "Facturas y documentos tributarios del proyecto"),
            ("Acta de recepción", "Actas de recepción de obra y de materiales"),
            ("Informe técnico", "Informes de ensayo, topografía y mecánica de suelos"),
        ]:
            TipoDocumento.objects.get_or_create(
                nombre=nombre_tipo, defaults={"descripcion": desc_tipo})

        # --- Materiales y herramientas ---
        # (nombre, unidad, precio_ref, tipo, stock, activo, codigo_activo)
        materiales = [
            ("Cemento Portland 25kg",      "saco",   4500,  "CONSUMIBLE",  320, True,  ""),
            ("Fierro estriado 12mm",       "barra",  8900,  "CONSUMIBLE",  150, True,  ""),
            ("Fierro estriado 8mm",        "barra",  5200,  "CONSUMIBLE",  210, True,  ""),
            ("Arena gruesa",               "m3",     18000, "CONSUMIBLE",  45,  True,  ""),
            ("Gravilla 20mm",              "m3",     21000, "CONSUMIBLE",  38,  True,  ""),
            ("Ladrillo fiscal",            "unidad", 380,   "CONSUMIBLE",  9800,True,  ""),
            ("Placa de yeso-cartón 15mm",  "plancha",7900,  "CONSUMIBLE",  260, True,  ""),
            ("Pintura látex blanco 1 gal", "galón",  15990, "CONSUMIBLE",  70,  True,  ""),
            ("Tornillo autoperforante 1\"","caja",   3990,  "CONSUMIBLE",  120, True,  ""),
            ("Disco de corte metal 7\"",   "unidad", 1990,  "CONSUMIBLE",  400, True,  ""),
            ("Guantes de seguridad",       "par",    2500,  "CONSUMIBLE",  180, True,  ""),
            ("Cal hidratada 25kg",         "saco",   3200,  "CONSUMIBLE",  0,   False, ""),
            ("Taladro percutor",           "unidad", 89990, "HERRAMIENTA", 12,  True,  "HER-0001"),
            ("Esmeril angular 4.5\"",      "unidad", 45990, "HERRAMIENTA", 8,   True,  "HER-0002"),
            ("Sierra circular 7.1/4\"",    "unidad", 79990, "HERRAMIENTA", 5,   True,  "HER-0003"),
            ("Martillo demoledor",         "unidad", 189990,"HERRAMIENTA", 3,   True,  "HER-0004"),
            ("Nivel láser autonivelante",  "unidad", 129990,"HERRAMIENTA", 4,   True,  "HER-0005"),
            ("Generador eléctrico 3 kVA",  "unidad", 349990,"HERRAMIENTA", 2,   True,  "HER-0006"),
            ("Andamio modular (cuerpo)",   "unidad", 59990, "HERRAMIENTA", 40,  True,  "HER-0007"),
            ("Betonera 130 lt",            "unidad", 259990,"HERRAMIENTA", 1,   False, "HER-0008"),
        ]
        objs = {}
        for nombre, um, precio, tipo, stock, activo, cod in materiales:
            m, _ = Material.objects.get_or_create(nombre=nombre, defaults={
                "unidad_medida": um, "precio_referencia": precio, "tipo": tipo,
                "stock_actual": stock, "activo": activo, "codigo_activo": cod})
            objs[nombre] = m

        # RF-37: stock mínimo y ubicación en algunos materiales
        minimos = {
            "Cemento Portland 25kg": (100, "Bodega central · Estante A1"),
            "Fierro estriado 12mm": (200, "Bodega central · Rack fierros"),  # 150 <= 200 -> crítico
            "Pintura látex blanco 1 gal": (80, "Bodega central · Estante C4"),  # 70 <= 80 -> crítico
            "Arena gruesa": (40, "Patio exterior"),
        }
        for nombre, (minimo, ubic) in minimos.items():
            if nombre in objs:
                Material.objects.filter(pk=objs[nombre].pk).update(
                    stock_minimo=minimo, ubicacion=ubic)

        # --- Solicitud de ejemplo ---
        ea = Usuario.objects.get(username="encargado")
        if not SolicitudMaterial.objects.exists():
            sol = SolicitudMaterial.objects.create(
                proyecto=proyecto, emisor=ea,
                observaciones="Materiales para fundaciones del primer nivel.")
            SolicitudDetalle.objects.create(solicitud=sol, material=objs["Cemento Portland 25kg"],
                cantidad_solicitada=200, unidad_medida="saco", partida=it1)
            SolicitudDetalle.objects.create(solicitud=sol, material=objs["Fierro estriado 12mm"],
                cantidad_solicitada=150, unidad_medida="barra", partida=it1)
            self.stdout.write(f"  Solicitud creada: {sol.correlativo}")

        # ------------------------------------------------------------------
        # Incremento 2: cadena aprobada -> cotización -> OC -> recepción -> factura
        # ------------------------------------------------------------------
        if not Cotizacion.objects.exists():
            sol2 = SolicitudMaterial.objects.create(
                proyecto=proyecto, emisor=ea, estado=SolicitudMaterial.Estado.APROBADA,
                observaciones="Compra de cemento y fierro para losa nivel 2.")
            d_cem = SolicitudDetalle.objects.create(
                solicitud=sol2, material=objs["Cemento Portland 25kg"],
                cantidad_solicitada=120, unidad_medida="saco", partida=it1)
            d_fie = SolicitudDetalle.objects.create(
                solicitud=sol2, material=objs["Fierro estriado 12mm"],
                cantidad_solicitada=80, unidad_medida="barra", partida=it1)

            prov_a = prov_objs["Ferretería El Constructor SpA"]
            prov_b = prov_objs["Aceros y Fierros del Sur Ltda"]

            cot_a = Cotizacion.objects.create(
                solicitud=sol2, proveedor=prov_a, creada_por=ea,
                costo_despacho=25000, tiempo_entrega_dias=3)
            CotizacionLinea.objects.create(cotizacion=cot_a, solicitud_detalle=d_cem, valor_unitario=4600)
            CotizacionLinea.objects.create(cotizacion=cot_a, solicitud_detalle=d_fie, valor_unitario=9200)

            cot_b = Cotizacion.objects.create(
                solicitud=sol2, proveedor=prov_b, creada_por=ea,
                costo_despacho=18000, tiempo_entrega_dias=5)
            CotizacionLinea.objects.create(cotizacion=cot_b, solicitud_detalle=d_cem, valor_unitario=4750)
            CotizacionLinea.objects.create(cotizacion=cot_b, solicitud_detalle=d_fie, valor_unitario=8900)

            # Aprobar la mejor línea de cada material (RF-22)
            cot_a.lineas.get(solicitud_detalle=d_cem).aprobar()   # cemento: Ferretería
            cot_b.lineas.get(solicitud_detalle=d_fie).aprobar()   # fierro: Aceros del Sur
            sol2.estado = SolicitudMaterial.Estado.EN_COTIZACION
            sol2.save(update_fields=["estado"])

            # Generar OC por proveedor (RF-23)
            oc_a = OrdenCompra.objects.create(
                solicitud=sol2, proveedor=prov_a, cotizacion=cot_a,
                costo_despacho=cot_a.costo_despacho, creada_por=ea)
            OrdenCompraLinea.objects.create(
                orden=oc_a, material=objs["Cemento Portland 25kg"], descripcion="Cemento Portland 25 kg",
                cantidad=120, unidad_medida="saco", valor_unitario=4600)
            oc_b = OrdenCompra.objects.create(
                solicitud=sol2, proveedor=prov_b, cotizacion=cot_b,
                costo_despacho=cot_b.costo_despacho, creada_por=ea)
            OrdenCompraLinea.objects.create(
                orden=oc_b, material=objs["Fierro estriado 12mm"], descripcion="Fierro estriado 12 mm",
                cantidad=80, unidad_medida="barra", valor_unitario=8900)
            sol2.estado = SolicitudMaterial.Estado.OC_GENERADA
            sol2.save(update_fields=["estado"])

            # OC-A aprobada y enviada (RF-24/27); OC-B queda como borrador para demo
            jefe_user_local = Usuario.objects.get(username="jefe")
            oc_a.estado = OrdenCompra.Estado.ENVIADA
            oc_a.aprobada_por = jefe_user_local
            oc_a.fecha_aprobacion = timezone.now()
            oc_a.fecha_envio = timezone.now()
            oc_a.save(update_fields=["estado", "aprobada_por", "fecha_aprobacion", "fecha_envio"])

            # Recepción parcial en bodega (RF-28/29/32)
            bod = Usuario.objects.get(username="bodega")
            MovimientoInventario.objects.create(
                tipo=MovimientoInventario.Tipo.ENTRADA, material=objs["Cemento Portland 25kg"],
                cantidad=80, orden_compra=oc_a, ubicacion="Bodega central · Estante A1",
                registrado_por=bod)
            linea_cem = oc_a.lineas.first()
            linea_cem.cantidad_recibida = 80
            linea_cem.save(update_fields=["cantidad_recibida"])
            oc_a.estado = OrdenCompra.Estado.RECEPCION_PARCIAL
            oc_a.save(update_fields=["estado"])

            # Salida a obra y merma de ejemplo (RF-31 / RF-35)
            MovimientoInventario.objects.create(
                tipo=MovimientoInventario.Tipo.SALIDA, material=objs["Cemento Portland 25kg"],
                cantidad=30, proyecto=proyecto, jefe_proyecto=jefe_user_local,
                guia_despacho="GD-1001", registrado_por=bod)
            MovimientoInventario.objects.create(
                tipo=MovimientoInventario.Tipo.MERMA, material=objs["Ladrillo fiscal"],
                cantidad=120, motivo=MovimientoInventario.MotivoMerma.DANO,
                observacion="Pallet caído en descarga.", registrado_por=bod)

            # Préstamo de herramienta (RF-33)
            PrestamoHerramienta.objects.create(
                herramienta=objs["Taladro percutor"], jefe_proyecto=jefe_user_local,
                proyecto=proyecto, fecha_salida=date.today(),
                fecha_devolucion_esperada=date.today() + timedelta(days=15),
                registrado_por=bod)

            # Factura del proveedor A vinculada a la OC-A (RF-40/41)
            cont = Usuario.objects.get(username="contador")
            f = Factura.objects.create(
                numero="F-9001", proveedor=prov_a,
                fecha_emision=date.today(), fecha_vencimiento=date.today() + timedelta(days=30),
                monto_total=oc_a.total, registrado_por=cont)
            f.ordenes.add(oc_a)
            oc_a.facturada = True
            oc_a.save(update_fields=["facturada"])

            # CU-53: la bitácora se escribe desde las vistas, así que los datos
            # sembrados a mano no pasan por ahí. Se registran acá para que la
            # pantalla de auditoría arranque con la cadena completa a la vista
            # (los movimientos de bodega ya entraron solos por señal).
            A = RegistroAuditoria.Accion
            registrar(ea, A.SM_EMITIDA,
                      f"Emitió la solicitud de material para {proyecto.nombre} "
                      f"(2 ítems).", sol2.correlativo)
            registrar(jefe_user_local, A.SM_APROBADA,
                      f"Aprobó la solicitud de {proyecto.nombre}.", sol2.correlativo)
            registrar(ea, A.OC_EMITIDA,
                      f"Emitió la orden de compra a {prov_a.nombre} por la "
                      f"solicitud {sol2.correlativo}.", oc_a.correlativo)
            registrar(ea, A.OC_EMITIDA,
                      f"Emitió la orden de compra a {prov_b.nombre} por la "
                      f"solicitud {sol2.correlativo}.", oc_b.correlativo)
            registrar(jefe_user_local, A.OC_APROBADA,
                      f"Aprobó la orden de compra a {prov_a.nombre}.", oc_a.correlativo)
            registrar(jefe_user_local, A.OC_ENVIADA,
                      f"Envió la orden de compra a {prov_a.nombre} "
                      f"({prov_a.correo}).", oc_a.correlativo)
            registrar(cont, A.FACTURA_RECIBIDA,
                      f"Recibió la factura de {prov_a.nombre} por "
                      f"${f.monto_total:,.0f}.".replace(",", "."), f.numero)
            registrar(Usuario.objects.get(username="admin"), A.USUARIO_APROBADO,
                      "Aprobó la cuenta de bodega como Bodeguero.", "bodega")

            self.stdout.write("  Cadena Inc.2 creada: cotizaciones, OC, recepción y factura demo.")
            self.stdout.write("  Bitácora de auditoría poblada (CU-53).")

        self.stdout.write(self.style.SUCCESS("Datos de demostración cargados correctamente."))
        self.stdout.write("Usuarios: admin / jefe / encargado / bodega / contador  (clave: demo12345)")
