# Sistema de Gestión de Adquisiciones e Inventario — Constructora M5 SpA

**Grupo 23 — Ingeniería de Software**
**Incremento 2 (Scrum++) — Bloque B: Sistema funcionando**

**Stack:** Django 5 · PostgreSQL · Bootstrap 5 · reportlab + pillow (PDF de la OC)

---

## Índice

1. [Alcance del proyecto](#1-alcance-del-proyecto)
2. [Novedades del Incremento 2](#2-novedades-del-incremento-2)
3. [Roles del sistema (RBAC)](#3-roles-del-sistema-rbac)
4. [Arquitectura](#4-arquitectura)
5. [Requisitos previos](#5-requisitos-previos)
6. [Instalación paso a paso](#6-instalación-paso-a-paso)
7. [Variables de entorno (`.env`)](#7-variables-de-entorno-env)
8. [Usuarios de prueba](#8-usuarios-de-prueba)
9. [Flujo de demostración sugerido](#9-flujo-de-demostración-sugerido)
10. [Pruebas unitarias](#10-pruebas-unitarias)
11. [Estructura del proyecto](#11-estructura-del-proyecto)
12. [Problemas frecuentes](#12-problemas-frecuentes)

---

## 1. Alcance del proyecto

El proyecto completo son **64 requerimientos funcionales (RF)**. Este entregable
acumula **48 de 64 RF → 75 %**.

| Incremento | RF | Total | % del proyecto |
|---|---|---|---|
| **Incremento 1** | RF-01–13, RF-15, RF-18, RF-50–52 | 16 | 25 % |
| **Incremento 2** | RF-05–07, RF-14, RF-16–17, RF-19–44 | 32 | 50 % |
| **Acumulado** | — | **48** | **75 %** |

> Toda la parte transaccional se almacena en una **base de datos relacional
> (PostgreSQL)**, según exige la rúbrica. Los archivos que suben los usuarios
> (adjuntos de solicitudes, PDF de órdenes de compra, archivo digital de facturas)
> se guardan en la carpeta `media/` y Django los sirve mientras `DEBUG=True`.

### Trazabilidad RF → módulo (Incremento 2)

| Módulo | RF | Qué implementa |
|---|---|---|
| **Proveedores** | RF-05, RF-06, RF-07 | Listado de materiales que suministra el proveedor: agregar material, marcarlo *no disponible* sin borrarlo, y editar código / unidad / descripción (guarda fecha de última modificación). |
| **Proyectos** | RF-14 | El **centro de costo** no puede repetirse en otro proyecto. |
| **Solicitudes de Materiales** | RF-16 | Alerta visual + campo **Justificación** obligatorio si la cantidad pedida supera el saldo de la partida del itemizado. |
| | RF-17 | Adjuntar hasta **3 archivos** PDF/JPG (máx. 5 MB c/u) a una solicitud. |
| **Adquisiciones — Cotizaciones** | RF-19 | Bandeja de entrada de Adquisiciones con las SM listas para cotizar, ordenadas por fecha. |
| | RF-20 | Registrar varias cotizaciones por SM (proveedor, valor unitario por material, costo de despacho, tiempo de entrega). Nacen en estado *Pendiente*. |
| | RF-21 | El **valor total** de cada cotización se calcula y muestra automáticamente: Σ(cantidad × valor unitario) + despacho. |
| | RF-22 | Aprobar, por cada material, la línea más conveniente; las demás quedan *Descartadas*. Cuando todas están resueltas, la SM pasa a *En cotización* y se habilita **Generar OC**. |
| **Adquisiciones — Órdenes de Compra** | RF-23 | Genera un **borrador de OC por cada proveedor** con las líneas aprobadas; autocompleta datos del proveedor y de M5; **correlativo automático e irrepetible** (`OC-000001`). |
| | RF-24 | El **Jefe de Proyecto** aprueba o rechaza el borrador (rechazo con motivo, notifica a Adquisiciones). |
| | RF-25 | Una OC **rechazada** se puede editar y vuelve a *Borrador* para nueva aprobación. |
| | RF-26 | Exportar la OC aprobada a **PDF** con el logotipo corporativo. |
| | RF-27 | Al aprobar, se **envía el PDF por correo** al proveedor y la OC pasa a *Enviada*. |
| **Inventario y Bodega** | RF-28 | Registrar entrada física de materiales, asociada a una **OC enviada** (recepción) o a un **proyecto** (retorno de sobrantes). Al rol Bodega se le ocultan los precios. |
| | RF-29 | La cantidad recibida no puede superar la cantidad de la OC. |
| | RF-30 | Registrar la **ubicación física** de cada material. |
| | RF-31 | Registrar **salida** de materiales/herramientas (material, cantidad, proyecto destino, jefe de proyecto, guía de despacho). |
| | RF-32 | El **stock disponible se actualiza en tiempo real** en cada entrada y salida. |
| | RF-33 | Gestión de **préstamos de herramientas** (activo fijo); notifica al rol Administración. |
| | RF-34 | Registrar la **devolución** de una herramienta prestada → vuelve a *Disponible en bodega*. |
| | RF-35 | Registrar **mermas / pérdidas** clasificadas por motivo (Daño / Robo); descuenta del stock. |
| | RF-36 | Registrar **devoluciones a proveedores** asociadas a una OC, con motivo. Se ocultan precios al rol Bodega. |
| | RF-37 | **Alerta visual de stock mínimo** cuando un material crítico llega a su umbral. |
| **Recepción** | RF-38 | Adquisiciones actualiza el estado de una OC enviada a *Recibida / Recepción parcial / No recibida*; notifica al Jefe de Proyecto con las cantidades recibidas. |
| | RF-39 | En el detalle de la SM se muestra el estado de recepción de **cada OC asociada por separado**. |
| **Facturación y Contabilidad** | RF-40 | Contabilidad recepciona una factura vinculándola a **una o más OC enviadas** (número, fecha de emisión y de vencimiento) y marca esas OC como *Facturada* (campo independiente de la recepción). |
| | RF-41 | Valida el monto total de la factura contra el de las OC; si supera la **tolerancia parametrizable**, la factura queda **Bloqueada**. |
| | RF-42 | El rol **Administración** desbloquea una factura bloqueada (con justificación). |
| | RF-43 | Vista **"Cuentas por Pagar"** ordenada por fecha de vencimiento, con alerta de vencidas / por vencer. |
| | RF-44 | Contabilidad **exporta el listado de facturas a CSV**. |

---

## 2. Novedades del Incremento 2

### Módulos nuevos

- **`adquisiciones/`** — cotizaciones y órdenes de compra (RF-19 a RF-27, RF-38, RF-39).
  Incluye `adquisiciones/pdf.py`, que arma el PDF de la OC con `reportlab`.
- **`facturacion/`** — recepción de facturas, control de monto, Cuentas por Pagar y
  exportación CSV (RF-40 a RF-44).

### Módulos existentes ampliados

- **`proveedores/`** — nuevo modelo `ProveedorMaterial` (listado de materiales del proveedor).
- **`proyectos/`** — campo `centro_costo` con validación de unicidad.
- **`solicitudes/`** — `SolicitudDetalle` gana partida del itemizado + justificación;
  nuevo modelo `SolicitudAdjunto`; el estado de la SM se amplía con
  *En cotización · OC generada · Recepción parcial · Entregada*.
- **`inventario/`** — nuevos modelos `MovimientoInventario` y `PrestamoHerramienta`;
  `Material` gana `stock_minimo` y `ubicacion`.
- **`usuarios/`** — se agrega el **quinto rol del RBAC: `CONTABILIDAD`** (RF-54).

### Configuración nueva (`config/settings.py`)

- `MEDIA_URL` / `MEDIA_ROOT` — archivos subidos por los usuarios.
- Bloque de **correo** (`EMAIL_*`); por defecto usa el backend de consola, así que
  los correos de la OC (RF-27) se imprimen en la terminal del `runserver`.
- Datos de facturación de M5 (`EMPRESA_*`) que se autocompletan en la OC (RF-23).
- `FACTURA_TOLERANCIA_PCT` — tolerancia de monto factura ↔ OC (RF-41).

### Interfaz

- El área interna (todo lo posterior al login) pasó del **blanco** a un **gris de
  marca** con un velo muy tenue de naranja y celeste, para suavizar la transición
  desde el login oscuro. Se controla con la variable `--m5-light` en
  `static/css/style.css`.
- Menú superior con las secciones nuevas: **Bodega**, **Adquisiciones** y
  **Facturación**, visibles según el rol.

### Dependencias nuevas

`reportlab==4.2.2` y `pillow==10.4.0` (PDF de la Orden de Compra con logo).

---

## 3. Roles del sistema (RBAC)

Cinco perfiles. `ADMIN` tiene acceso a todo. El resto ve solo sus secciones.

| Rol | Secciones | Acciones clave |
|---|---|---|
| **Administrador** (`admin`) | Todas | Gestión de cuentas y roles · desbloqueo de facturas (RF-42) |
| **Jefe de Proyecto** (`jefe`) | Proyectos · Solicitudes · Adquisiciones | Crea proyectos e itemizado · aprueba/rechaza solicitudes · aprueba/rechaza Órdenes de Compra (RF-24) |
| **Encargado de Adquisiciones** (`encargado`) | Proveedores · Proyectos · Solicitudes · Adquisiciones · Bodega | Proveedores y su catálogo · genera solicitudes · cotiza y genera OC · actualiza recepción |
| **Bodeguero** (`bodega`) | Bodega | Entradas, salidas, mermas, devoluciones y préstamos. **No ve precios** (RF-28, RF-36) |
| **Contabilidad** (`contador`) | Facturación | Recepciona facturas · Cuentas por Pagar · exporta CSV |

El control de acceso está en `usuarios/permisos.py` (`RolRequeridoMixin` para vistas
de clase y el decorador `@rol_requerido` para vistas de función).

---

## 4. Arquitectura

### Apps Django (una por módulo)

```
usuarios  →  proveedores  →  proyectos  →  inventario  →  solicitudes  →  adquisiciones  →  facturacion
```

### Modelo de datos principal

| Entidad | App | Relaciones |
|---|---|---|
| `Usuario` (rol) | usuarios | emite Solicitudes; aprueba OC; registra movimientos |
| `Proveedor` · `ProveedorMaterial` | proveedores | Proveedor 1─N ProveedorMaterial |
| `Proyecto` · `Itemizado` | proyectos | Proyecto 1─N Itemizado (partidas) |
| `Material` | inventario | catálogo; `stock_actual`, `stock_minimo`, `ubicacion` |
| `SolicitudMaterial` · `SolicitudDetalle` · `SolicitudAdjunto` | solicitudes | SM 1─N líneas; línea → Material y (opcional) Itemizado |
| `Cotizacion` · `CotizacionLinea` | adquisiciones | 1 cotización por (SM, proveedor); línea → SolicitudDetalle |
| `OrdenCompra` · `OrdenCompraLinea` | adquisiciones | OC → SM + Proveedor + Cotización |
| `MovimientoInventario` | inventario | tipo ENTRADA/SALIDA/MERMA/DEVOLUCION; ajusta el stock al guardar |
| `PrestamoHerramienta` | inventario | Herramienta prestada a un Jefe de Proyecto |
| `Factura` | facturacion | Factura N─M OrdenCompra |

### Flujo de estados

**Solicitud de Materiales:**
`Borrador → Enviada → Aprobada → En cotización → OC generada → Recepción parcial → Entregada`
(el Jefe puede *Rechazar* en "Enviada").

**Orden de Compra:**
`Borrador → Aprobada → Enviada → (Recepción parcial) → Recibida`
(*Rechazada* → editar → vuelve a *Borrador*; también puede quedar *No recibida*).
Campo `facturada` independiente del estado de recepción.

**Factura:** `Registrada` · `Bloqueada` (por diferencia de monto) → Administración desbloquea → `Registrada`.

---

## 5. Requisitos previos

- **Python 3.11 o 3.12** — verificar con `python --version`
- **PostgreSQL 14 o superior** — verificar con `psql --version`
- **Git** (opcional) — `git --version`
- **pip** y **venv** (vienen con Python)

> Si al escribir `python` en la terminal se abre la Microsoft Store, Python no está
> en el `PATH`. Instálalo desde [python.org](https://www.python.org/downloads/)
> marcando *"Add Python to PATH"*, o usa la ruta completa a tu `python.exe`.

---

## 6. Instalación paso a paso

> Para la guía detallada con capturas y solución de errores, ver
> **`docs/PASO_A_PASO.md`**.

### 6.1. Obtener el proyecto

```bash
git clone <URL_DEL_REPOSITORIO>
cd m5_adquisiciones
```

(o descomprimir el ZIP y entrar a la carpeta `m5_adquisiciones`).

### 6.2. Crear y activar el entorno virtual

**Windows (PowerShell):**
```powershell
python -m venv venv
venv\Scripts\activate
```
> Si sale *"la ejecución de scripts está deshabilitada"*:
> `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` y reintenta.

**Linux / macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
```

Al activarse, el prompt muestra `(venv)` al inicio. **Repite este paso cada vez que
abras una terminal nueva.**

### 6.3. Instalar dependencias

```bash
pip install -r requirements.txt
```

Instala: `Django 5.0.6`, `psycopg2-binary` (conector PostgreSQL), `python-dotenv`,
`reportlab` y `pillow` (PDF de la OC — RF-26).

### 6.4. Crear la base de datos en PostgreSQL

```bash
psql -U postgres
```
```sql
CREATE DATABASE m5_adquisiciones;
\q
```

### 6.5. Configurar `.env`

```powershell
copy .env.example .env      # Windows
# cp .env.example .env      # Linux / macOS
```

Edita `.env` y ajusta al menos la contraseña de PostgreSQL (`DB_PASSWORD`).
Ver la sección [7. Variables de entorno](#7-variables-de-entorno-env).

> El `.env` **no se sube a Git**. Cada integrante crea el suyo desde `.env.example`.

### 6.6. Crear las tablas

```bash
python manage.py makemigrations
python manage.py migrate
```

Las migraciones del Incremento 2 ya vienen escritas en el repo, así que
`makemigrations` debería decir **`No changes detected`**. Si generara algo,
`migrate` lo aplica igual.

### 6.7. Cargar datos de demostración

```bash
python manage.py seed_demo
```

Crea los 5 usuarios de prueba, proveedores con su catálogo, un proyecto con
itemizado y centro de costo, materiales con stock mínimo, solicitudes, y la
**cadena completa del Incremento 2**: cotizaciones → OC → recepción parcial →
factura, más una merma y un préstamo de ejemplo.

### 6.8. Levantar el servidor

```bash
python manage.py runserver
```

Abrir **http://127.0.0.1:8000/** e iniciar sesión (ver usuarios abajo).
Para apagarlo: `Ctrl + C`.

---

## 7. Variables de entorno (`.env`)

| Variable | Para qué | Valor por defecto |
|---|---|---|
| `SECRET_KEY` | Clave de Django | *(cambiar)* |
| `DEBUG` | Modo desarrollo | `True` |
| `ALLOWED_HOSTS` | Hosts permitidos | `127.0.0.1,localhost` |
| `DB_NAME` · `DB_USER` · `DB_PASSWORD` · `DB_HOST` · `DB_PORT` | Conexión PostgreSQL | `m5_adquisiciones` / `postgres` / `postgres` / `127.0.0.1` / `5432` |
| `EMAIL_BACKEND` | Backend de correo | consola (los correos se imprimen en el `runserver`) |
| `EMAIL_HOST` … `EMAIL_USE_TLS` | SMTP real (opcional) | vacío |
| `DEFAULT_FROM_EMAIL` | Remitente de las notificaciones | `adquisiciones@m5.cl` |
| `EMPRESA_RAZON_SOCIAL` · `EMPRESA_RUT` · `EMPRESA_GIRO` · `EMPRESA_DIRECCION` | Datos de M5 que se autocompletan en la OC (RF-23) | Constructora M5 SpA … |
| `FACTURA_TOLERANCIA_PCT` | % de diferencia permitido entre factura y OC antes de bloquear (RF-41) | `5` |

Para envío real de la OC por correo, descomenta el bloque SMTP de `.env.example`.

---

## 8. Usuarios de prueba

Todos con clave **`demo12345`** (los crea `seed_demo`).

| Usuario | Rol |
|---|---|
| `admin` | Administrador |
| `jefe` | Jefe de Proyecto |
| `encargado` | Encargado de Adquisiciones |
| `bodega` | Bodeguero |
| `contador` | Contabilidad |

Para un superusuario propio: `python manage.py createsuperuser`.

---

## 9. Flujo de demostración sugerido

### Base (Incremento 1)

1. **`encargado`** → registrar un proveedor con RUT chileno (valida dígito
   verificador y anti-duplicado). En su ficha, **agregar materiales al listado** y
   marcar uno *no disponible* → **RF-05 / RF-06 / RF-07**.
2. **`jefe`** → crear un proyecto con **centro de costo** (probar que no se
   repita → **RF-14**) y su **itemizado**.
3. **`encargado`** → crear una **solicitud**, agregar ítems vinculados a una
   partida. Si la cantidad supera el saldo del itemizado, el sistema exige
   **justificación** → **RF-16**. **Adjuntar** un PDF → **RF-17**. Enviar.
4. **`jefe`** → **aprobar** la solicitud.

### Adquisiciones (Incremento 2)

5. **`encargado`** → **Adquisiciones → Bandeja de cotización** (**RF-19**). Abrir la
   SM y **registrar 2 cotizaciones** de proveedores distintos (**RF-20**); el
   sistema muestra el **valor total** de cada una (**RF-21**).
6. **Aprobar** por cada material la línea más conveniente (**RF-22**) y pulsar
   **Generar Orden(es) de Compra** (**RF-23**): una OC por proveedor, con
   correlativo automático.
7. **`jefe`** → abrir la OC y **Aprobar** → se genera el **PDF** (**RF-26**) y se
   **envía por correo** al proveedor (**RF-27**, visible en la consola del
   `runserver`). Probar también **Rechazar** con motivo (**RF-24**) y, como
   `encargado`, **Editar líneas y reenviar** (**RF-25**).

### Bodega (Incremento 2)

8. **`bodega`** → **Bodega**: registrar una **entrada** asociada a la OC (valida que
   no supere lo pedido → **RF-29**, guarda ubicación → **RF-30**), una **salida a
   obra** (**RF-31**), una **merma** (**RF-35**) y un **préstamo de herramienta**
   (**RF-33**). El stock se actualiza al instante (**RF-32**) y se ve la **alerta de
   stock mínimo** (**RF-37**). Observar que **no aparecen precios**.
9. **`encargado`** → en la OC, **actualizar el estado de recepción** (**RF-38**); el
   estado por OC se ve en el detalle de la SM (**RF-39**).

### Facturación (Incremento 2)

10. **`contador`** → **Facturación → Recepcionar factura** vinculada a la OC
    (**RF-40**). Con monto dentro de la tolerancia queda *Registrada* y marca la OC
    como *Facturada*; con un monto muy distinto queda **Bloqueada** (**RF-41**).
11. **`admin`** → **desbloquear** la factura (**RF-42**). Ver **Cuentas por Pagar**
    (**RF-43**) y **Exportar CSV** (**RF-44**).
12. Entrar con **`bodega`** a una sección no permitida → el sistema **bloquea por
    rol** (RBAC).

---

## 10. Pruebas unitarias

```bash
python manage.py test
```

Con detalle (para la evidencia del informe):

```bash
python manage.py test --verbosity=2
```

Actualmente son **66 pruebas** (Incremento 1 + Incremento 2). Cada módulo incluye
además un test que comprueba que **todas sus plantillas se renderizan sin error**.
La evidencia (captura de `... OK`) se pega en `docs/INFORME_PRUEBAS.md`, que ya trae
la trazabilidad prueba ↔ RF.

Para correr solo un módulo:

```bash
python manage.py test adquisiciones --verbosity=2
```

---

## 11. Estructura del proyecto

```
m5_adquisiciones/
├── config/              # settings, urls raíz, wsgi/asgi
├── usuarios/            # autenticación, cuentas y roles (RBAC · 5 perfiles)
│   ├── validators.py    # RUT chileno (módulo 11)
│   ├── permisos.py      # mixin + decorador de control de acceso por rol
│   └── management/commands/seed_demo.py     # carga de datos demo
├── proveedores/         # RF-01–08 · proveedores + listado de materiales (RF-05/06/07)
├── proyectos/           # RF-09–14 · proyectos, itemizado, centro de costo (RF-14)
├── inventario/          # catálogo + Bodega: movimientos, préstamos, stock mínimo (RF-28–37)
├── solicitudes/         # solicitudes de material + justificación (RF-16) y adjuntos (RF-17)
├── adquisiciones/       # RF-19–27, 38, 39 · cotizaciones y órdenes de compra
│   └── pdf.py           # PDF de la OC con logo (reportlab)
├── facturacion/         # RF-40–44 · facturas, cuentas por pagar, export CSV
├── templates/           # plantillas HTML (Bootstrap 5)
├── static/css/style.css # tema visual (variables de marca)
├── media/               # archivos subidos — NO se versiona
├── docs/                # GUIA_GIT · PASO_A_PASO · INFORME_PRUEBAS
├── requirements.txt
├── .env.example
└── manage.py
```

---

## 12. Problemas frecuentes

| Síntoma | Solución |
|---|---|
| Al escribir `python` se abre la Microsoft Store | Python no está en el `PATH`. Instálalo desde python.org con *"Add to PATH"*, o usa la ruta completa a `python.exe` / el `venv\Scripts\python.exe`. |
| `psycopg2` no instala en Windows | Usa Python 3.11 o 3.12; `psycopg2-binary` ya trae los binarios. |
| `FATAL: password authentication failed for user "postgres"` | Revisa `DB_USER` / `DB_PASSWORD` en `.env`. |
| `could not connect to server` / `Connection refused` | PostgreSQL no está corriendo o usa otro puerto; ajusta `DB_PORT` en `.env`. |
| `database "m5_adquisiciones" does not exist` | Repite el paso 6.4 (crear la base). |
| `No module named 'dotenv'` / `'django'` / `'reportlab'` | Falta activar el `venv` o `pip install -r requirements.txt`. |
| El PDF de la OC da error 503 | Falta `reportlab`. Ejecuta `pip install -r requirements.txt`. |
| El navegador no carga | Confirma que el `runserver` sigue activo y usa `http://127.0.0.1:8000/`. |
| `makemigrations` pide migraciones nuevas | No debería; si pasa, ejecútalo y luego `migrate` — se aplica igual. |
