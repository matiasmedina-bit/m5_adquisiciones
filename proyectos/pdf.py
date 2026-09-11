"""
Exportación de la ficha de un proyecto a PDF, para compartirla con el mandante.

Mismo criterio gráfico que la Orden de Compra (adquisiciones/pdf.py): logotipo
corporativo, cabecera con los datos de Constructora M5 SpA y tablas con el azul
institucional. Usa reportlab (requirements.txt).
"""
import io
from pathlib import Path

from django.conf import settings
from django.utils import timezone


class ReportlabNoInstalado(RuntimeError):
    pass


def _miles(valor):
    """Formato chileno: 1.234.567 (el separador de miles es el punto)."""
    try:
        return f"{int(valor):,}".replace(",", ".")
    except (TypeError, ValueError):
        return "0"


def _cantidad(valor):
    """Cantidades del itemizado: sin decimales si son enteras."""
    try:
        numero = float(valor)
    except (TypeError, ValueError):
        return "0"
    if numero == int(numero):
        return _miles(int(numero))
    return f"{numero:,.2f}".replace(",", "·").replace(".", ",").replace("·", ".")


def generar_pdf_proyecto(proyecto) -> bytes:
    """Devuelve la ficha del proyecto como bytes de un PDF."""
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import mm
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.platypus import (
            SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image,
        )
    except ImportError as exc:  # pragma: no cover
        raise ReportlabNoInstalado(
            "Falta la librería 'reportlab'. Ejecuta: pip install -r requirements.txt"
        ) from exc

    AZUL = colors.HexColor("#1f3b57")

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        leftMargin=18 * mm, rightMargin=18 * mm,
        topMargin=16 * mm, bottomMargin=16 * mm,
        title=f"Proyecto {proyecto.nombre}",
        author=settings.EMPRESA_RAZON_SOCIAL,
    )
    estilos = getSampleStyleSheet()
    normal = estilos["Normal"]
    h1 = estilos["Heading1"]
    h2 = estilos["Heading2"]
    pie = ParagraphStyle("pie", parent=normal, fontSize=7.5, textColor=colors.grey)
    celda = ParagraphStyle("celda", parent=normal, fontSize=8, leading=10)

    elementos = []

    # ---------------- Encabezado corporativo ----------------
    logo_path = Path(settings.BASE_DIR) / "static" / "img" / "Logo-M5.png"
    encabezado_izq = ""
    if logo_path.exists():
        try:
            encabezado_izq = Image(str(logo_path), width=38 * mm, height=38 * mm)
        except Exception:  # pragma: no cover
            encabezado_izq = ""
    encabezado_der = Paragraph(
        f"<b>{settings.EMPRESA_RAZON_SOCIAL}</b><br/>"
        f"RUT: {settings.EMPRESA_RUT}<br/>"
        f"Giro: {settings.EMPRESA_GIRO}<br/>"
        f"{settings.EMPRESA_DIRECCION}",
        normal,
    )
    tabla_enc = Table([[encabezado_izq, encabezado_der]], colWidths=[45 * mm, None])
    tabla_enc.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
    elementos += [tabla_enc, Spacer(1, 8 * mm)]

    # ---------------- Identificación del proyecto ----------------
    elementos.append(Paragraph(f"FICHA DE PROYECTO — {proyecto.nombre.upper()}", h1))
    elementos.append(Paragraph(
        f"Mandante: <b>{proyecto.mandante}</b>", normal))
    elementos.append(Spacer(1, 5 * mm))

    jefe = proyecto.jefe_proyecto
    jefe_txt = (jefe.get_full_name() or jefe.username) if jefe else "Sin asignar"

    ficha = [
        ["Centro de costo", proyecto.centro_costo or "—",
         "Estado", proyecto.get_estado_display()],
        ["Jefe de proyecto", jefe_txt,
         "Presupuesto", f"${_miles(proyecto.presupuesto_total)}"],
        ["Fecha de inicio", f"{proyecto.fecha_inicio:%d-%m-%Y}",
         "Fecha de término",
         f"{proyecto.fecha_termino:%d-%m-%Y}" if proyecto.fecha_termino else "—"],
    ]
    tabla_ficha = Table(ficha, colWidths=[32 * mm, None, 30 * mm, 38 * mm])
    tabla_ficha.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("TEXTCOLOR", (0, 0), (0, -1), colors.grey),
        ("TEXTCOLOR", (2, 0), (2, -1), colors.grey),
        ("FONTNAME", (1, 0), (1, -1), "Helvetica-Bold"),
        ("FONTNAME", (3, 0), (3, -1), "Helvetica-Bold"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("LINEBELOW", (0, 0), (-1, -2), 0.3, colors.HexColor("#dddddd")),
    ]))
    elementos += [tabla_ficha, Spacer(1, 7 * mm)]

    # ---------------- Itemizado ----------------
    elementos.append(Paragraph("Itemizado presupuestario", h2))
    itemizados = list(proyecto.itemizados.all())
    if itemizados:
        filas = [["Partida", "Descripción", "Unidad", "Presupuestado", "Ejecutado", "Saldo"]]
        for item in itemizados:
            filas.append([
                item.codigo_partida,
                Paragraph(item.descripcion, celda),
                item.unidad_medida,
                _cantidad(item.cant_presupuestada),
                _cantidad(item.cant_ejecutada),
                _cantidad(item.saldo_disponible),
            ])
        tabla_items = Table(
            filas, colWidths=[24 * mm, None, 18 * mm, 26 * mm, 22 * mm, 22 * mm],
            repeatRows=1,
        )
        estilo_items = [
            ("BACKGROUND", (0, 0), (-1, 0), AZUL),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
            ("ALIGN", (3, 0), (-1, -1), "RIGHT"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]
        # Resalta en rojo las partidas sin saldo
        for fila, item in enumerate(itemizados, start=1):
            if item.saldo_disponible < 0:
                estilo_items.append(
                    ("TEXTCOLOR", (5, fila), (5, fila), colors.HexColor("#a33a2c"))
                )
        tabla_items.setStyle(TableStyle(estilo_items))
        elementos.append(tabla_items)
    else:
        elementos.append(Paragraph(
            "Este proyecto aún no tiene partidas cargadas en su itemizado.", normal))
    elementos.append(Spacer(1, 7 * mm))

    # ---------------- Solicitudes asociadas ----------------
    solicitudes = list(proyecto.solicitudes.all()[:40])
    elementos.append(Paragraph("Solicitudes de material asociadas", h2))
    if solicitudes:
        filas_sm = [["Correlativo", "Fecha", "Emisor", "Ítems", "Estado"]]
        for sm in solicitudes:
            emisor = sm.emisor.get_full_name() or sm.emisor.username
            filas_sm.append([
                sm.correlativo, f"{sm.fecha:%d-%m-%Y}", Paragraph(emisor, celda),
                str(sm.total_items), sm.get_estado_display(),
            ])
        tabla_sm = Table(
            filas_sm, colWidths=[26 * mm, 22 * mm, None, 14 * mm, 34 * mm],
            repeatRows=1,
        )
        tabla_sm.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), AZUL),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
            ("ALIGN", (3, 0), (3, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]))
        elementos.append(tabla_sm)
        if proyecto.solicitudes.count() > 40:
            elementos.append(Spacer(1, 2 * mm))
            elementos.append(Paragraph(
                f"Se muestran las 40 solicitudes más recientes de "
                f"{proyecto.solicitudes.count()} en total.", pie))
    else:
        elementos.append(Paragraph(
            "Todavía no se han generado solicitudes de material para este proyecto.", normal))

    # ---------------- Pie ----------------
    elementos.append(Spacer(1, 10 * mm))
    elementos.append(Paragraph(
        f"Documento generado el {timezone.localtime():%d-%m-%Y a las %H:%M} por el "
        f"Sistema de Gestión de Adquisiciones e Inventario — {settings.EMPRESA_RAZON_SOCIAL}.",
        pie,
    ))

    doc.build(elementos)
    return buffer.getvalue()
