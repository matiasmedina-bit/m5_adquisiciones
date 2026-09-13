"""
Búsqueda de materiales para la pantalla de solicitud (CU-12).

Dos endpoints JSON que resuelven el cruce proveedor ↔ material en los dos
sentidos, que es como trabaja de verdad quien compra:

  · Ya sé a quién comprarle  -> elijo proveedor y busco dentro de su catálogo.
  · Sé qué necesito          -> escribo el material y veo quién lo tiene,
                                con su precio, para elegir.

Ninguno de los dos devuelve más de LIMITE filas: la lista es para elegir
rápido, no para pasearse por el catálogo completo.
"""
from django.db.models import Q
from django.http import JsonResponse

from proveedores.models import Proveedor, ProveedorMaterial
from inventario.models import Material
from proyectos.models import Itemizado
from usuarios.permisos import rol_requerido

LIMITE = 12
ROLES = ("ENCARGADO_ADQUISICIONES", "JEFE_PROYECTO")


def _miles(valor):
    """Formato chileno para mostrar en el desplegable: $5.490"""
    try:
        entero = int(valor or 0)
    except (TypeError, ValueError):
        return ""
    if entero <= 0:
        return ""
    return "$" + f"{entero:,}".replace(",", ".")


def _fila_oferta(oferta):
    return {
        "tipo": "oferta",
        "pm": oferta.pk,
        "material": oferta.material_id,
        "codigo": oferta.codigo,
        "descripcion": oferta.descripcion,
        "unidad": oferta.unidad_medida or "un",
        "precio": int(oferta.precio or 0),
        "precio_txt": _miles(oferta.precio),
        "proveedor": oferta.proveedor_id,
        "proveedor_nombre": oferta.proveedor.nombre,
        "condicion": oferta.condicion_pago_efectiva,
    }


def _fila_material(material):
    return {
        "tipo": "catalogo",
        "pm": None,
        "material": material.pk,
        "codigo": "",
        "descripcion": material.nombre,
        "unidad": material.unidad_medida or "un",
        "precio": int(material.precio_referencia or 0),
        "precio_txt": _miles(material.precio_referencia),
        "proveedor": None,
        "proveedor_nombre": "",
        "condicion": "",
    }


@rol_requerido(*ROLES)
def buscar_materiales(request):
    """
    GET ?q=texto&proveedor=<id opcional>

    Con proveedor: sólo su catálogo disponible.
    Sin proveedor: los catálogos de todos los proveedores activos, y además
    los materiales del catálogo general que nadie ofrece todavía (para poder
    pedir algo aunque aún no se sepa a quién comprárselo).
    """
    texto = (request.GET.get("q") or "").strip()
    proveedor_id = (request.GET.get("proveedor") or "").strip()

    ofertas = ProveedorMaterial.objects.select_related("proveedor").filter(
        disponible=True, proveedor__estado=True,
    )
    if proveedor_id.isdigit():
        ofertas = ofertas.filter(proveedor_id=int(proveedor_id))
    if texto:
        ofertas = ofertas.filter(
            Q(descripcion__icontains=texto) | Q(codigo__icontains=texto)
        )

    resultados = [_fila_oferta(o) for o in ofertas.order_by("descripcion")[:LIMITE]]

    # Sin proveedor fijado, completar con materiales del catálogo general que
    # no aparecieron ya como oferta de alguien.
    if not proveedor_id.isdigit() and len(resultados) < LIMITE:
        vistos = {fila["descripcion"].lower() for fila in resultados}
        materiales = Material.objects.filter(activo=True)
        if texto:
            materiales = materiales.filter(nombre__icontains=texto)
        for material in materiales.order_by("nombre")[: LIMITE * 2]:
            if material.nombre.lower() in vistos:
                continue
            resultados.append(_fila_material(material))
            vistos.add(material.nombre.lower())
            if len(resultados) >= LIMITE:
                break

    return JsonResponse({"resultados": resultados, "total": len(resultados)})


@rol_requerido(*ROLES)
def proveedores_de(request):
    """
    GET ?q=texto  ó  ?material=<id>

    Devuelve qué proveedores ofrecen ese material y a qué precio, ordenados
    del más barato al más caro. Es lo que permite escribir el material primero
    y que el selector de la izquierda se reduzca a quienes lo tienen.
    """
    texto = (request.GET.get("q") or "").strip()
    material_id = (request.GET.get("material") or "").strip()

    ofertas = ProveedorMaterial.objects.select_related("proveedor").filter(
        disponible=True, proveedor__estado=True,
    )
    if material_id.isdigit():
        material = Material.objects.filter(pk=int(material_id)).first()
        condicion = Q(material_id=int(material_id))
        if material:
            condicion |= Q(descripcion__iexact=material.nombre)
        ofertas = ofertas.filter(condicion)
    elif texto:
        ofertas = ofertas.filter(
            Q(descripcion__icontains=texto) | Q(codigo__icontains=texto)
        )
    else:
        return JsonResponse({"proveedores": [], "total": 0})

    # Un proveedor puede tener varias líneas que calcen; se queda la más barata
    por_proveedor = {}
    for oferta in ofertas.order_by("precio"):
        actual = por_proveedor.get(oferta.proveedor_id)
        if actual is None or (oferta.precio or 0) < (actual["precio"] or 0):
            por_proveedor[oferta.proveedor_id] = {
                "id": oferta.proveedor_id,
                "nombre": oferta.proveedor.nombre,
                "pm": oferta.pk,
                "codigo": oferta.codigo,
                "descripcion": oferta.descripcion,
                "unidad": oferta.unidad_medida or "un",
                "precio": int(oferta.precio or 0),
                "precio_txt": _miles(oferta.precio),
                "condicion": oferta.condicion_pago_efectiva,
            }

    lista = sorted(
        por_proveedor.values(),
        key=lambda p: (p["precio"] == 0, p["precio"], p["nombre"]),
    )[:LIMITE]
    return JsonResponse({"proveedores": lista, "total": len(lista)})


@rol_requerido(*ROLES)
def partidas_de_proyecto(request):
    """
    GET ?proyecto=<id>

    Partidas del itemizado de un proyecto con su saldo disponible. Alimenta el
    selector de partida de la solicitud, que en la pantalla de creación no puede
    conocerse en el servidor: el proyecto se elige en el mismo formulario.

    El saldo viaja al navegador para que la alerta del CU-13 —cantidad que
    supera la partida— se dispare mientras se escribe, y no recién al guardar.
    """
    proyecto_id = (request.GET.get("proyecto") or "").strip()
    if not proyecto_id.isdigit():
        return JsonResponse({"partidas": [], "total": 0})

    partidas = []
    for item in Itemizado.objects.filter(proyecto_id=int(proyecto_id)).order_by("codigo_partida"):
        saldo = float(item.saldo_disponible)
        partidas.append({
            "id": item.pk,
            "codigo": item.codigo_partida,
            "descripcion": item.descripcion,
            "unidad": item.unidad_medida,
            "presupuestado": float(item.cant_presupuestada),
            "ejecutado": float(item.cant_ejecutada),
            "saldo": saldo,
            "etiqueta": f"{item.codigo_partida} · {item.descripcion} (saldo {saldo:g} {item.unidad_medida})",
        })
    return JsonResponse({"partidas": partidas, "total": len(partidas)})
