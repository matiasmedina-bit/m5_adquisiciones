"""
CU-47 — Buscando trazabilidad de material u Orden de Compra.

La pregunta que responde esta pantalla es siempre la misma, venga de quien
venga: «¿qué pasó con esto?». Se entra por cualquiera de las tres puertas que
la gente tiene a mano —el correlativo de una solicitud, el de una orden de
compra, o el nombre del material— y se sale con la cadena completa:

    Solicitud de material
        └─ cotizaciones recibidas
             └─ órdenes de compra emitidas
                  ├─ movimientos de bodega (recepciones)
                  └─ facturas asociadas

La búsqueda se resuelve acá, aparte de las vistas, porque arma datos y no
pantallas: la vista sólo elige la plantilla.
"""
from django.db.models import Q

from facturacion.models import Factura
from proveedores.models import ProveedorMaterial
from inventario.models import Material, MovimientoInventario
from solicitudes.models import SolicitudMaterial, SolicitudDetalle
from .models import Cotizacion, OrdenCompra


def _correlativo(texto):
    """Normaliza 'sm 12', 'SM-12', 'sm-000012' a un patrón buscable."""
    return texto.replace(" ", "").replace("_", "-").upper()


def cadena_de_solicitud(solicitud):
    """
    Toda la vida de una solicitud, en el orden en que ocurrió. Devuelve el
    diccionario que la plantilla dibuja como línea de tiempo.
    """
    ordenes = list(
        OrdenCompra.objects
        .filter(solicitud=solicitud)
        .select_related("proveedor", "cotizacion")
        .prefetch_related("lineas__material")
    )
    ids_ordenes = [oc.pk for oc in ordenes]

    movimientos = list(
        MovimientoInventario.objects
        .filter(orden_compra_id__in=ids_ordenes)
        .select_related("material", "orden_compra", "registrado_por")
        .order_by("fecha")
    )
    facturas = list(
        Factura.objects
        .filter(ordenes__in=ids_ordenes)
        .select_related("proveedor")
        .distinct()
    )
    cotizaciones = list(
        Cotizacion.objects
        .filter(solicitud=solicitud)
        .select_related("proveedor")
        .prefetch_related("lineas")
    )

    # Movimientos del material pedido que no vinieron por una OC de esta SM
    # (salidas a obra, mermas): también son parte de lo que pasó con el material.
    materiales = [d.material_id for d in solicitud.detalles.all()]
    otros_movimientos = list(
        MovimientoInventario.objects
        .filter(material_id__in=materiales)
        .exclude(orden_compra_id__in=ids_ordenes)
        .select_related("material", "registrado_por", "proyecto")
        .order_by("fecha")[:20]
    )

    return {
        "solicitud": solicitud,
        "detalles": list(solicitud.detalles.select_related("material", "proveedor")),
        "cotizaciones": cotizaciones,
        "ordenes": ordenes,
        "movimientos": movimientos,
        "otros_movimientos": otros_movimientos,
        "facturas": facturas,
        # Para que la pantalla pueda decir dónde se cortó la cadena
        "sin_cotizaciones": not cotizaciones,
        "sin_ordenes": not ordenes,
        "sin_recepcion": not movimientos,
        "sin_factura": not facturas,
    }


def _visible(cadena, usuario):
    """El Jefe de Proyecto sólo reconstruye la cadena de sus obras."""
    if usuario is None or usuario.rol != "JEFE_PROYECTO":
        return True
    solicitud = cadena.get("solicitud")
    obra = solicitud.proyecto if solicitud else cadena["ordenes"][0].obra
    return obra is not None and obra.dirigida_por(usuario)


def buscar(texto, usuario=None):
    """Igual que _buscar, pero filtrando lo que el usuario puede ver."""
    resultado = _buscar(texto)
    if usuario is not None and usuario.rol == "JEFE_PROYECTO" and resultado["cadenas"]:
        resultado["cadenas"] = [c for c in resultado["cadenas"] if _visible(c, usuario)]
        if not resultado["cadenas"] and resultado["tipo"] in ("sm", "oc"):
            resultado["tipo"] = "sin_resultados"
    return resultado


def _buscar(texto):
    """
    Resuelve la búsqueda del CU-47 y devuelve:

        {"tipo": "sm" | "oc" | "material" | "vacio" | "sin_resultados",
         "cadenas": [...],      # una por solicitud encontrada
         "materiales": [...],   # sólo en la búsqueda por material
         "termino": texto}

    Una búsqueda que no encuentra nada NO es un error: devuelve
    'sin_resultados' y la pantalla lo dice con todas sus letras, en vez de
    mostrar una tabla vacía que parece un sistema roto.
    """
    texto = (texto or "").strip()
    if not texto:
        return {"tipo": "vacio", "cadenas": [], "materiales": [], "termino": ""}

    clave = _correlativo(texto)

    # El folio se puede escribir «13285», «13.285» u «OC 13285»: todos llevan
    # a la misma orden, se haya impreso con punto o sin él.
    solo_digitos = clave.removeprefix("OC").lstrip("-").replace(".", "")
    por_folio = (OrdenCompra.objects.filter(folio=int(solo_digitos)).select_related("solicitud")
                 if solo_digitos.isdigit() and len(solo_digitos) <= 9
                 else OrdenCompra.objects.none())

    # --- Puerta 1: folio / correlativo de orden de compra ---
    if clave.startswith("OC") or por_folio.exists():
        ordenes = por_folio
        if not ordenes:
            ordenes = (OrdenCompra.objects
                       .filter(correlativo__icontains=clave.replace("OC-", "OC"))
                       .select_related("solicitud"))
        if not ordenes:
            ordenes = OrdenCompra.objects.filter(correlativo__icontains=clave)
        cadenas = []
        vistas = set()
        for oc in ordenes:
            # Una compra anticipada no cuelga de ninguna solicitud: su cadena
            # empieza en la propia orden.
            if oc.solicitud_id is None:
                cadenas.append({"solicitud": None, "cotizaciones": [],
                                "ordenes": [oc], "orden_buscada": oc,
                                "anticipada": True})
                continue
            if oc.solicitud_id in vistas:
                continue
            vistas.add(oc.solicitud_id)
            cadena = cadena_de_solicitud(oc.solicitud)
            cadena["orden_buscada"] = oc
            cadenas.append(cadena)
        return {"tipo": "oc" if cadenas else "sin_resultados",
                "cadenas": cadenas, "materiales": [], "termino": texto}

    # --- Puerta 2: correlativo de solicitud ---
    if clave.startswith("SM"):
        solicitudes = (SolicitudMaterial.objects
                       .filter(correlativo__icontains=clave)
                       .select_related("proyecto", "emisor"))
        cadenas = [cadena_de_solicitud(s) for s in solicitudes]
        return {"tipo": "sm" if cadenas else "sin_resultados",
                "cadenas": cadenas, "materiales": [], "termino": texto}

    # --- Puerta 3: código o nombre del material ---
    # El código puede ser el interno del catálogo maestro (MAT-00012) o el
    # que usa el proveedor en su catálogo (CEM-001).
    por_codigo_proveedor = (ProveedorMaterial.objects
                            .filter(codigo__iexact=texto, material__isnull=False)
                            .values_list("material_id", flat=True))
    materiales = list(Material.objects.filter(
        Q(codigo_interno__iexact=texto) | Q(pk__in=list(por_codigo_proveedor))
    )[:10]) or list(Material.objects.filter(
        Q(nombre__icontains=texto) | Q(codigo_interno__icontains=texto))[:10])
    if not materiales:
        return {"tipo": "sin_resultados", "cadenas": [], "materiales": [],
                "termino": texto}

    ids = [m.pk for m in materiales]
    solicitudes = (SolicitudMaterial.objects
                   .filter(detalles__material_id__in=ids)
                   .select_related("proyecto", "emisor")
                   .distinct()
                   .order_by("-fecha")[:10])
    cadenas = [cadena_de_solicitud(s) for s in solicitudes]

    # Resumen por material: cuánto se pidió, cuánto se movió, stock de hoy
    resumen = []
    for material in materiales:
        pedido = sum(
            (d.cantidad_solicitada for d in
             SolicitudDetalle.objects.filter(material=material)), 0)
        resumen.append({
            "material": material,
            "pedido": pedido,
            "movimientos": MovimientoInventario.objects.filter(material=material).count(),
            "stock": material.stock_actual,
        })

    return {"tipo": "material", "cadenas": cadenas, "materiales": resumen,
            "termino": texto}
