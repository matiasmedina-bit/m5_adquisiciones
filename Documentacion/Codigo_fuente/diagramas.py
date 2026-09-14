# -*- coding: utf-8 -*-
"""Modelo físico, componentes, despliegue y árbol de navegación, con el código morado/azul."""
import os, subprocess

OUT = '/home/claude/final/img'
os.makedirs(OUT, exist_ok=True)

MOR, MOR_C = '#7030A0', '#EFE4F8'
AZU, AZU_C = '#1F3864', '#D9E2F3'
GRI, GRI_C = '#A6A6A6', '#F2F2F2'


def render(nombre, dot, extra=()):
    src = os.path.join(OUT, nombre + '.dot')
    png = os.path.join(OUT, nombre + '.png')
    open(src, 'w', encoding='utf8').write(dot)
    subprocess.run(['dot', '-Tpng', '-Gdpi=170', *extra, src, '-o', png], check=True)
    print('->', png, os.path.getsize(png) // 1024, 'KB')


LEYENDA = ("""
  leyenda [shape=none margin=0 label=<
      <TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0" CELLPADDING="5">
        <TR><TD BGCOLOR="%s"><FONT COLOR="white"><B>Heredado del Incremento 1</B></FONT></TD>
            <TD BGCOLOR="%s"><FONT COLOR="white"><B>Nuevo o modificado en el Incremento 2</B></FONT></TD>
            <TD BGCOLOR="%s"><FONT COLOR="#595959"><B>Comprometido para el Incremento 3</B></FONT></TD></TR>
      </TABLE>>];
""" % (MOR, AZU, GRI_C))


# ---------------------------------------------------------------- 1. modelo físico
def tabla(nombre, campos, color, fondo, nota=None):
    filas = ''
    for c in campos:
        marca = ''
        if c.startswith('+'):
            c = c[1:]; marca = ' <FONT COLOR="%s"><B>nuevo</B></FONT>' % AZU
        filas += ('<TR><TD ALIGN="LEFT" BGCOLOR="white"><FONT POINT-SIZE="9">%s%s</FONT></TD></TR>'
                  % (c, marca))
    pie = ('<TR><TD ALIGN="LEFT" BGCOLOR="%s"><FONT POINT-SIZE="8"><I>%s</I></FONT></TD></TR>'
           % (fondo, nota)) if nota else ''
    return ('%s [shape=none margin=0 label=<<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0" '
            'CELLPADDING="3"><TR><TD BGCOLOR="%s"><FONT COLOR="white" POINT-SIZE="10"><B>%s</B>'
            '</FONT></TD></TR>%s%s</TABLE>>];' % (nombre, color, nombre, filas, pie))


TABLAS = [
 # heredadas sin cambios
 ('usuarios_perfiljefeproyecto', ['PK id', 'FK usuario_id', 'telefono'], MOR, MOR_C, None),
 ('usuarios_perfilencargadoadquisiciones', ['PK id', 'FK usuario_id', 'telefono'], MOR, MOR_C, None),
 ('usuarios_perfilbodeguero', ['PK id', 'FK usuario_id', 'turno'], MOR, MOR_C, None),
 ('proveedores_proveedor', ['PK id', 'UQ rut', 'razon_social', 'giro', 'direccion',
                            'correo', 'telefono', 'condicion_pago', 'activo'], MOR, MOR_C, None),
 ('proyectos_proyecto_responsables', ['PK id', 'FK proyecto_id', 'FK usuario_id'], MOR, MOR_C, None),
 ('solicitudes_solicituddetalle', ['PK id', 'FK solicitud_id', 'FK material_id', 'FK itemizado_id',
                                   'cantidad', 'unidad', 'justificacion'], MOR, MOR_C, None),
 # heredadas modificadas
 ('usuarios_usuario', ['PK id', 'UQ username', 'email', 'password', 'is_active',
                       '+rol: valor CONTABILIDAD'], AZU, AZU_C,
  'Modificada: el rol CONTABILIDAD pasa a tener funcionalidad (CU-38 a CU-40)'),
 ('proyectos_proyecto', ['PK id', 'nombre', 'mandante', '+UQ centro_costo', 'fecha_inicio',
                         'fecha_termino', 'presupuesto', 'estado'], AZU, AZU_C,
  'Modificada: CU-07 exige centro de costo único'),
 ('proyectos_itemizado', ['PK id', 'FK proyecto_id', 'codigo_partida', 'descripcion',
                          'cantidad_presupuestada', 'unidad', '+cant_ejecutada'], AZU, AZU_C,
  'Modificada: las salidas de bodega descuentan contra la partida (CU-08, CU-29)'),
 ('inventario_material', ['PK id', 'nombre', 'tipo', 'unidad', 'stock_actual',
                          'precio_referencia', '+stock_minimo'], AZU, AZU_C,
  'Modificada: CU-35 alerta bajo el stock mínimo'),
 ('solicitudes_solicitudmaterial', ['PK id', 'UQ correlativo', 'FK proyecto_id', 'FK emisor_id',
                                    '+estado: dominio ampliado', 'fecha', '+fecha_cambio_estado'],
  AZU, AZU_C, 'Modificada: CU-15 notifica los cambios de estado'),
 # nuevas
 ('adquisiciones_cotizacion', ['PK id', 'FK solicitud_id', 'FK proveedor_id', 'costo_despacho',
                               'dias_entrega', 'valor_total', 'estado', 'fecha'], AZU, AZU_C, 'Nueva'),
 ('adquisiciones_cotizacionlinea', ['PK id', 'FK cotizacion_id', 'FK detalle_id',
                                    'valor_unitario', 'subtotal', 'estado'], AZU, AZU_C, 'Nueva'),
 ('adquisiciones_ordencompra', ['PK id', 'UQ correlativo', 'FK solicitud_id', 'FK proveedor_id',
                                'estado', 'total', 'motivo_rechazo', 'fecha_envio',
                                'estado_recepcion', 'facturada'], AZU, AZU_C, 'Nueva'),
 ('adquisiciones_ordencompradetalle', ['PK id', 'FK orden_id', 'FK material_id', 'cantidad',
                                       'valor_unitario', 'subtotal', 'cantidad_recibida'],
  AZU, AZU_C, 'Nueva'),
 ('inventario_movimientobodega', ['PK id', 'FK material_id', 'tipo', 'cantidad',
                                  'FK orden_compra_id', 'FK proyecto_id', 'ubicacion',
                                  'guia_despacho', 'motivo', 'FK usuario_id', 'fecha'],
  AZU, AZU_C, 'Nueva'),
 ('inventario_prestamoherramienta', ['PK id', 'FK material_id', 'FK jefe_proyecto_id',
                                     'FK proyecto_id', 'fecha_salida', 'fecha_devolucion_esperada',
                                     'fecha_devolucion_real', 'estado'], AZU, AZU_C, 'Nueva'),
 ('facturacion_factura', ['PK id', 'numero', 'FK proveedor_id', 'fecha_emision',
                          'fecha_vencimiento', 'monto_total', 'estado',
                          'FK autorizada_por_id'], AZU, AZU_C, 'Nueva'),
 ('facturacion_factura_ordenes', ['PK id', 'FK factura_id', 'FK orden_compra_id'], AZU, AZU_C, 'Nueva'),
 ('config_parametrosistema', ['PK id', 'UQ clave', 'valor', 'descripcion'], AZU, AZU_C, 'Nueva'),
]

ARISTAS = [
 ('usuarios_perfiljefeproyecto', 'usuarios_usuario'),
 ('usuarios_perfilencargadoadquisiciones', 'usuarios_usuario'),
 ('usuarios_perfilbodeguero', 'usuarios_usuario'),
 ('proyectos_proyecto_responsables', 'proyectos_proyecto'),
 ('proyectos_proyecto_responsables', 'usuarios_usuario'),
 ('proyectos_itemizado', 'proyectos_proyecto'),
 ('solicitudes_solicitudmaterial', 'proyectos_proyecto'),
 ('solicitudes_solicitudmaterial', 'usuarios_usuario'),
 ('solicitudes_solicituddetalle', 'solicitudes_solicitudmaterial'),
 ('solicitudes_solicituddetalle', 'inventario_material'),
 ('solicitudes_solicituddetalle', 'proyectos_itemizado'),
 ('adquisiciones_cotizacion', 'solicitudes_solicitudmaterial'),
 ('adquisiciones_cotizacion', 'proveedores_proveedor'),
 ('adquisiciones_cotizacionlinea', 'adquisiciones_cotizacion'),
 ('adquisiciones_cotizacionlinea', 'solicitudes_solicituddetalle'),
 ('adquisiciones_ordencompra', 'solicitudes_solicitudmaterial'),
 ('adquisiciones_ordencompra', 'proveedores_proveedor'),
 ('adquisiciones_ordencompradetalle', 'adquisiciones_ordencompra'),
 ('adquisiciones_ordencompradetalle', 'inventario_material'),
 ('inventario_movimientobodega', 'inventario_material'),
 ('inventario_movimientobodega', 'adquisiciones_ordencompra'),
 ('inventario_movimientobodega', 'proyectos_proyecto'),
 ('inventario_prestamoherramienta', 'inventario_material'),
 ('inventario_prestamoherramienta', 'proyectos_proyecto'),
 ('facturacion_factura', 'proveedores_proveedor'),
 ('facturacion_factura_ordenes', 'facturacion_factura'),
 ('facturacion_factura_ordenes', 'adquisiciones_ordencompra'),
]

nodos = '\n  '.join(tabla(*t) for t in TABLAS)
aristas = '\n  '.join('%s -> %s [arrowhead=crow arrowtail=none dir=both];' % a for a in ARISTAS)
MOD = """digraph modelo {
  rankdir=LR; splines=spline; nodesep=0.35; ranksep=1.1; bgcolor="white";
  graph [fontname="DejaVu Sans"]; node [fontname="DejaVu Sans"]; edge [color="#808080" penwidth=1.0];
  %(nodos)s
  %(aristas)s
%(LEY)s
  config_parametrosistema -> leyenda [style=invis];
}""" % dict(nodos=nodos, aristas=aristas, LEY=LEYENDA)
render('Fig_3.1_Modelo_fisico', MOD)


# ---------------------------------------------------------------- 2. componentes
def caja(id_, texto, color, fondo, forma='box'):
    return ('%s [shape=%s style="filled,rounded" fillcolor="%s" color="%s" penwidth=1.6 '
            'fontcolor="#1A1A1A" fontsize=10 label="%s"];' % (id_, forma, fondo, color, texto))


C = {}
C['v_login'] = caja('v_login', 'V_InicioSesion\\nV_PanelPrincipal', MOR, MOR_C)
C['v_base'] = caja('v_base', 'V_Proveedores · V_Proyectos\\nV_Solicitudes · V_Usuarios', MOR, MOR_C)
C['v_new'] = caja('v_new', 'V_Cotizaciones · V_OrdenesCompra\\nV_Bodega · V_Contabilidad', AZU, AZU_C)
C['c_base'] = caja('c_base', 'C_Usuarios · C_Proveedores\\nC_Proyectos · C_Solicitudes', MOR, MOR_C)
C['c_mixin'] = caja('c_mixin', 'C_RolRequeridoMixin\\n(ampliado a Bodega y Contabilidad)', AZU, AZU_C)
C['c_new'] = caja('c_new', 'C_Adquisiciones · C_OrdenCompra\\nC_Bodega · C_Facturacion', AZU, AZU_C)
C['m_base'] = caja('m_base', 'usuarios · proveedores\\nproyectos · solicitudes', MOR, MOR_C)
C['m_new'] = caja('m_new', 'adquisiciones · facturacion\\ninventario (movimientos y préstamos)', AZU, AZU_C)
C['cfg'] = caja('cfg', 'config.settings\\n(registra las apps nuevas)', AZU, AZU_C)
C['db'] = caja('db', 'PostgreSQL 16', MOR, MOR_C, 'cylinder')
C['pdf'] = caja('pdf', 'reportlab\\n(OC en PDF, CU-24)', AZU, AZU_C)
C['smtp'] = caja('smtp', 'SMTP\\n(envío de la OC, CU-25)', AZU, AZU_C)

comp = """digraph componentes {
  rankdir=TB; bgcolor="white"; nodesep=0.3; ranksep=0.55; compound=true;
  graph [fontname="DejaVu Sans" fontsize=11]; node [fontname="DejaVu Sans"];
  subgraph cluster_v { label="Capa visual — plantillas V_"; style="rounded"; color="%(MOR)s"; fontcolor="%(MOR)s";
    %(v_login)s
    %(v_base)s
    %(v_new)s
  }
  subgraph cluster_c { label="Capa de controladores — vistas y formularios C_"; style="rounded"; color="%(MOR)s"; fontcolor="%(MOR)s";
    %(c_base)s
    %(c_mixin)s
    %(c_new)s
  }
  subgraph cluster_m { label="Capa de tablas — modelos del ORM"; style="rounded"; color="%(MOR)s"; fontcolor="%(MOR)s";
    %(m_base)s
    %(m_new)s
  }
  subgraph cluster_e { label="Infraestructura y dependencias externas"; style="rounded"; color="%(AZU)s"; fontcolor="%(AZU)s";
    %(cfg)s
    %(db)s
    %(pdf)s
    %(smtp)s
  }
  edge [color="#808080" penwidth=1.2];
  v_login -> c_base; v_base -> c_base; v_new -> c_new;
  c_base -> m_base; c_new -> m_new; c_mixin -> c_new [style=dashed];
  c_mixin -> c_base [style=dashed];
  m_base -> db; m_new -> db; cfg -> m_new [style=dashed];
  c_new -> pdf [style=dashed]; c_new -> smtp [style=dashed];
%(LEY)s
  db -> leyenda [style=invis];
}""" % dict(C, MOR=MOR, AZU=AZU, LEY=LEYENDA)
render('Fig_3.2_Componentes', comp)


# ---------------------------------------------------------------- 3. despliegue
D = {}
D['pc'] = caja('pc', 'Equipos cliente\\nNavegador web (HTTPS)', MOR, MOR_C)
D['adm'] = caja('adm', 'Estación de administración\\nSSH y pgAdmin por túnel', AZU, AZU_C)
D['fw'] = caja('fw', 'Fortinet 30E\\nreserva DHCP / IP fija', AZU, AZU_C)
D['win'] = caja('win', 'Windows Server (host)', MOR, MOR_C)
D['nginx'] = caja('nginx', 'nginx\\nsirve /static/ y /media/', AZU, AZU_C)
D['gunicorn'] = caja('gunicorn', 'gunicorn + systemd\\n3 workers, socket Unix', AZU, AZU_C)
D['django'] = caja('django', 'Aplicación Django 5.2 LTS\\n/opt/m5/app', MOR, MOR_C)
D['env'] = caja('env', 'archivo .env\\n(credenciales y hosts)', AZU, AZU_C)
D['pg'] = caja('pg', 'PostgreSQL 16\\nsólo 127.0.0.1', MOR, MOR_C, 'cylinder')

desp = """digraph despliegue {
  rankdir=TB; bgcolor="white"; nodesep=0.4; ranksep=0.6;
  graph [fontname="DejaVu Sans" fontsize=11]; node [fontname="DejaVu Sans"];
  subgraph cluster_cli { label="Red local de Constructora M5 SpA"; style="rounded"; color="%(MOR)s"; fontcolor="%(MOR)s";
    %(pc)s
    %(adm)s
    %(fw)s
  }
  subgraph cluster_srv { label="Servidor HP ProLiant DL20 Gen9"; style="rounded"; color="%(MOR)s"; fontcolor="%(MOR)s";
    %(win)s
    subgraph cluster_vm { label="VirtualBox — VM m5-app (Ubuntu Server 24.04 LTS)"; style="rounded"; color="%(AZU)s"; fontcolor="%(AZU)s";
      %(nginx)s
      %(gunicorn)s
      %(django)s
      %(env)s
      %(pg)s
    }
  }
  edge [color="#808080" penwidth=1.2];
  pc -> fw [label="HTTPS" fontsize=9]; fw -> nginx [label="puerto 80" fontsize=9];
  adm -> fw [label="SSH 22" fontsize=9 style=dashed];
  nginx -> gunicorn [label="socket Unix" fontsize=9]; gunicorn -> django;
  django -> pg [label="psycopg2" fontsize=9]; env -> django [style=dashed];
  win -> nginx [style=invis];
%(LEY)s
  pg -> leyenda [style=invis];
}""" % dict(D, MOR=MOR, AZU=AZU, LEY=LEYENDA)
render('Fig_3.3_Despliegue', desp)


# ---------------------------------------------------------------- 4. árbol de navegación
def vista(id_, texto, tipo='mor'):
    color, fondo, extra = ((MOR, MOR_C, '') if tipo == 'mor' else
                           (AZU, AZU_C, '') if tipo == 'azu' else
                           (GRI, GRI_C, 'style="filled,rounded,dashed" fontcolor="#595959" '))
    est = extra or 'style="filled,rounded" '
    return ('%s [shape=box %sfillcolor="%s" color="%s" penwidth=1.6 fontsize=10 label="%s"];'
            % (id_, est, fondo, color, texto))


nodos_arbol = [
 vista('login', 'V_InicioSesion', 'mor'),
 vista('panel', 'V_PanelPrincipal\\npanel e indicadores por rol', 'mor'),
 vista('usu', 'Usuarios\\nCU-49, CU-50, CU-51', 'mor'),
 vista('prov', 'Proveedores', 'mor'),
 vista('prov1', 'Listado y ficha del proveedor\\nCU-01, CU-02', 'mor'),
 vista('prov2', 'Catálogo de materiales del proveedor\\nCU-03, CU-04, CU-05', 'azu'),
 vista('prov3', 'Inactivar proveedor\\nCU-06', 'azu'),
 vista('proy', 'Proyectos', 'mor'),
 vista('proy1', 'Detalle, jefe y estado de la obra\\nCU-09, CU-10, CU-11', 'mor'),
 vista('proy2', 'Nuevo proyecto\\nCU-07', 'azu'),
 vista('proy3', 'Itemizado presupuestado\\nCU-08', 'azu'),
 vista('sol', 'Solicitudes', 'mor'),
 vista('sol1', 'Crear y consultar la SM\\nCU-12, CU-13, CU-14, CU-16', 'mor'),
 vista('sol2', 'Notificaciones de estado\\nCU-15', 'azu'),
 vista('sol3', 'Estado de recepción por OC\\nCU-37', 'azu'),
 vista('adq', 'Adquisiciones', 'azu'),
 vista('adq1', 'Bandeja de cotización\\nCU-17, CU-18, CU-19, CU-20', 'azu'),
 vista('adq2', 'Órdenes de compra\\nCU-21 a CU-25, CU-36', 'azu'),
 vista('bod', 'Bodega', 'azu'),
 vista('bod1', 'Entradas, salidas y devoluciones\\nCU-26 a CU-29, CU-34', 'azu'),
 vista('bod2', 'Préstamos de herramientas\\nCU-31, CU-32', 'azu'),
 vista('bod3', 'Catálogo, stock y mermas\\nCU-30, CU-33, CU-35', 'azu'),
 vista('fac', 'Facturación\\nCU-38, CU-39, CU-40', 'azu'),
 vista('tra', 'Trazabilidad\\nCU-47', 'mor'),
 vista('aud', 'Auditoría\\nCU-53', 'mor'),
 vista('par', 'Parámetros del sistema\\n(Incremento 3)', 'gri'),
]
NODOS = chr(10).join('  ' + n for n in nodos_arbol)
arbol = """digraph arbol {
  rankdir=LR; bgcolor="white"; nodesep=0.20; ranksep=0.85;
  graph [fontname="DejaVu Sans" fontsize=11]; node [fontname="DejaVu Sans"];
%(NODOS)s
  edge [color="#808080" penwidth=1.2];
  login -> panel;
  panel -> usu; panel -> prov; panel -> proy; panel -> sol;
  panel -> adq; panel -> bod; panel -> fac; panel -> tra; panel -> aud;
  panel -> par [style=dashed color="%(GRI)s"];
  prov -> prov1; prov -> prov2; prov -> prov3;
  proy -> proy1; proy -> proy2; proy -> proy3;
  sol -> sol1; sol -> sol2; sol -> sol3;
  adq -> adq1; adq -> adq2;
  bod -> bod1; bod -> bod2; bod -> bod3;
%(LEY)s
  { rank=same; login; leyenda; }
}""" % dict(NODOS=NODOS, GRI=GRI, LEY=LEYENDA)
render('Fig_4.1_Arbol_navegacion', arbol)
