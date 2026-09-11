"""
Inventario / Bodega.
Catálogo de materiales (Inc.1) + gestión de bodega del Incremento 2:
RF-28/29/30 entrada · RF-31 salida · RF-32 stock en tiempo real ·
RF-33/34 préstamos de herramientas · RF-35 mermas · RF-36 devoluciones a proveedor ·
RF-37 alerta de stock mínimo.
"""
from datetime import date

from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.core.mail import EmailMessage
from django.db.models import Sum, F, Q, DecimalField, ExpressionWrapper
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView

from usuarios.permisos import RolRequeridoMixin, rol_requerido
from adquisiciones.models import OrdenCompra
from .models import Material, MovimientoInventario, PrestamoHerramienta
from .forms import (
    MaterialForm, EntradaForm, SalidaForm, MermaForm,
    DevolucionProveedorForm, PrestamoForm,
)

ROLES = ["BODEGUERO", "ENCARGADO_ADQUISICIONES"]
ROLES_BODEGA = ["BODEGUERO", "ENCARGADO_ADQUISICIONES"]


# ---------------------------------------------------------------- catálogo
class MaterialListView(RolRequeridoMixin, ListView):
    roles_permitidos = ROLES
    model = Material
    template_name = "inventario/material_list.html"
    context_object_name = "materiales"

    def _filtros(self):
        return {
            "q": self.request.GET.get("q", "").strip(),
            "tipo": self.request.GET.get("tipo", "").strip(),
            "estado": self.request.GET.get("estado", "").strip(),
        }

    def get_queryset(self):
        qs = Material.objects.all()
        f = self._filtros()
        if f["q"]:
            qs = qs.filter(
                Q(nombre__icontains=f["q"])
                | Q(unidad_medida__icontains=f["q"])
                | Q(codigo_activo__icontains=f["q"])
                | Q(ubicacion__icontains=f["q"])
            )
        if f["tipo"] in (Material.Tipo.CONSUMIBLE, Material.Tipo.HERRAMIENTA):
            qs = qs.filter(tipo=f["tipo"])
        if f["estado"] == "activo":
            qs = qs.filter(activo=True)
        elif f["estado"] == "inactivo":
            qs = qs.filter(activo=False)
        elif f["estado"] == "critico":  # RF-37
            qs = qs.filter(stock_minimo__gt=0, stock_actual__lte=F("stock_minimo"))
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        f = self._filtros()
        base = Material.objects.all()
        valor_total = base.aggregate(
            total=Coalesce(
                Sum(ExpressionWrapper(
                    F("stock_actual") * F("precio_referencia"),
                    output_field=DecimalField(),
                )),
                0,
                output_field=DecimalField(),
            )
        )["total"]
        criticos = base.filter(stock_minimo__gt=0, stock_actual__lte=F("stock_minimo"))
        ctx["metricas"] = {
            "total": base.count(),
            "activos": base.filter(activo=True).count(),
            "consumibles": base.filter(tipo=Material.Tipo.CONSUMIBLE).count(),
            "herramientas": base.filter(tipo=Material.Tipo.HERRAMIENTA).count(),
            "valor_total": valor_total,
            "criticos": criticos.count(),  # RF-37
        }
        ctx["total_filtrado"] = ctx["materiales"].count() if hasattr(ctx["materiales"], "count") else len(ctx["materiales"])
        ctx["f_q"] = f["q"]
        ctx["f_tipo"] = f["tipo"]
        ctx["f_estado"] = f["estado"]
        ctx["hay_filtros"] = bool(f["q"] or f["tipo"] or f["estado"])
        ctx["oculta_precios"] = self.request.user.rol == "BODEGUERO"  # RF-53
        return ctx


class MaterialCreateView(RolRequeridoMixin, SuccessMessageMixin, CreateView):
    roles_permitidos = ROLES
    model = Material
    form_class = MaterialForm
    template_name = "inventario/material_form.html"
    success_url = reverse_lazy("inventario:lista")
    success_message = "Material agregado al catálogo."


class MaterialUpdateView(RolRequeridoMixin, SuccessMessageMixin, UpdateView):
    roles_permitidos = ROLES
    model = Material
    form_class = MaterialForm
    template_name = "inventario/material_form.html"
    success_url = reverse_lazy("inventario:lista")
    success_message = "Material actualizado."


# ---------------------------------------------------------------- bodega
@rol_requerido(*ROLES_BODEGA)
def bodega_panel(request):
    """Panel de bodega: alertas de stock mínimo (RF-37) y accesos a los movimientos."""
    criticos = Material.objects.filter(
        stock_minimo__gt=0, stock_actual__lte=F("stock_minimo")).order_by("nombre")
    ultimos = MovimientoInventario.objects.select_related("material", "registrado_por")[:10]
    prestamos_activos = PrestamoHerramienta.objects.filter(
        estado=PrestamoHerramienta.Estado.PRESTADA).select_related("herramienta", "proyecto")
    return render(request, "inventario/bodega_panel.html", {
        "criticos": criticos,
        "ultimos": ultimos,
        "prestamos_activos": prestamos_activos,
        "oculta_precios": request.user.rol == "BODEGUERO",
    })


@rol_requerido(*ROLES_BODEGA)
def movimiento_lista(request):
    movimientos = MovimientoInventario.objects.select_related(
        "material", "registrado_por", "proyecto", "orden_compra")
    tipo = request.GET.get("tipo")
    if tipo:
        movimientos = movimientos.filter(tipo=tipo)
    return render(request, "inventario/movimiento_lista.html", {
        "movimientos": movimientos,
        "tipos": MovimientoInventario.Tipo.choices,
        "tipo_filtro": tipo or "",
        "oculta_precios": request.user.rol == "BODEGUERO",
    })


@rol_requerido(*ROLES_BODEGA)
def entrada_crear(request):
    """RF-28/29/30: registrar entrada física de materiales."""
    if request.method == "POST":
        form = EntradaForm(request.POST)
        if form.is_valid():
            d = form.cleaned_data
            mov = MovimientoInventario.objects.create(
                tipo=MovimientoInventario.Tipo.ENTRADA,
                material=d["material"], cantidad=d["cantidad"],
                orden_compra=d["orden_compra"] if d["origen"] == "OC" else None,
                proyecto=d["proyecto"] if d["origen"] == "PROYECTO" else None,
                ubicacion=d["ubicacion"], observacion=d["observacion"],
                registrado_por=request.user,
            )
            if mov.orden_compra:
                _acumular_recepcion_oc(mov.orden_compra, d["material"], d["cantidad"])
            d["material"].refresh_from_db()
            messages.success(request, f"Entrada registrada. Stock de {d['material'].nombre}: {d['material'].stock_actual}")
            return redirect("inventario:movimiento_lista")
    else:
        form = EntradaForm()
    return render(request, "inventario/movimiento_form.html",
                  {"form": form, "titulo": "Registrar entrada a bodega", "tipo": "ENTRADA"})


def _acumular_recepcion_oc(orden, material, cantidad):
    """RF-29/RF-38: suma lo recibido a la línea de la OC y ajusta su estado."""
    linea = orden.lineas.filter(material=material).first()
    if linea:
        linea.cantidad_recibida = linea.cantidad_recibida + cantidad
        linea.save(update_fields=["cantidad_recibida"])
    if orden.recepcion_completa:
        orden.estado = OrdenCompra.Estado.RECIBIDA
    elif orden.recepcion_iniciada:
        orden.estado = OrdenCompra.Estado.RECEPCION_PARCIAL
    orden.save(update_fields=["estado"])
    from adquisiciones.views import _refrescar_estado_recepcion_sm
    _refrescar_estado_recepcion_sm(orden.solicitud)


@rol_requerido(*ROLES_BODEGA)
def salida_crear(request):
    """RF-31: registrar salida de materiales/herramientas hacia una obra."""
    if request.method == "POST":
        form = SalidaForm(request.POST)
        if form.is_valid():
            d = form.cleaned_data
            MovimientoInventario.objects.create(
                tipo=MovimientoInventario.Tipo.SALIDA,
                material=d["material"], cantidad=d["cantidad"],
                proyecto=d["proyecto"], jefe_proyecto=d["jefe_proyecto"],
                guia_despacho=d["guia_despacho"], registrado_por=request.user,
            )
            messages.success(request, "Salida registrada y stock actualizado.")
            return redirect("inventario:movimiento_lista")
    else:
        form = SalidaForm()
    return render(request, "inventario/movimiento_form.html",
                  {"form": form, "titulo": "Registrar salida a obra", "tipo": "SALIDA"})


@rol_requerido(*ROLES_BODEGA)
def merma_crear(request):
    """RF-35: registrar merma o pérdida (motivo Daño / Robo)."""
    if request.method == "POST":
        form = MermaForm(request.POST)
        if form.is_valid():
            d = form.cleaned_data
            MovimientoInventario.objects.create(
                tipo=MovimientoInventario.Tipo.MERMA,
                material=d["material"], cantidad=d["cantidad"],
                motivo=d["motivo"], observacion=d["observacion"],
                registrado_por=request.user,
            )
            messages.success(request, "Merma registrada y descontada del stock.")
            return redirect("inventario:movimiento_lista")
    else:
        form = MermaForm()
    return render(request, "inventario/movimiento_form.html",
                  {"form": form, "titulo": "Registrar merma o pérdida", "tipo": "MERMA"})


@rol_requerido(*ROLES_BODEGA)
def devolucion_proveedor_crear(request):
    """RF-36: registrar devolución de material a un proveedor (asociada a una OC)."""
    if request.method == "POST":
        form = DevolucionProveedorForm(request.POST)
        if form.is_valid():
            d = form.cleaned_data
            MovimientoInventario.objects.create(
                tipo=MovimientoInventario.Tipo.DEVOLUCION_PROVEEDOR,
                material=d["material"], cantidad=d["cantidad"],
                orden_compra=d["orden_compra"], guia_despacho=d["guia_despacho"],
                motivo=d["motivo"], registrado_por=request.user,
            )
            messages.success(request, "Devolución a proveedor registrada y descontada del stock.")
            return redirect("inventario:movimiento_lista")
    else:
        form = DevolucionProveedorForm()
    return render(request, "inventario/movimiento_form.html",
                  {"form": form, "titulo": "Registrar devolución a proveedor", "tipo": "DEVOLUCION"})


# ---------------------------------------------------------------- préstamos
@rol_requerido(*ROLES_BODEGA)
def prestamo_lista(request):
    prestamos = PrestamoHerramienta.objects.select_related(
        "herramienta", "proyecto", "jefe_proyecto")
    estado = request.GET.get("estado")
    if estado:
        prestamos = prestamos.filter(estado=estado)
    return render(request, "inventario/prestamo_lista.html", {
        "prestamos": prestamos, "estado_filtro": estado or "",
    })


@rol_requerido(*ROLES_BODEGA)
def prestamo_crear(request):
    """RF-33: registrar préstamo de herramienta; avisa a Administración."""
    if request.method == "POST":
        form = PrestamoForm(request.POST)
        if form.is_valid():
            prestamo = form.save(commit=False)
            prestamo.registrado_por = request.user
            prestamo.save()
            # La herramienta sale de bodega (RF-32)
            Material.objects.filter(pk=prestamo.herramienta_id).update(
                stock_actual=F("stock_actual") - 1)
            _avisar_administracion(prestamo)
            messages.success(request, "Préstamo registrado. Se notificó a Administración.")
            return redirect("inventario:prestamo_lista")
    else:
        form = PrestamoForm()
    return render(request, "inventario/prestamo_form.html", {"form": form})


@rol_requerido(*ROLES_BODEGA)
def prestamo_devolver(request, pk):
    """RF-34: registrar la devolución de una herramienta prestada."""
    prestamo = get_object_or_404(PrestamoHerramienta, pk=pk)
    if prestamo.estado == PrestamoHerramienta.Estado.PRESTADA:
        prestamo.estado = PrestamoHerramienta.Estado.DEVUELTA
        prestamo.fecha_devolucion_real = date.today()
        prestamo.save(update_fields=["estado", "fecha_devolucion_real"])
        Material.objects.filter(pk=prestamo.herramienta_id).update(
            stock_actual=F("stock_actual") + 1)
        messages.success(request, f"«{prestamo.herramienta.nombre}» devuelta y disponible en bodega.")
    else:
        messages.info(request, "Esta herramienta ya fue devuelta.")
    return redirect("inventario:prestamo_lista")


def _avisar_administracion(prestamo):
    from usuarios.models import usuarios_asignables
    correos = list(
        usuarios_asignables("ADMIN").exclude(email="").values_list("email", flat=True)
    )
    if not correos:
        return
    try:
        EmailMessage(
            subject=f"Préstamo de herramienta: {prestamo.herramienta.nombre}",
            body=(
                f"Se registró el préstamo de «{prestamo.herramienta.nombre}» "
                f"a {prestamo.jefe_proyecto.get_full_name() or prestamo.jefe_proyecto.username} "
                f"para la obra {prestamo.proyecto.nombre}.\n"
                f"Salida: {prestamo.fecha_salida} · Devolución esperada: {prestamo.fecha_devolucion_esperada}."
            ),
            to=correos,
        ).send(fail_silently=True)
    except Exception:  # pragma: no cover
        pass
