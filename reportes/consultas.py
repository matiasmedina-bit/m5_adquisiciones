"""
Los cuatro reportes del Incremento 3 (CU-42 a CU-45, RF-41 a RF-44).

Cada función devuelve el reporte ya armado en una estructura común:

    {
      "titulo":    str,
      "subtitulo": str,
      "filtros":   [(etiqueta, valor), …]   lo que el usuario eligió, para el PDF
      "columnas":  [{"clave", "titulo", "tipo"}]   tipo: texto | numero | moneda
      "filas":     [dict]
      "totales":   {clave: valor}   pie de tabla, opcional
      "vacio":     bool             para poder decirlo con palabras, no con una tabla en blanco
      "grafico":   {…}              sólo donde el requisito pide gráfico
    }

Esa forma común es lo que permite que la exportación a XLSX y PDF (CU-46) sea
una sola implementación en vez de cuatro: el exportador no sabe qué reporte
está imprimiendo, sólo lee columnas y filas.

Las consultas viven acá, separadas de las vistas, porque son la parte que hay
que poder leer y discutir con el cliente: qué se está contando exactamente como
"despachado", qué precio se usa para valorizar una merma.
"""
from decimal import Decimal

from django.db.models import Count, DecimalField, F, Q, Sum, ExpressionWrapper
from django.db.models.functions import Coalesce

from adquisiciones.models import OrdenCompra, OrdenCompraLinea
from inventario.models import MovimientoInventario
from proyectos.models import Itemizado, Proyecto
from solicitudes.models import SolicitudDetalle

CERO = Decimal("0")


def _decimal(valor):
    return valor if valor is not None else CERO


def proyectos_visibles(usuario):
    """
    Excepción 1 del CU-42: el Jefe de Proyecto sólo ve los proyectos que tiene
    asignados. No es un filtro de pantalla —es el queryset— así que tampoco
    puede llegar a otro escribiendo el id en la URL.
    """
    qs = Proyecto.objects.all().order_by("nombre")
    if usuario.rol == "JEFE_PROYECTO":
        return qs.filter(jefe_proyecto=usuario)
    return qs


# ==========================================================================
#  CU-42 (RF-41) — Consumo consolidado por proyecto
# ==========================================================================

def consumo_por_proyecto(proyecto):
    """
    Qué se pidió, qué se despachó y cuánto costó, material por material.

    «Solicitado» sale de las líneas de solicitud del proyecto; «despachado» de
    los movimientos de salida a esa obra. Son dos cosas distintas a propósito:
    la diferencia entre ambas es material aprobado que todavía no sale de
    bodega, y es justo lo que el Jefe de Proyecto quiere ver.
    """
    solicitado = (SolicitudDetalle.objects
                  .filter(solicitud__proyecto=proyecto)
                  .values("material_id", "material__codigo_interno",
                          "material__nombre", "material__unidad_medida",
                          "material__precio_referencia")
                  .annotate(
                      cantidad=Coalesce(Sum("cantidad_solicitada"), CERO,
                                        output_field=DecimalField()),
                      valor=Coalesce(Sum(ExpressionWrapper(
                          F("cantidad_solicitada") * F("valor_unitario"),
                          output_field=DecimalField())), CERO,
                          output_field=DecimalField()),
                  ))

    despachado = dict(
        MovimientoInventario.objects
        .filter(proyecto=proyecto, tipo=MovimientoInventario.Tipo.SALIDA)
        .values_list("material_id")
        .annotate(total=Coalesce(Sum("cantidad"), CERO, output_field=DecimalField()))
    )

    filas = []
    for item in solicitado:
        cantidad = _decimal(item["cantidad"])
        valor = _decimal(item["valor"])
        entregado = _decimal(despachado.get(item["material_id"]))
        # El unitario se reconstruye desde el total: es el precio que de verdad
        # se pagó (o se estimó), no el de referencia del catálogo.
        unitario = (valor / cantidad) if cantidad else CERO
        # Una línea cargada sin precio negociado no vale cero: se valoriza al
        # precio de referencia del catálogo, que es la mejor cifra disponible.
        # Si no, el reporte de consumo daría $0 y sería inútil para el Jefe.
        if not unitario:
            unitario = _decimal(item["material__precio_referencia"])
            valor = unitario * cantidad
        filas.append({
            "codigo": item["material__codigo_interno"] or "—",
            "material": item["material__nombre"],
            "unidad": item["material__unidad_medida"],
            "solicitado": cantidad,
            "despachado": entregado,
            "pendiente": cantidad - entregado,
            "costo_unitario": unitario,
            "costo_total": valor,
        })
    filas.sort(key=lambda f: f["costo_total"], reverse=True)

    return {
        "titulo": "Consumo consolidado por proyecto",
        "subtitulo": proyecto.nombre,
        "filtros": [("Proyecto", proyecto.nombre),
                    ("Mandante", proyecto.mandante),
                    ("Estado", proyecto.get_estado_display())],
        "columnas": [
            {"clave": "codigo", "titulo": "Código", "tipo": "texto"},
            {"clave": "material", "titulo": "Material", "tipo": "texto"},
            {"clave": "unidad", "titulo": "Unidad", "tipo": "texto"},
            {"clave": "solicitado", "titulo": "Solicitado", "tipo": "numero"},
            {"clave": "despachado", "titulo": "Despachado", "tipo": "numero"},
            {"clave": "pendiente", "titulo": "Pendiente", "tipo": "numero"},
            {"clave": "costo_unitario", "titulo": "Costo unitario", "tipo": "moneda"},
            {"clave": "costo_total", "titulo": "Costo total", "tipo": "moneda"},
        ],
        "filas": filas,
        "totales": {"material": "Total a la fecha",
                    "costo_total": sum((f["costo_total"] for f in filas), CERO)},
        "vacio": not filas,
        "mensaje_vacio": "Este proyecto todavía no tiene materiales solicitados.",
    }


# ==========================================================================
#  CU-43 (RF-42) — Desviación presupuestaria
# ==========================================================================

def desviacion_presupuestaria(proyecto):
    """
    El itemizado original contra lo que de verdad se compró y se consumió.

    Se compara contra `cant_ejecutada` del itemizado, que es la cifra que la
    obra mantiene al día, y contra lo comprado en órdenes aprobadas. Un proyecto
    sin itemizado cargado no da un reporte vacío: da el aviso de que faltan los
    datos de entrada (Excepción 1 del caso de uso).
    """
    partidas = Itemizado.objects.filter(proyecto=proyecto).order_by("codigo_partida")
    if not partidas.exists():
        return {
            "titulo": "Desviación presupuestaria",
            "subtitulo": proyecto.nombre,
            "filtros": [("Proyecto", proyecto.nombre)],
            "columnas": [], "filas": [], "totales": {},
            "vacio": True,
            "sin_datos_de_entrada": True,
            "mensaje_vacio": (
                f"El proyecto «{proyecto.nombre}» no tiene itemizado cargado. "
                f"Sin las partidas presupuestarias no hay contra qué comparar: "
                f"carga el itemizado y vuelve a generar el reporte."),
        }

    # Comprado: líneas de OC aprobadas o posteriores, por partida de la solicitud
    comprado = dict(
        OrdenCompraLinea.objects
        .filter(orden__solicitud__proyecto=proyecto)
        .exclude(orden__estado__in=[OrdenCompra.Estado.BORRADOR,
                                    OrdenCompra.Estado.RECHAZADA])
        .values_list("material_id")
        .annotate(total=Coalesce(Sum("cantidad"), CERO, output_field=DecimalField()))
    )
    # Qué partida pidió cada material en este proyecto
    partida_de_material = {}
    for detalle in (SolicitudDetalle.objects
                    .filter(solicitud__proyecto=proyecto, partida__isnull=False)
                    .values("material_id", "partida_id")):
        partida_de_material.setdefault(detalle["material_id"], detalle["partida_id"])

    comprado_por_partida = {}
    for material_id, cantidad in comprado.items():
        partida_id = partida_de_material.get(material_id)
        if partida_id:
            comprado_por_partida[partida_id] = comprado_por_partida.get(partida_id, CERO) + cantidad

    filas = []
    for partida in partidas:
        presupuestado = _decimal(partida.cant_presupuestada)
        ejecutado = _decimal(partida.cant_ejecutada)
        adquirido = comprado_por_partida.get(partida.pk, CERO)
        desviacion = ejecutado - presupuestado
        pct = (desviacion / presupuestado * 100) if presupuestado else CERO
        filas.append({
            "codigo": partida.codigo_partida,
            "descripcion": partida.descripcion,
            "unidad": partida.unidad_medida,
            "presupuestado": presupuestado,
            "comprado": adquirido,
            "consumido": ejecutado,
            "desviacion": desviacion,
            "desviacion_pct": pct,
            "sobregirada": desviacion > 0,
        })

    # Gráfico: presupuestado vs consumido por partida, dibujado como barras en
    # el propio HTML. Sin librería externa a propósito — el appliance corre en
    # la red interna de la constructora y puede no tener salida a internet.
    tope = max([max(f["presupuestado"], f["consumido"]) for f in filas] + [CERO]) or Decimal("1")
    grafico = {
        "titulo": "Presupuestado vs. consumido por partida",
        "tope": tope,
        "barras": [{
            "etiqueta": f["codigo"],
            "descripcion": f["descripcion"],
            "presupuestado": f["presupuestado"],
            "consumido": f["consumido"],
            "pct_presupuestado": float(f["presupuestado"] / tope * 100),
            "pct_consumido": float(f["consumido"] / tope * 100),
            "sobregirada": f["sobregirada"],
        } for f in filas],
    }

    return {
        "titulo": "Desviación presupuestaria",
        "subtitulo": proyecto.nombre,
        "filtros": [("Proyecto", proyecto.nombre),
                    ("Partidas", str(len(filas))),
                    ("Sobregiradas", str(sum(1 for f in filas if f["sobregirada"])))],
        "columnas": [
            {"clave": "codigo", "titulo": "Partida", "tipo": "texto"},
            {"clave": "descripcion", "titulo": "Descripción", "tipo": "texto"},
            {"clave": "unidad", "titulo": "Unidad", "tipo": "texto"},
            {"clave": "presupuestado", "titulo": "Presupuestado", "tipo": "numero"},
            {"clave": "comprado", "titulo": "Comprado", "tipo": "numero"},
            {"clave": "consumido", "titulo": "Consumido", "tipo": "numero"},
            {"clave": "desviacion", "titulo": "Desviación", "tipo": "numero"},
            {"clave": "desviacion_pct", "titulo": "Desviación %", "tipo": "numero"},
        ],
        "filas": filas,
        "totales": {},
        "vacio": False,
        "grafico": grafico,
    }


# ==========================================================================
#  CU-44 (RF-43) — Mermas y pérdidas
# ==========================================================================

def mermas_y_perdidas(proyecto=None, desde=None, hasta=None):
    """
    Lo que se perdió, valorizado en plata.

    Una merma se registra en unidades; lo que le importa a la administración es
    cuánto costó. Se valoriza al precio de referencia del material, que es el
    único precio que existe para algo que no se compró en esa operación.
    """
    movimientos = (MovimientoInventario.objects
                   .filter(tipo=MovimientoInventario.Tipo.MERMA)
                   .select_related("material", "proyecto", "registrado_por"))
    if proyecto:
        movimientos = movimientos.filter(proyecto=proyecto)
    if desde:
        movimientos = movimientos.filter(fecha__date__gte=desde)
    if hasta:
        movimientos = movimientos.filter(fecha__date__lte=hasta)

    # `motivo` es un CharField sin choices en el modelo (los comparte con las
    # devoluciones), así que la etiqueta legible se resuelve acá.
    etiquetas_motivo = dict(MovimientoInventario.MotivoMerma.choices)

    filas = []
    for m in movimientos.order_by("-fecha"):
        precio = _decimal(m.material.precio_referencia)
        cantidad = _decimal(m.cantidad)
        filas.append({
            "fecha": m.fecha.strftime("%d/%m/%Y"),
            "codigo": m.material.codigo_interno or "—",
            "material": m.material.nombre,
            "cantidad": cantidad,
            "unidad": m.material.unidad_medida,
            "motivo": etiquetas_motivo.get(m.motivo, m.motivo or "—"),
            "proyecto": m.proyecto.nombre if m.proyecto else "Bodega central",
            "registrado_por": m.registrado_por.get_full_name() or m.registrado_por.username,
            "observacion": m.observacion or "",
            "valorizacion": cantidad * precio,
        })

    filtros = [("Proyecto", proyecto.nombre if proyecto else "Todos"),
               ("Desde", desde.strftime("%d/%m/%Y") if desde else "Sin límite"),
               ("Hasta", hasta.strftime("%d/%m/%Y") if hasta else "Sin límite")]

    return {
        "titulo": "Mermas y pérdidas",
        "subtitulo": proyecto.nombre if proyecto else "Todos los proyectos",
        "filtros": filtros,
        "columnas": [
            {"clave": "fecha", "titulo": "Fecha", "tipo": "texto"},
            {"clave": "codigo", "titulo": "Código", "tipo": "texto"},
            {"clave": "material", "titulo": "Material", "tipo": "texto"},
            {"clave": "cantidad", "titulo": "Cantidad", "tipo": "numero"},
            {"clave": "unidad", "titulo": "Unidad", "tipo": "texto"},
            {"clave": "motivo", "titulo": "Motivo", "tipo": "texto"},
            {"clave": "proyecto", "titulo": "Proyecto", "tipo": "texto"},
            {"clave": "registrado_por", "titulo": "Registró", "tipo": "texto"},
            {"clave": "valorizacion", "titulo": "Valorización", "tipo": "moneda"},
        ],
        "filas": filas,
        "totales": {"material": "Pérdida total del periodo",
                    "valorizacion": sum((f["valorizacion"] for f in filas), CERO)},
        "vacio": not filas,
        "mensaje_vacio": "No hay mermas ni pérdidas registradas con estos filtros. "
                         "Es una buena noticia, no un error del reporte.",
    }


# ==========================================================================
#  CU-45 (RF-44) — Historial de compras por proveedor
# ==========================================================================

def compras_por_proveedor(desde=None, hasta=None):
    """
    Cuánto se le compró a cada proveedor en el periodo, y en cuántas operaciones.

    Sólo cuenta órdenes efectivamente emitidas: un borrador o una OC rechazada
    no es una compra, y sumarlas inflaría el historial con plata que nunca salió.
    """
    ordenes = (OrdenCompra.objects
               .exclude(estado__in=[OrdenCompra.Estado.BORRADOR,
                                    OrdenCompra.Estado.RECHAZADA])
               .select_related("proveedor")
               .prefetch_related("lineas"))
    if desde:
        ordenes = ordenes.filter(fecha__date__gte=desde)
    if hasta:
        ordenes = ordenes.filter(fecha__date__lte=hasta)

    por_proveedor = {}
    for orden in ordenes:
        datos = por_proveedor.setdefault(orden.proveedor_id, {
            "proveedor": orden.proveedor.nombre,
            "rut": orden.proveedor.rut_formateado if hasattr(orden.proveedor, "rut_formateado") else orden.proveedor.rut,
            "transacciones": 0,
            "monto_total": CERO,
            "recibidas": 0,
        })
        datos["transacciones"] += 1
        datos["monto_total"] += _decimal(orden.total)
        if orden.estado == OrdenCompra.Estado.RECIBIDA:
            datos["recibidas"] += 1

    filas = sorted(por_proveedor.values(), key=lambda d: d["monto_total"], reverse=True)
    for fila in filas:
        fila["ticket_promedio"] = (fila["monto_total"] / fila["transacciones"]
                                   if fila["transacciones"] else CERO)

    return {
        "titulo": "Historial de compras por proveedor",
        "subtitulo": "Órdenes de compra emitidas",
        "filtros": [("Desde", desde.strftime("%d/%m/%Y") if desde else "Sin límite"),
                    ("Hasta", hasta.strftime("%d/%m/%Y") if hasta else "Sin límite"),
                    ("Proveedores", str(len(filas)))],
        "columnas": [
            {"clave": "proveedor", "titulo": "Proveedor", "tipo": "texto"},
            {"clave": "rut", "titulo": "RUT", "tipo": "texto"},
            {"clave": "transacciones", "titulo": "Órdenes", "tipo": "numero"},
            {"clave": "recibidas", "titulo": "Recibidas", "tipo": "numero"},
            {"clave": "ticket_promedio", "titulo": "Promedio por orden", "tipo": "moneda"},
            {"clave": "monto_total", "titulo": "Monto total", "tipo": "moneda"},
        ],
        "filas": filas,
        "totales": {"proveedor": "Total del periodo",
                    "transacciones": sum(f["transacciones"] for f in filas),
                    "monto_total": sum((f["monto_total"] for f in filas), CERO)},
        "vacio": not filas,
        "mensaje_vacio": "No hay órdenes de compra emitidas en el periodo seleccionado.",
    }
