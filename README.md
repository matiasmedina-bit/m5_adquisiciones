# Sistema de Gestión de Adquisiciones e Inventario — Constructora M5 SpA

**Grupo 23 — Ingeniería de Software.**
Estado del sistema a noviembre de 2026, después de la revisión contra el Documento 0
(`requerimientos_funcionales.md`, `casos_de_uso.md`, `requerimientos_no_funcionales.md`).

**Stack:** Python 3.11 · Django 5.2 · PostgreSQL 14+ · Bootstrap 5 + JavaScript sin
frameworks · reportlab (PDF) · openpyxl (Excel) · gunicorn + nginx en producción.

- Cumplimiento de cada RF/RNF: [`cumplimiento.md`](cumplimiento.md)
- Diferencias con el Documento 0 y redacción propuesta: [`cambios_para_documento.md`](cambios_para_documento.md)
- Historial de entregas: `LEEME.md` (entrega 1) y `LEEME_ENTREGA2/3/4.md`

---

## Índice

1. [Roles y lo que puede hacer cada uno](#1-roles-y-lo-que-puede-hacer-cada-uno)
2. [Flujo del sistema](#2-flujo-del-sistema)
3. [Estados](#3-estados)
4. [Instalación en desarrollo](#4-instalación-en-desarrollo)
5. [Variables del `.env`](#5-variables-del-env)
6. [Despliegue en el servidor de M5](#6-despliegue-en-el-servidor-de-m5)
7. [Usuarios de demostración](#7-usuarios-de-demostración)
8. [Pruebas](#8-pruebas)
9. [Estructura del proyecto](#9-estructura-del-proyecto)
10. [Problemas frecuentes](#10-problemas-frecuentes)

---

## 1. Roles y lo que puede hacer cada uno

Cinco roles. Cada permiso se revisa en el servidor (`usuarios/permisos.py`): entrar a
una pantalla no permitida por la URL directa devuelve **403**, y sin sesión lleva al
login. `usuarios/tests_permisos.py` lo verifica para cada rol.

| Rol (en el documento) | En el sistema | Qué hace |
|---|---|---|
| **Administrador / Administración** | `ADMIN` | Todo. En exclusiva: cuentas de usuario, parámetros del sistema y tipos de documento, **asignar o quitar jefes de una obra (RF-09), cambiar su estado (RF-10)** y eliminarla, catálogo maestro de materiales, desbloquear facturas (RF-38). |
| **Jefe de Proyecto** | `JEFE_PROYECTO` | **Registra obras** (queda asignado a la que crea) y **edita los datos y el itemizado sólo de sus obras** (RF-07, RF-08). Crea, emite y corrige las solicitudes de material de sus obras (RF-12 a RF-14). Aprueba o rechaza las OC de sus obras (RF-22). Reportes y trazabilidad de sus obras. **Nunca ve ni modifica obras a las que no está asignado.** |
| **Adquisiciones** | `ENCARGADO_ADQUISICIONES` | Proveedores y su catálogo (RF-01 a RF-06). Bandeja de SM emitidas, cotizaciones, aprobación de líneas y generación de OC (RF-16 a RF-21). Rechaza una SM que no puede atender. Corrige OC rechazadas (RF-23), gestiona el envío si el correo falló (RF-25) y el estado de recepción (RF-35). Compras anticipadas. Reportes y trazabilidad. |
| **Bodega** | `BODEGUERO` | Entradas (por OC o devolución de obra), salidas a obra, mermas, devoluciones a proveedor y préstamos de herramientas (RF-26 a RF-33). **Nunca ve precios.** |
| **Contabilidad** | `CONTABILIDAD` | Recepción de facturas con validación de monto, cuentas por pagar y exportación CSV (RF-37, RF-39, RF-40). Bitácora de auditoría. |

Bodega y Contabilidad pueden **leer** las SM emitidas y las OC (Bodega sin precios). El
inicio de sesión es con el **nombre de usuario o el correo institucional**, más la
contraseña (RF-47, decisión del grupo). Tras 5 intentos fallidos la cuenta queda
bloqueada 15 minutos (RNF-08); los fallos se cuentan por cuenta, así que se suman los
hechos con el usuario y con el correo, y el bloqueo cierra las dos formas de entrar. La
sesión se cierra sola tras 30 minutos sin actividad (RF-52).

---

## 2. Flujo del sistema

```
Administrador                Jefe de Proyecto            Adquisiciones              Bodega             Contabilidad
─────────────                ────────────────            ─────────────              ──────             ────────────
usuarios, proveedores*       obra + itemizado
asigna jefes, estado         (o el Administrador)
"En ejecución"
                             SM en Borrador ──emitir──►  bandeja (Emitida)
                                                         cotiza a varios proveedores
                                                         aprueba 1 línea por material
                             ◄── aviso "En cotización" ─ genera 1 OC por proveedor
                             aprueba / rechaza la OC ──► (si rechaza: corrige y reenvía)
                                       │ aprobada → PDF por correo al proveedor → "Enviada"
                                       ▼
                                                                                    recibe contra la OC
                                                                                    (parcial / total)
                             ◄── aviso con cantidades ── estado de recepción         stock al día
                                                                                                       factura contra OC
                                                                                                       (tolerancia, IVA incl.)
                                                                                                       cuentas por pagar
                             salida a obra imputada a una partida  ◄─────────────── Bodega
reportes y trazabilidad (Jefe de Proyecto sólo sus obras · Adquisiciones · Administrador)
```
\* Los proveedores los registra Adquisiciones (o el Administrador).

Paso a paso:

1. **Obra.** El Administrador o un Jefe de Proyecto registra la obra con su itemizado
   (partidas con cantidad presupuestada). Nace «En planificación». El Administrador
   asigna los jefes y la pasa a **«En ejecución»**: sólo así admite solicitudes.
2. **Solicitud de Materiales (SM).** El Jefe de Proyecto la arma en **Borrador**:
   materiales del catálogo maestro (o del catálogo de un proveedor), cantidad y
   **partida obligatoria**. Si una línea supera el saldo restante de la partida
   (presupuesto − lo ya pedido o ejecutado), el sistema alerta y exige justificación
   (RF-13). Puede adjuntar hasta 3 PDF/JPG de 5 MB. Al **emitirla** recibe su número
   `SM-000001` y queda **«Emitida»**.
3. **Cotización.** Adquisiciones la ve en la bandeja (más antigua primero), registra
   cotizaciones de distintos proveedores (valor unitario por material, despacho y días
   de entrega; el total se calcula solo) y aprueba la línea más conveniente de cada
   material. Con todas aprobadas la SM pasa a **«En cotización»**.
4. **Orden de Compra.** «Generar OC» crea un borrador por proveedor con folio
   automático, los datos de facturación de M5 y los del proveedor (no se genera si
   falta alguno). El Jefe de Proyecto de la obra la aprueba o la rechaza con motivo.
   Al aprobarla se envía el PDF por correo al proveedor y pasa a **«Enviada»**; si el
   proveedor no tiene correo o el envío falla, queda «Aprobada» y Adquisiciones
   reintenta o registra la entrega manual.
5. **Recepción.** Bodega registra la entrada contra la OC (sin superar lo pedido) y su
   ubicación; el stock se actualiza al instante y la OC pasa a «Recepción parcial» o
   «Recibida». La SM refleja el estado de cada OC y el Jefe de Proyecto recibe un aviso
   con las cantidades.
6. **Salida a obra.** Bodega despacha a la obra indicando jefe de proyecto, guía de
   despacho y **partida**: es lo que alimenta el «consumido» del reporte de desviación.
7. **Factura.** Contabilidad la vincula a una o más OC enviadas. Si el monto (IVA
   incluido) difiere del de las OC más que la tolerancia configurada, queda
   «Bloqueada» hasta que el Administrador la desbloquee. Si no, la OC queda marcada
   como facturada y la factura aparece en Cuentas por Pagar.
8. **Reportes y trazabilidad.** Consumo por proyecto, desviación presupuestaria
   (gráfico), mermas, compras por proveedor (Excel/PDF), y un buscador que reconstruye
   la cadena completa desde un número de SM, un folio de OC o el código de un material.

Cada cambio de estado de la SM se notifica al Jefe de Proyecto (campana de la barra
superior + correo). Los movimientos de bodega, emisiones, facturas, cuentas e
itemizado quedan en la bitácora con usuario, fecha y operación (Crear/Editar/Eliminar).

---

## 3. Estados

| Entidad | Estados |
|---|---|
| Proyecto | En planificación → En ejecución → Finalizado |
| Solicitud de Materiales | **Borrador** → Emitida → En cotización → OC generada → Entregada parcialmente → Entregada · Rechazada (por Adquisiciones; el JP la devuelve a Borrador y la reemite con el mismo número) |
| Orden de Compra | Borrador → Aprobada → Enviada → Recepción parcial → Recibida · Rechazada (vuelve a Borrador) · No recibida. Marca `facturada` independiente. |
| Factura | Registrada · Bloqueada (por diferencia de monto) |
| Préstamo de herramienta | Prestada → Devuelta / disponible en bodega |

---

## 4. Instalación en desarrollo

Requisitos: Python 3.11 o 3.12, PostgreSQL 14 o superior.

```powershell
git clone <URL_DEL_REPOSITORIO>
cd m5_adquisiciones
python -m venv venv
venv\Scripts\activate                  # Linux/macOS: source venv/bin/activate
pip install -r requirements.txt
```

Crear la base y el `.env`:

```sql
-- psql -U postgres
CREATE DATABASE m5_adquisiciones;
```
```powershell
copy .env.example .env                 # Linux/macOS: cp .env.example .env
# editar DB_PASSWORD y SECRET_KEY
```

Tablas, datos de prueba y servidor:

```bash
python manage.py migrate               # aplica todas las migraciones (incluidas las de datos)
python manage.py seed_demo             # opcional: usuarios, obra, proveedores y una cadena completa
python manage.py runserver             # http://127.0.0.1:8000/
```

> **Sobre las migraciones de esta revisión.** Algunas transforman datos existentes:
> las SM «Aprobada» y «Enviada» pasan a «Emitida», las obras «Suspendidas» a
> «En planificación», la bitácora se clasifica por operación, se cargan los seis tipos
> de documento del RF-51 y a las salidas a obra antiguas se les asigna la partida
> cuando no hay duda. No borran datos. Respalda la base antes de migrar una
> instalación con datos reales.

En desarrollo los correos se imprimen en la consola del `runserver`.

---

## 5. Variables del `.env`

| Variable | Para qué | Por defecto |
|---|---|---|
| `SECRET_KEY` | Clave de Django. **En producción, una larga y secreta.** | — |
| `DEBUG` | `True` en desarrollo, **`False` en producción** | `True` |
| `ALLOWED_HOSTS` | Nombres/IP con que se entra al sistema, separados por coma | `127.0.0.1,localhost` |
| `CSRF_TRUSTED_ORIGINS` | Opcional; si no se define se deduce de `ALLOWED_HOSTS` (http y https) | — |
| `DB_NAME` `DB_USER` `DB_PASSWORD` `DB_HOST` `DB_PORT` | Conexión a PostgreSQL | `m5_adquisiciones` / `postgres` / … / `127.0.0.1` / `5432` |
| `USAR_HTTPS` | **RNF-07.** `True` detrás de nginx con certificado: redirige http→https, cookies `Secure`, HSTS | `False` |
| `SECURE_HSTS_SECONDS` | Duración de HSTS cuando `USAR_HTTPS=True` | `31536000` |
| `ARCHIVOS_X_ACCEL` | `True` si nginx sirve los archivos subidos por `/protegido/` (descarga protegida) | `False` |
| `EMAIL_BACKEND` | `django.core.mail.backends.smtp.EmailBackend` para envío real | consola |
| `EMAIL_HOST` `EMAIL_PORT` | Servidor SMTP (Google Workspace: `smtp.gmail.com` 587 · Microsoft 365: `smtp.office365.com` 587) | — / `587` |
| `EMAIL_HOST_USER` `EMAIL_HOST_PASSWORD` | Cuenta con que se autentica el sistema | — |
| `EMAIL_USE_TLS` / `EMAIL_USE_SSL` | 587 → TLS; 465 → SSL (si se marcan las dos, manda SSL) | `True` / `False` |
| `EMAIL_TIMEOUT` | Segundos antes de dar por fallido un envío | `20` |
| `DEFAULT_FROM_EMAIL` | Remitente | `adquisiciones@m-5.cl` |
| `EMAIL_REPLY_TO` | Casilla donde llegan las respuestas de los proveedores | `EMPRESA_EMAIL` |
| `EMPRESA_RAZON_SOCIAL` `EMPRESA_RUT` `EMPRESA_GIRO` `EMPRESA_DIRECCION` `EMPRESA_TELEFONO` `EMPRESA_EMAIL` `EMPRESA_WEB` | Datos de facturación de M5 impresos en la OC (sin ellos no se genera la OC) | Constructora M5 SpA … |
| `EMPRESA_REPRESENTANTE_NOMBRE` `EMPRESA_REPRESENTANTE_RUT` | Quien autoriza la OC impresa | ver `config/settings.py` |
| `IVA_PORCENTAJE` | IVA de la OC y de la comparación con la factura | `19` |

Sin SMTP configurado **no salen** las OC a los proveedores (quedan «Aprobada»), ni los
enlaces de activación de cuenta y recuperación de contraseña. La tolerancia de
facturación, el stock mínimo por defecto, el umbral de tamaño de archivo y el folio de
la próxima OC se configuran en **Parámetros** dentro del sistema, no en el `.env`.

---

## 6. Despliegue en el servidor de M5

El servidor es una VM Ubuntu con la aplicación en `/opt/m5/app`, el entorno en
`/opt/m5/venv`, gunicorn como servicio (`systemctl … gunicorn`) y nginx delante.

**1. Subir el código y actualizar.**

```bash
cd /opt/m5/app
/opt/m5/venv/bin/pip install -r requirements.txt
/opt/m5/venv/bin/python manage.py migrate
/opt/m5/venv/bin/python manage.py collectstatic --noinput
/opt/m5/venv/bin/python manage.py check --deploy
```

**2. Extras del servidor: `despliegue/instalar.sh`** (una vez).

```bash
cd /tmp/m5_extras && bash instalar.sh
```

Deja `/opt/m5/set_ip.sh` (cambiar la IP en `ALLOWED_HOSTS` con un comando), el
**respaldo diario a las 00:00** de la base y de `media/` (`/etc/cron.d/m5-backup`,
30 días de retención en `/var/backups/m5`, RNF-10) y el bloque `EMAIL_*` comentado en
el `.env`. Para completar el correo: `despliegue/configurar_correo.sh`.

**3. HTTPS y descarga protegida: `despliegue/nginx-m5.conf`.**

```bash
sudo mkdir -p /etc/ssl/m5          # copiar aquí m5.crt y m5.key (certificado de TI de M5)
sudo cp despliegue/nginx-m5.conf /etc/nginx/sites-available/m5
sudo ln -sf /etc/nginx/sites-available/m5 /etc/nginx/sites-enabled/m5
sudo nginx -t && sudo systemctl reload nginx
```

El archivo redirige http→https, sirve `/static/` y deja los archivos subidos en una
ubicación interna (`/protegido/`) que nginx sólo entrega cuando Django lo autoriza.

**4. `.env` de producción** (como mínimo):

```ini
DEBUG=False
SECRET_KEY=<larga y secreta>
ALLOWED_HOSTS=m5.local,192.168.1.50
USAR_HTTPS=True
ARCHIVOS_X_ACCEL=True
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.office365.com
EMAIL_PORT=587
EMAIL_HOST_USER=sistema@m-5.cl
EMAIL_HOST_PASSWORD=<clave>
EMAIL_USE_TLS=True
DEFAULT_FROM_EMAIL=sistema@m-5.cl
EMAIL_REPLY_TO=adquisiciones@m-5.cl
```

**5. Reiniciar y dejar la instalación limpia.**

```bash
sudo systemctl restart gunicorn
/opt/m5/venv/bin/python manage.py preparar_produccion   # borra datos demo y crea el primer administrador
```

`preparar_produccion` es la **única** operación que borra físicamente datos (los de
demostración); en uso normal OC, proveedores, facturas y movimientos no se pueden borrar.

---

## 7. Usuarios de demostración

`seed_demo` crea una cuenta por rol, todas con la clave **`demo12345`**. Se entra con
el **usuario o con el correo** (cualquiera de las dos columnas):

| Usuario | Correo | Rol |
|---|---|---|
| `admin` | `admin@m5.cl` | Administrador |
| `jefe` | `jefe@m5.cl` | Jefe de Proyecto |
| `encargado` | `encargado@m5.cl` | Adquisiciones |
| `bodega` | `bodega@m5.cl` | Bodega |
| `contador` | `contador@m5.cl` | Contabilidad |

---

## 8. Pruebas

```bash
python manage.py test          # ≈ 550 pruebas, ≈ 8 minutos
python manage.py check
```

Pruebas destacadas:

- `usuarios/tests_permisos.py` — matriz rol × funcionalidad (403 por URL directa).
- `adquisiciones/tests_e2e.py` — la cadena completa, de proveedor a trazabilidad.
- `*/tests_rf.py`, `usuarios/tests_seguridad.py` — reglas de cada RF/RNF.

En Git Bash en Windows, si el comando no avanza, redirigir la entrada:
`python manage.py test --noinput < /dev/null`.

---

## 9. Estructura del proyecto

```
m5_adquisiciones/
├── config/          settings (HTTPS, correo, datos de M5), urls
├── usuarios/        cuentas y roles, login por correo y bloqueo (backends.py), permisos.py,
│                    notificaciones.py, integridad.py (sin borrado físico), descargas.py,
│                    parámetros del sistema, seed_demo y preparar_produccion
├── proveedores/     proveedores y su catálogo (carga desde Excel)
├── proyectos/       obras, itemizado, archivos y tipos de documento, ficha PDF
├── inventario/      catálogo maestro y bodega (movimientos, préstamos, stock)
├── solicitudes/     solicitudes de materiales, adjuntos, API del buscador
├── adquisiciones/   cotizaciones, órdenes de compra, PDF, trazabilidad
├── facturacion/     facturas, cuentas por pagar, CSV
├── reportes/        consumo, desviación, mermas, compras; exportación XLSX/PDF
├── auditoria/       bitácora (sólo lectura)
├── templates/  static/
├── despliegue/      instalar.sh, m5-backup, nginx-m5.conf, set_ip.sh, configurar_correo.sh
└── docs/
```

---

## 10. Problemas frecuentes

| Síntoma | Solución |
|---|---|
| «Usuario o correo, o contraseña incorrectos» con una cuenta que existe | Revisar la contraseña. El correo no distingue mayúsculas, pero el nombre de usuario sí (`jefe` ≠ `Jefe`). Una cuenta deshabilitada tampoco entra. |
| «Demasiados intentos fallidos…» | Esperar 15 minutos (RNF-08), o que el Administrador revise la cuenta. |
| El JP no ve una obra / recibe 403 | No está asignado a esa obra; el Administrador lo asigna (RF-09). |
| No aparece ninguna obra al crear una SM | La obra no está «En ejecución» o el JP no está asignado. |
| «No se puede generar la orden de compra: falta …» | Completar la dirección / datos del proveedor o los `EMPRESA_*` del `.env`. |
| La OC queda «Aprobada» y no «Enviada» | El proveedor no tiene correo o el SMTP falló: reintentar o registrar entrega manual. |
| Una factura correcta queda «Bloqueada» | El monto se compara con el total de la OC **con IVA**; revisar la tolerancia en Parámetros. |
| `FATAL: password authentication failed` | Revisar `DB_USER` / `DB_PASSWORD` en el `.env`. |
| Tras activar `USAR_HTTPS` el sitio entra en bucle de redirección | nginx no está enviando `X-Forwarded-Proto`; usar `despliegue/nginx-m5.conf`. |
