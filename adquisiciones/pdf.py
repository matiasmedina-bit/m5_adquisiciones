"""
RF-26: exportación de la Orden de Compra a PDF.

Replica el formato de la «Orden de Compra Electrónica» que M5 emitía en Excel
y que sus proveedores ya reconocen: encabezado con logo y recuadro de folio,
bloque «Datos proveedor», grilla de ítems numerados con la marca de agua M5 de
fondo, firma del representante legal, monto en palabras y pie con neto, IVA
y total.

Se dibuja directamente sobre el canvas de reportlab (no con platypus) porque
es un formulario de posiciones fijas, igual que la planilla original.
"""
import io
import re
import unicodedata
from decimal import Decimal
from pathlib import Path

from django.conf import settings


class ReportlabNoInstalado(RuntimeError):
    pass


RECURSOS = Path(__file__).resolve().parent / "recursos"
LOGO = Path(settings.BASE_DIR) / "static" / "img" / "Logo-M5.png"
MARCA_AGUA = RECURSOS / "marca_agua_m5.png"
FIRMA = RECURSOS / "firma_representante.png"

FILAS_POR_PAGINA = 44


# ---------------------------------------------------------------------------
# Formatos
# ---------------------------------------------------------------------------
def _cantidad(valor):
    """10.00 se imprime «10»; 2.50 se imprime «2,5». Los decimales sólo
    aparecen cuando el material realmente se pide fraccionado."""
    texto = f"{valor:f}"
    if "." in texto:
        texto = texto.rstrip("0").rstrip(".")
    return (texto or "0").replace(".", ",")


def _pesos(valor):
    """1234567 -> «1.234.567» (separador de miles chileno, sin decimales)."""
    return f"{Decimal(valor):,.0f}".replace(",", ".")


def _fecha_larga(valor):
    """«martes, 03 de noviembre de 2026», en la zona horaria de Chile.

    Es el formato que usan las órdenes de compra que M5 emite hoy. Si la
    localización fallara por cualquier motivo, cae a dd-mm-aaaa antes que
    dejar la orden sin fecha.
    """
    from django.utils import timezone
    from django.utils.formats import date_format

    if timezone.is_aware(valor):
        valor = timezone.localtime(valor)
    try:
        return date_format(valor, r"l, d \d\e F \d\e Y")
    except Exception:  # pragma: no cover
        return valor.strftime("%d-%m-%Y")


def _condicion_pago(texto):
    """«30 días» -> «O/C A 30 DIAS», como se imprime en las OC de M5."""
    plano = unicodedata.normalize("NFD", texto or "").encode("ascii", "ignore").decode().upper()
    m = re.search(r"(\d+)\s*DIAS", plano)
    return f"O/C A {m.group(1)} DIAS" if m else plano


_UNIDADES = ["", "UN", "DOS", "TRES", "CUATRO", "CINCO", "SEIS", "SIETE", "OCHO", "NUEVE"]
_DIEZ_A_VEINTINUEVE = [
    "DIEZ", "ONCE", "DOCE", "TRECE", "CATORCE", "QUINCE", "DIECISÉIS", "DIECISIETE",
    "DIECIOCHO", "DIECINUEVE", "VEINTE", "VEINTIÚN", "VEINTIDÓS", "VEINTITRÉS",
    "VEINTICUATRO", "VEINTICINCO", "VEINTISÉIS", "VEINTISIETE", "VEINTIOCHO", "VEINTINUEVE",
]
_DECENAS = ["", "", "", "TREINTA", "CUARENTA", "CINCUENTA", "SESENTA", "SETENTA",
            "OCHENTA", "NOVENTA"]
_CENTENAS = ["", "CIENTO", "DOSCIENTOS", "TRESCIENTOS", "CUATROCIENTOS", "QUINIENTOS",
             "SEISCIENTOS", "SETECIENTOS", "OCHOCIENTOS", "NOVECIENTOS"]


def _menor_mil(n):
    if n == 100:
        return "CIEN"
    centena, resto = divmod(n, 100)
    partes = [_CENTENAS[centena]] if centena else []
    if 10 <= resto <= 29:
        partes.append(_DIEZ_A_VEINTINUEVE[resto - 10])
    elif resto:
        decena, unidad = divmod(resto, 10)
        if decena:
            partes.append(_DECENAS[decena] + (f" Y {_UNIDADES[unidad]}" if unidad else ""))
        else:
            partes.append(_UNIDADES[unidad])
    return " ".join(partes)


def _menor_millon(n):
    miles, resto = divmod(n, 1000)
    partes = []
    if miles == 1:
        partes.append("MIL")
    elif miles:
        partes.append(f"{_menor_mil(miles)} MIL")
    if resto:
        partes.append(_menor_mil(resto))
    return " ".join(partes)


def monto_en_palabras(valor):
    """29674 -> «VEINTINUEVE MIL SEISCIENTOS SETENTA Y CUATRO PESOS.»"""
    n = int(Decimal(valor).quantize(Decimal("1")))
    if n == 0:
        return "CERO PESOS."
    millones, resto = divmod(n, 1_000_000)
    partes = []
    if millones == 1:
        partes.append("UN MILLÓN")
    elif millones:
        partes.append(f"{_menor_millon(millones)} MILLONES")
    if resto:
        partes.append(_menor_millon(resto))
    texto = " ".join(partes)
    if n == 1:
        return "UN PESO."
    if millones and not resto:
        return f"{texto} DE PESOS."
    return f"{texto} PESOS."


# ---------------------------------------------------------------------------
# Datos de la orden
# ---------------------------------------------------------------------------
def _codigo_linea(linea, proveedor):
    """El código con que el proveedor conoce el material (como en la OC de
    ejemplo: el SKU de Sodimac). Si no está en su catálogo, el interno de M5."""
    from proveedores.models import ProveedorMaterial

    oferta = (ProveedorMaterial.objects
              .filter(proveedor=proveedor, material=linea.material)
              .order_by("-disponible", "-modificado").first())
    if oferta:
        return oferta.codigo
    return getattr(linea.material, "codigo_interno", "") or ""


def _filas_orden(orden):
    filas = [{
        "codigo": _codigo_linea(l, orden.proveedor),
        "descripcion": (l.descripcion or "").upper(),
        "cantidad": _cantidad(l.cantidad),
        "precio": f"${_pesos(l.valor_unitario)}",
        "total": _pesos(l.valor_total),
    } for l in orden.lineas.select_related("material").all()]
    if orden.costo_despacho:
        filas.append({"codigo": "", "descripcion": "DESPACHO", "cantidad": "1",
                      "precio": f"${_pesos(orden.costo_despacho)}",
                      "total": _pesos(orden.costo_despacho)})
    return filas


def _firmada(orden):
    """La firma del representante sólo va en órdenes ya autorizadas: un
    borrador firmado podría circular como si fuera una orden válida."""
    return bool(orden.fecha_aprobacion) and orden.estado not in (
        orden.Estado.BORRADOR, orden.Estado.RECHAZADA)


# ---------------------------------------------------------------------------
# Dibujo
# ---------------------------------------------------------------------------
def generar_pdf_orden(orden) -> bytes:
    """Devuelve el PDF de la orden como bytes. Lanza ReportlabNoInstalado si falta la librería."""
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import mm
        from reportlab.lib.utils import ImageReader, simpleSplit
        from reportlab.pdfgen import canvas as rl_canvas
    except ImportError as exc:  # pragma: no cover
        raise ReportlabNoInstalado(
            "Falta la librería 'reportlab'. Ejecuta: pip install -r requirements.txt"
        ) from exc

    def imagen(ruta):
        try:
            return ImageReader(str(ruta)) if ruta.exists() else None
        except Exception:  # pragma: no cover - PNG ilegible: se omite
            return None

    logo, marca, firma = imagen(LOGO), imagen(MARCA_AGUA), imagen(FIRMA)

    ancho, alto = A4
    X0, X1 = 10 * mm, ancho - 10 * mm
    AZUL = colors.HexColor("#1f3b57")
    GRIS = colors.HexColor("#c8c8c8")
    NEGRO = colors.black

    proveedor = orden.proveedor
    obra = orden.obra
    filas = _filas_orden(orden)
    paginas = [filas[i:i + FILAS_POR_PAGINA] for i in range(0, len(filas), FILAS_POR_PAGINA)] or [[]]
    folio = orden.correlativo
    fecha = orden.fecha_aprobacion or orden.fecha

    buffer = io.BytesIO()
    c = rl_canvas.Canvas(buffer, pagesize=A4)
    c.setTitle(f"Orden de Compra {folio}")
    c.setAuthor(settings.EMPRESA_RAZON_SOCIAL)

    # Columnas de la grilla: ITEM | CODIGO | DESCRIPCION | CANTIDAD | PRECIO | TOTAL
    cols = [X0, X0 + 9 * mm, X0 + 27 * mm, X1 - 66 * mm, X1 - 48 * mm, X1 - 26 * mm, X1]

    def texto(x, y, s, size=8, bold=False, color=NEGRO, align="left"):
        c.setFillColor(color)
        c.setFont("Helvetica-Bold" if bold else "Helvetica", size)
        if align == "right":
            c.drawRightString(x, y, s)
        elif align == "center":
            c.drawCentredString(x, y, s)
        else:
            c.drawString(x, y, s)

    def recortar(s, ancho_max, size=8, bold=False):
        fuente = "Helvetica-Bold" if bold else "Helvetica"
        while s and c.stringWidth(s, fuente, size) > ancho_max:
            s = s[:-1]
        return s

    for n_pag, filas_pag in enumerate(paginas, start=1):
        ultima = n_pag == len(paginas)
        offset_item = (n_pag - 1) * FILAS_POR_PAGINA

        # --- Marca de agua (primero, para que quede detrás de todo) ---
        if marca:
            mw = 190 * mm
            mh = mw * marca.getSize()[1] / marca.getSize()[0]
            c.drawImage(marca, (ancho - mw) / 2, 70 * mm, mw, mh, mask="auto")

        # --- Encabezado ---
        top = alto - 10 * mm
        if logo:
            c.drawImage(logo, X0, top - 24 * mm, 38 * mm, 24 * mm,
                        preserveAspectRatio=True, mask="auto")
        cx = X0 + 100 * mm  # columna derecha del bloque de la empresa
        y = top - 3 * mm
        texto(cx, y, settings.EMPRESA_RAZON_SOCIAL.upper(), 10, bold=True, align="right")
        y -= 4 * mm
        texto(cx, y, f"R.U.T.: {settings.EMPRESA_RUT}", 7, align="right")
        for linea in simpleSplit(settings.EMPRESA_GIRO.upper(), "Helvetica", 6.5, 62 * mm):
            y -= 3.2 * mm
            texto(cx, y, linea, 6.5, align="right")
        for linea in [p.strip() for p in settings.EMPRESA_DIRECCION.split(",")]:
            y -= 3.2 * mm
            texto(cx, y, linea, 6.5, align="right")
        y -= 3.2 * mm
        texto(cx, y, f"Teléfono: {settings.EMPRESA_TELEFONO}", 6.5, align="right")
        y -= 3.2 * mm
        texto(cx, y, f"e-mail: {settings.EMPRESA_EMAIL}  -  {settings.EMPRESA_WEB}", 6.5,
              color=AZUL, align="right")

        # Recuadro del folio
        bx, bw, bh = X1 - 78 * mm, 78 * mm, 27 * mm
        c.setStrokeColor(NEGRO)
        c.setLineWidth(1)
        c.rect(bx, top - bh, bw, bh)
        texto(bx + bw / 2, top - 8 * mm, "ORDEN DE COMPRA ELECTRÓNICA", 11, bold=True, align="center")
        texto(bx + 8 * mm, top - 18 * mm, "FOLIO N°", 11, bold=True)
        c.setLineWidth(1.2)
        c.rect(bx + 30 * mm, top - 20.5 * mm, 36 * mm, 7 * mm)
        texto(bx + 64 * mm, top - 18.5 * mm, folio, 11, bold=True, align="right")
        if not _firmada(orden):
            texto(bx + bw / 2, top - 25 * mm,
                  f"{orden.get_estado_display().upper()} — SIN VALIDEZ HASTA SU APROBACIÓN",
                  6.5, bold=True, color=colors.HexColor("#b02a37"), align="center")
        if len(paginas) > 1:
            texto(X1, top - bh - 3 * mm, f"Página {n_pag} de {len(paginas)}", 6.5, align="right")

        # --- Datos proveedor ---
        y = top - 33 * mm
        c.setFillColor(colors.HexColor("#efefef"))
        c.rect(X0, y, X1 - X0, 4 * mm, fill=1, stroke=0)
        texto(X0 + 1 * mm, y + 1.1 * mm, "DATOS PROVEEDOR", 6.5, bold=True)
        caja_alto = 19 * mm
        c.setStrokeColor(NEGRO)
        c.setLineWidth(0.8)
        c.rect(X0, y - caja_alto, X1 - X0, caja_alto)
        mitad = X0 + 115 * mm
        izq = [
            ("Fecha:", _fecha_larga(fecha), False),
            ("Señores:", (orden.proveedor_razon_social or proveedor.nombre).upper(), True),
            ("Dirección:", (proveedor.direccion or "").upper(), False),
            ("Comuna:", (proveedor.comuna or "").upper(), False),
        ]
        der = [
            ("R.U.T.:", orden.proveedor_rut or proveedor.rut_formateado, False),
            ("Giro:", (proveedor.giro or "").upper(), False),
            ("Cond.pag", _condicion_pago(orden.proveedor_condicion_pago
                                         or proveedor.get_condicion_pago_display()), True),
            ("Obra:", (f"{obra.centro_costo} {obra.nombre}".strip().upper() if obra else ""), True),
        ]
        for i, ((e1, v1, b1), (e2, v2, b2)) in enumerate(zip(izq, der)):
            fy = y - 4 * mm - i * 4.3 * mm
            texto(X0 + 1.5 * mm, fy, e1, 6.5, bold=True)
            texto(X0 + 18 * mm, fy, recortar(v1, mitad - X0 - 20 * mm, 8.5 if b1 else 8, b1),
                  8.5 if b1 else 8, bold=b1)
            texto(mitad, fy, e2, 6.5, bold=True)
            texto(mitad + 15 * mm, fy, recortar(v2, X1 - mitad - 16 * mm, 8, b2), 8, bold=b2)

        # --- Grilla de ítems ---
        g_top = y - caja_alto - 2 * mm
        alto_fila = 4.35 * mm
        enc_alto = 4.5 * mm
        g_bottom = g_top - enc_alto - FILAS_POR_PAGINA * alto_fila
        c.setLineWidth(0.8)
        c.rect(X0, g_bottom, X1 - X0, g_top - g_bottom)
        c.line(X0, g_top - enc_alto, X1, g_top - enc_alto)
        for xc in cols[1:-1]:
            c.line(xc, g_top, xc, g_bottom)
        titulos = ["ITEM", "CODIGO", "DESCRIPCION", "CANTIDAD", "PRECIO", "TOTAL"]
        for i, t in enumerate(titulos):
            texto((cols[i] + cols[i + 1]) / 2, g_top - 3.3 * mm, t, 7.5 if i else 6, bold=True,
                  align="center")
        c.setStrokeColor(GRIS)
        c.setLineWidth(0.25)
        for r in range(1, FILAS_POR_PAGINA):
            fy = g_top - enc_alto - r * alto_fila
            c.line(X0, fy, X1, fy)
        c.setStrokeColor(NEGRO)

        for r in range(FILAS_POR_PAGINA):
            base = g_top - enc_alto - (r + 1) * alto_fila + 1.3 * mm
            fila = filas_pag[r] if r < len(filas_pag) else None
            texto(cols[1] - 1 * mm, base, str(offset_item + r + 1), 6, align="right")
            texto(cols[5] + 1.5 * mm, base, "$", 7.5)
            if fila is None:
                texto(cols[6] - 3 * mm, base, "-", 7.5, align="right")
                continue
            texto(cols[2] - 1 * mm, base, recortar(fila["codigo"], cols[2] - cols[1] - 2 * mm, 7.5),
                  7.5, align="right")
            texto(cols[2] + 1.2 * mm, base,
                  recortar(fila["descripcion"], cols[3] - cols[2] - 2.5 * mm, 7.5), 7.5)
            texto((cols[3] + cols[4]) / 2, base, fila["cantidad"], 7.5, align="center")
            texto(cols[5] - 1.2 * mm, base, fila["precio"], 7.5, align="right")
            texto(cols[6] - 1.5 * mm, base, fila["total"], 7.5, align="right")

        # Firma del representante legal, sobre las últimas filas de la descripción
        if ultima and _firmada(orden):
            fx = cols[2] + 3 * mm
            fy = g_bottom + 22 * mm
            texto(fx, fy, "Autorizado por Representante legal "
                          f"{settings.EMPRESA_REPRESENTANTE_NOMBRE}", 7.5)
            texto(fx, fy - 3.6 * mm, f"C.I. {settings.EMPRESA_REPRESENTANTE_RUT}", 7.5)
            if firma:
                fw = 40 * mm
                fh = fw * firma.getSize()[1] / firma.getSize()[0]
                c.drawImage(firma, fx + 22 * mm, g_bottom + 1 * mm, fw, fh, mask="auto")

        # --- Pie ---
        p_top = g_bottom
        fila_pie = 5 * mm
        c.setLineWidth(0.8)
        # NOMBRE | R.U.T. | FIRMA  (lo completa quien recibe)
        c.rect(X0, p_top - fila_pie, X1 - X0, fila_pie)
        c.line(cols[3] - 40 * mm, p_top - fila_pie, cols[3] - 40 * mm, p_top)
        c.line(cols[4], p_top - fila_pie, cols[4], p_top)
        texto(X0 + 1.5 * mm, p_top - 3.5 * mm, "NOMBRE", 7, bold=True)
        texto(cols[3] - 39 * mm, p_top - 3.5 * mm, "R.U.T.:", 7, bold=True)
        texto(cols[4] + 1.5 * mm, p_top - 3.5 * mm, "FIRMA:", 7, bold=True)

        t_top = p_top - fila_pie
        t_alto = 3 * fila_pie
        c.rect(X0, t_top - t_alto, X1 - X0, t_alto)
        c.line(cols[4], t_top, cols[4], t_top - t_alto)
        c.line(cols[5], t_top, cols[5], t_top - t_alto)
        if ultima:
            texto(X0 + 1.5 * mm, t_top - 3.6 * mm, "SON:", 8, bold=True)
            palabras = simpleSplit(monto_en_palabras(orden.total_con_iva), "Helvetica-Bold", 8.5,
                                   cols[4] - X0 - 16 * mm)
            for i, linea in enumerate(palabras[:3]):
                texto(X0 + 13 * mm, t_top - 3.6 * mm - i * 4 * mm, linea, 8.5, bold=True)
            iva_pct = getattr(settings, "IVA_PORCENTAJE", 19)
            for i, (etq, val, b) in enumerate([("NETO", orden.total, False),
                                               (f"I.V.A. {iva_pct}%", orden.iva, False),
                                               ("TOTAL:", orden.total_con_iva, True)]):
                fy = t_top - 3.6 * mm - i * fila_pie
                texto(cols[4] + 1.5 * mm, fy, etq, 8, bold=True)
                texto(cols[5] + 1.5 * mm, fy, "$", 8, bold=b)
                texto(cols[6] - 1.5 * mm, fy, _pesos(val), 9 if b else 8, bold=True, align="right")
            c.line(cols[4], t_top - 2 * fila_pie, X1, t_top - 2 * fila_pie)
        else:
            texto(X0 + 1.5 * mm, t_top - 3.6 * mm, "Continúa en la página siguiente…", 8)

        # Observaciones: de dónde viene la compra
        o_top = t_top - t_alto
        c.rect(X0, o_top - fila_pie, X1 - X0, fila_pie)
        texto(X0 + 1.5 * mm, o_top - 3.5 * mm, "OBS:", 7, bold=True)
        obs = (f"Solicitud de materiales {orden.solicitud.correlativo}" if orden.solicitud_id
               else "Compra anticipada (sin solicitud previa)")
        texto(X0 + 11 * mm, o_top - 3.5 * mm, obs, 7)

        c.showPage()

    c.save()
    return buffer.getvalue()
