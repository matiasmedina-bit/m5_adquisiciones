# -*- coding: utf-8 -*-
"""
Incremento 4 — Diagrama de componentes, diagrama de despliegue y árbol de navegación.

Mismo estilo que diagramas.py (Incrementos 1 y 2) y el árbol del Incremento 3,
con un cuarto color para lo nuevo o modificado en el Incremento 4.
Uso:  python diagramas_inc4.py [carpeta_de_salida]   (requiere Graphviz: dot)
"""
import os
import subprocess
import sys

OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.abspath(__file__))
os.makedirs(OUT, exist_ok=True)

MOR, MOR_C = '#7030A0', '#EFE4F8'   # heredado del Incremento 1
AZU, AZU_C = '#1F3864', '#D9E2F3'   # heredado del Incremento 2
TEA, TEA_C = '#00838F', '#DFF3F4'   # heredado del Incremento 3
NAR, NAR_C = '#D9480F', '#FDE8DC'   # nuevo o modificado en el Incremento 4

COLORES = {1: (MOR, MOR_C), 2: (AZU, AZU_C), 3: (TEA, TEA_C), 4: (NAR, NAR_C)}


def render(nombre, dot):
    src = os.path.join(OUT, nombre + '.dot')
    png = os.path.join(OUT, nombre + '.png')
    with open(src, 'w', encoding='utf8') as f:
        f.write(dot)
    subprocess.run(['dot', '-Tpng', '-Gdpi=170', src, '-o', png], check=True)
    print('->', png, os.path.getsize(png) // 1024, 'KB')


LEYENDA = """
  leyenda [shape=none margin=0 label=<
      <TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0" CELLPADDING="5">
        <TR><TD BGCOLOR="%s"><FONT COLOR="white"><B>Heredado del Incremento 1</B></FONT></TD>
            <TD BGCOLOR="%s"><FONT COLOR="white"><B>Heredado del Incremento 2</B></FONT></TD>
            <TD BGCOLOR="%s"><FONT COLOR="white"><B>Heredado del Incremento 3</B></FONT></TD>
            <TD BGCOLOR="%s"><FONT COLOR="white"><B>Nuevo o modificado en el Incremento 4</B></FONT></TD></TR>
      </TABLE>>];
""" % (MOR, AZU, TEA, NAR)


def caja(id_, texto, inc, forma='box'):
    color, fondo = COLORES[inc]
    return ('%s [shape=%s style="filled,rounded" fillcolor="%s" color="%s" penwidth=1.6 '
            'fontcolor="#1A1A1A" fontsize=10 label="%s"];' % (id_, forma, fondo, color, texto))


CABECERA = ('  graph [fontname="DejaVu Sans" fontsize=11]; node [fontname="DejaVu Sans"]; '
            'edge [fontname="DejaVu Sans"];')

# ============================================================== 1. componentes
C = dict(
    v1=caja('v1', 'V_InicioSesion · V_PanelPrincipal\\nV_Proveedores · V_Proyectos\\nV_Solicitudes · V_Usuarios', 1),
    v2=caja('v2', 'V_Cotizaciones · V_OrdenesCompra\\nV_Bodega · V_Contabilidad', 2),
    v3=caja('v3', 'V_Reportes · V_Trazabilidad\\nV_Parametros · V_MiPerfil', 3),
    v4=caja('v4', 'V_Catalogo\\n(buscador con filtros y ficha del ítem)\\nV_Notificaciones', 4),

    c1=caja('c1', 'C_Usuarios · C_Proveedores\\nC_Proyectos · C_Solicitudes', 1),
    c2=caja('c2', 'C_Adquisiciones · C_OrdenCompra\\nC_Bodega · C_Facturacion', 2),
    c3=caja('c3', 'C_Reportes · C_Trazabilidad\\nC_Parametros', 3),
    c4=caja('c4', 'C_Catalogo\\nMaterialListView · MaterialCreateView\\nMaterialUpdateView (RF-58 a RF-60)', 4),
    mix=caja('mix', 'C_RolRequeridoMixin\\n(permisos por rol y por obra)', 4),
    srv=caja('srv', 'Servicios transversales\\nnotificaciones · descargas protegidas\\n'
                    'integridad (sin borrado físico)\\nacceso: usuario o correo + bloqueo', 4),

    m1=caja('m1', 'usuarios · proveedores · proyectos\\nsolicitudes · auditoria (bitácora)', 1),
    m2=caja('m2', 'adquisiciones · facturacion\\ninventario (movimientos y préstamos)', 2),
    m3=caja('m3', 'parámetros del sistema\\narchivos y tipos de documento', 3),
    m4=caja('m4', 'inventario.Material: catálogo maestro\\n(tipo, código interno, stock mínimo)\\n'
                  'notificación · intento de acceso', 4),

    db=caja('db', 'PostgreSQL 16', 1, 'cylinder'),
    cfg=caja('cfg', 'config.settings\\n(apps, seguridad y correo)', 2),
    pdf=caja('pdf', 'reportlab\\n(OC, ficha y reportes en PDF)', 2),
    xls=caja('xls', 'openpyxl\\n(reportes y catálogo en Excel)', 3),
    smtp=caja('smtp', 'SMTP\\n(OC, notificaciones y activación)', 4),
)

comp = """digraph componentes {
  rankdir=TB; bgcolor="white"; nodesep=0.3; ranksep=0.6; compound=true;
%(CAB)s
  subgraph cluster_v { label="Capa visual — plantillas V_"; style="rounded"; color="%(MOR)s"; fontcolor="%(MOR)s";
    %(v1)s
    %(v2)s
    %(v3)s
    %(v4)s
  }
  subgraph cluster_c { label="Capa de controladores — vistas y formularios C_"; style="rounded"; color="%(MOR)s"; fontcolor="%(MOR)s";
    %(mix)s
    %(c1)s
    %(c2)s
    %(c3)s
    %(c4)s
    %(srv)s
  }
  subgraph cluster_m { label="Capa de tablas — modelos del ORM"; style="rounded"; color="%(MOR)s"; fontcolor="%(MOR)s";
    %(m1)s
    %(m2)s
    %(m3)s
    %(m4)s
  }
  subgraph cluster_e { label="Infraestructura y dependencias externas"; style="rounded"; color="%(AZU)s"; fontcolor="%(AZU)s";
    %(cfg)s
    %(db)s
    %(pdf)s
    %(xls)s
    %(smtp)s
  }
  edge [color="#808080" penwidth=1.2];
  v1 -> c1; v2 -> c2; v3 -> c3; v4 -> c4;
  v2 -> mix [style=invis];
  mix -> c1 [style=dashed]; mix -> c2 [style=dashed]; mix -> c3 [style=dashed]; mix -> c4 [style=dashed];
  c1 -> m1; c2 -> m2; c3 -> m3; c4 -> m4;
  c1 -> m4 [style=dashed label="buscador de la SM" fontsize=8 fontcolor="%(NAR)s" color="%(NAR)s"];
  c2 -> srv [style=dashed]; c1 -> srv [style=dashed];
  m1 -> db; m2 -> db; m3 -> db; m4 -> db;
  cfg -> m2 [style=dashed];
  c2 -> pdf [style=dashed]; c3 -> xls [style=dashed]; srv -> smtp [style=dashed];
%(LEY)s
  db -> leyenda [style=invis];
}""" % dict(C, MOR=MOR, AZU=AZU, NAR=NAR, CAB=CABECERA, LEY=LEYENDA)
render('Diagrama_de_Componentes_Incremento4', comp)

# ============================================================== 2. despliegue
D = dict(
    pc=caja('pc', 'Equipos cliente\\nNavegador web (HTTPS)', 1),
    adm=caja('adm', 'Estación de administración\\nSSH y pgAdmin por túnel', 2),
    fw=caja('fw', 'Fortinet 30E\\nreserva DHCP / IP fija', 2),
    win=caja('win', 'Windows Server (host)', 1),
    nginx=caja('nginx', 'nginx\\nHTTPS 443 con certificado (80 redirige a 443)\\n'
                        'sirve /static/ y /protegido/ (X-Accel-Redirect)', 4),
    gunicorn=caja('gunicorn', 'gunicorn + systemd\\n3 workers, socket Unix', 2),
    django=caja('django', 'Aplicación Django 5.2 LTS\\n/opt/m5/app', 1),
    env=caja('env', 'archivo .env\\n(credenciales, hosts, HTTPS y correo)', 4),
    media=caja('media', 'media/\\narchivos subidos\\n(sólo con permiso de Django)', 4),
    pg=caja('pg', 'PostgreSQL 16\\nsólo 127.0.0.1', 1, 'cylinder'),
    cron=caja('cron', 'Respaldo diario 00:00\\n/etc/cron.d/m5-backup\\n/var/backups/m5 (30 días)', 4),
    smtp=caja('smtp', 'Servidor de correo SMTP\\n(Microsoft 365 / Google Workspace)', 4),
)

desp = """digraph despliegue {
  rankdir=TB; bgcolor="white"; nodesep=0.45; ranksep=0.65;
%(CAB)s
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
      %(media)s
      %(pg)s
      %(cron)s
    }
  }
  subgraph cluster_ext { label="Internet"; style="rounded,dashed"; color="%(NAR)s"; fontcolor="%(NAR)s";
    %(smtp)s
  }
  edge [color="#808080" penwidth=1.2];
  pc -> fw [label="HTTPS 443" fontsize=9];
  fw -> nginx [label="443 (80 redirige)" fontsize=9 color="%(NAR)s" fontcolor="%(NAR)s"];
  adm -> fw [label="SSH 22" fontsize=9 style=dashed];
  nginx -> gunicorn [label="socket Unix" fontsize=9]; gunicorn -> django;
  django -> pg [label="psycopg2" fontsize=9]; env -> django [style=dashed];
  django -> media [label="guarda y autoriza" fontsize=9];
  nginx -> media [label="X-Accel-Redirect" fontsize=9 style=dashed color="%(NAR)s" fontcolor="%(NAR)s"];
  cron -> pg [label="pg_dump" fontsize=9 style=dashed color="%(NAR)s" fontcolor="%(NAR)s"];
  cron -> media [label="copia" fontsize=9 style=dashed color="%(NAR)s" fontcolor="%(NAR)s"];
  django -> smtp [label="SMTP 587 (TLS)" fontsize=9 color="%(NAR)s" fontcolor="%(NAR)s"];
  win -> nginx [style=invis];
%(LEY)s
  pg -> leyenda [style=invis];
}""" % dict(D, MOR=MOR, AZU=AZU, NAR=NAR, CAB=CABECERA, LEY=LEYENDA)
render('Diagrama_de_Despliegue_Incremento4', desp)

# ============================================================== 3. árbol de navegación
def vista(id_, texto, inc):
    color, fondo = COLORES[inc]
    return ('%s [shape=box style="filled,rounded" fillcolor="%s" color="%s" penwidth=1.6 '
            'fontsize=10 label="%s"];' % (id_, fondo, color, texto))


nodos_arbol = [
    vista('login', 'V_InicioSesion\\nusuario o correo · bloqueo tras 5 intentos\\nCU-48', 4),
    vista('rec', 'Recuperar contraseña\\nCU-56', 3),
    vista('defc', 'Definir contraseña\\n(enlace de activación o recuperación)\\nCU-52, CU-56', 3),
    vista('panel', 'V_PanelPrincipal\\npanel e indicadores por rol', 1),

    vista('usu', 'Usuarios\\nCU-49, CU-50, CU-51', 1),
    vista('usu1', 'Alta con enlace de activación\\ny reenvío del enlace\\nCU-52', 3),

    vista('prov', 'Proveedores', 1),
    vista('prov1', 'Listado y ficha del proveedor\\nCU-01, CU-02', 1),
    vista('prov2', 'Catálogo de materiales del proveedor\\nCU-03, CU-04, CU-05', 2),
    vista('prov3', 'Inactivar proveedor\\nCU-06', 2),

    vista('proy', 'Proyectos', 1),
    vista('proy1', 'Detalle, jefe y estado de la obra\\nCU-09, CU-10, CU-11', 1),
    vista('proy2', 'Nuevo proyecto\\nCU-07 (Administrador o Jefe de Proyecto)', 4),
    vista('proy3', 'Itemizado presupuestado\\nCU-08 (Jefe de Proyecto: sus obras)', 4),
    vista('proy4', 'Documentos del proyecto\\nCU-54', 1),
    vista('proy5', 'Advertencia de tamaño, edición offline\\ny subida de versión\\nCU-57, CU-58, CU-59', 3),

    vista('sol', 'Solicitudes', 1),
    vista('sol1', 'Crear (borrador), emitir y consultar la SM\\nCU-12, CU-13, CU-14, CU-16', 4),
    vista('sol2', 'Notificaciones de estado\\nCU-15', 2),
    vista('sol3', 'Estado de recepción por OC\\nCU-37', 2),
    vista('sol4', 'Rechazar y corregir la SM\\n(Adquisiciones / Jefe de Proyecto)', 4),

    vista('adq', 'Adquisiciones', 2),
    vista('adq1', 'Bandeja de cotización\\nCU-17, CU-18, CU-19, CU-20', 2),
    vista('adq2', 'Órdenes de compra\\nCU-21 a CU-25, CU-36', 2),

    vista('bod', 'Bodega', 2),
    vista('bod1', 'Entradas, salidas y devoluciones\\nCU-26 a CU-29, CU-34\\n(la salida exige partida)', 4),
    vista('bod2', 'Préstamos de herramientas\\nCU-31, CU-32', 2),
    vista('bod3', 'Stock y mermas\\nCU-30, CU-33, CU-35', 2),
    vista('cat', 'Catálogo maestro\\nbuscar y filtrar por código, descripción,\\ntipo, categoría y ubicación\\nCU-63 (RF-60)', 4),
    vista('cat1', 'Nuevo / editar ítem (sólo Administrador)\\nmaterial o herramienta, código interno\\nautomático\\nCU-61, CU-62 (RF-58, RF-59)', 4),

    vista('fac', 'Facturación\\nCU-38, CU-39, CU-40', 2),
    vista('tra', 'Trazabilidad\\nCU-47', 3),
    vista('rep', 'Reportes\\npanel de informes', 3),
    vista('rep1', 'Consumo consolidado por proyecto\\nCU-42', 3),
    vista('rep2', 'Desviación presupuestaria\\nCU-43 (consumo desde salidas)', 4),
    vista('rep3', 'Mermas y pérdidas\\nCU-44', 3),
    vista('rep4', 'Historial de compras por proveedor\\nCU-45', 3),
    vista('rep5', 'Exportar a Excel o PDF\\nCU-46', 3),
    vista('par', 'Parámetros del sistema\\nCU-60', 3),
    vista('par1', 'Catálogo de tipos de documento\\nCU-60', 3),
    vista('aud', 'Auditoría\\nCU-53', 1),
    vista('perf', 'Mi perfil\\ndatos, foto y cambio de contraseña', 3),
    vista('noti', 'Notificaciones (campana)\\navisos de estado, rechazo y recepción', 4),
]
NODOS = '\n'.join('  ' + n for n in nodos_arbol)
arbol = """digraph arbol {
  rankdir=LR; bgcolor="white"; nodesep=0.18; ranksep=0.85;
%(CAB)s
%(NODOS)s
  edge [color="#808080" penwidth=1.2];
  login -> panel; login -> rec; rec -> defc; usu -> usu1;
  panel -> login [style=dashed color="%(TEA)s" fontcolor="%(TEA)s" fontsize=8 label="30 min sin actividad\\nCU-55" constraint=false];
  panel -> usu; panel -> prov; panel -> proy; panel -> sol; panel -> adq; panel -> bod;
  panel -> fac; panel -> tra; panel -> rep; panel -> par; panel -> aud; panel -> perf; panel -> noti;
  prov -> prov1; prov -> prov2; prov -> prov3;
  proy -> proy1; proy -> proy2; proy -> proy3; proy -> proy4; proy4 -> proy5;
  sol -> sol1; sol -> sol2; sol -> sol3; sol -> sol4;
  adq -> adq1; adq -> adq2;
  bod -> bod1; bod -> bod2; bod -> bod3; bod -> cat; cat -> cat1;
  sol1 -> cat [style=dashed color="%(NAR)s" fontcolor="%(NAR)s" fontsize=8 label="buscador de materiales" constraint=false];
  rep -> rep1; rep -> rep2; rep -> rep3; rep -> rep4; rep -> rep5;
  par -> par1;
%(LEY)s
  { rank=same; login; leyenda; }
}""" % dict(NODOS=NODOS, TEA=TEA, NAR=NAR, CAB=CABECERA, LEY=LEYENDA)
render('Arbol_de_Navegacion_Incremento4', arbol)
