"""
RF-26: exportación de la Orden de Compra a PDF estructurado con el logotipo
corporativo de Constructora M5 SpA. Usa reportlab (requirements.txt).
"""
import io
from pathlib import Path

from django.conf import settings


class ReportlabNoInstalado(RuntimeError):
    pass


def generar_pdf_orden(orden) -> bytes:
    """Devuelve el PDF de la orden como bytes. Lanza ReportlabNoInstalado si falta la librería."""
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import mm
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import (
            SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image,
        )
    except ImportError as exc:  # pragma: no cover
        raise ReportlabNoInstalado(
            "Falta la librería 'reportlab'. Ejecuta: pip install -r requirements.txt"
        ) from exc

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        leftMargin=18 * mm, rightMargin=18 * mm,
        topMargin=16 * mm, bottomMargin=16 * mm,
        title=f"Orden de Compra {orden.correlativo}",
    )
    estilos = getSampleStyleSheet()
    normal = estilos["Normal"]
    h1 = estilos["Heading1"]
    h2 = estilos["Heading2"]
    elementos = []

    # Encabezado con logo (si falla la decodificación del PNG, se omite)
    logo_path = Path(settings.BASE_DIR) / "static" / "img" / "Logo-M5.png"
    encabezado_izq = []
    if logo_path.exists():
        try:
            encabezado_izq.append(Image(str(logo_path), width=38 * mm, height=38 * mm))
        except Exception:  # pragma: no cover
            encabezado_izq = []
    encabezado_der = Paragraph(
        f"<b>{settings.EMPRESA_RAZON_SOCIAL}</b><br/>"
        f"RUT: {settings.EMPRESA_RUT}<br/>"
        f"Giro: {settings.EMPRESA_GIRO}<br/>"
        f"{settings.EMPRESA_DIRECCION}",
        normal,
    )
    tabla_enc = Table([[encabezado_izq or "", encabezado_der]], colWidths=[45 * mm, None])
    tabla_enc.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
    elementos += [tabla_enc, Spacer(1, 8 * mm)]

    elementos.append(Paragraph(f"ORDEN DE COMPRA {orden.correlativo}", h1))
    elementos.append(Paragraph(
        f"Fecha: {orden.fecha:%d-%m-%Y} &nbsp;&nbsp; Solicitud: {orden.solicitud.correlativo} "
        f"&nbsp;&nbsp; Proyecto: {orden.solicitud.proyecto.nombre}",
        normal,
    ))
    elementos.append(Spacer(1, 5 * mm))

    elementos.append(Paragraph("Proveedor", h2))
    elementos.append(Paragraph(
        f"{orden.proveedor_razon_social or orden.proveedor.nombre}<br/>"
        f"RUT: {orden.proveedor_rut or orden.proveedor.rut_formateado}<br/>"
        f"Condición de pago: {orden.proveedor_condicion_pago or orden.proveedor.get_condicion_pago_display()}",
        normal,
    ))
    elementos.append(Spacer(1, 5 * mm))

    # Tabla de líneas
    filas = [["#", "Material", "Cantidad", "Unidad", "V. Unitario", "V. Total"]]
    for i, l in enumerate(orden.lineas.all(), start=1):
        filas.append([
            str(i), l.descripcion, f"{l.cantidad:g}", l.unidad_medida or "",
            f"${l.valor_unitario:,.0f}", f"${l.valor_total:,.0f}",
        ])
    filas.append(["", "", "", "", "Despacho", f"${orden.costo_despacho:,.0f}"])
    filas.append(["", "", "", "", "TOTAL", f"${orden.total:,.0f}"])

    tabla = Table(filas, colWidths=[10 * mm, None, 22 * mm, 18 * mm, 26 * mm, 26 * mm])
    tabla.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f3b57")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -3), 0.4, colors.grey),
        ("ALIGN", (2, 0), (-1, -1), "RIGHT"),
        ("FONTNAME", (4, -1), (-1, -1), "Helvetica-Bold"),
        ("LINEABOVE", (4, -2), (-1, -2), 0.8, colors.black),
    ]))
    elementos.append(tabla)
    elementos.append(Spacer(1, 10 * mm))
    elementos.append(Paragraph(
        "Documento generado por el Sistema de Gestión de Adquisiciones e Inventario — "
        "Constructora M5 SpA.", normal))

    doc.build(elementos)
    return buffer.getvalue()
