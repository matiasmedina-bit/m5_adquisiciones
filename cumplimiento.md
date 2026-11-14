# Cumplimiento de requerimientos — Sistema de Adquisiciones M5

**Estado final (Fase 2 + cambios finales del grupo), 14-11-2026 — rama `revision-requerimientos`.**
La auditoría inicial (antes de las correcciones) quedó en el commit `05412bc`
(`git show 05412bc:cumplimiento.md`).

Fuentes de verdad: `requerimientos_funcionales.md`, `casos_de_uso.md`,
`requerimientos_no_funcionales.md`. Lo que el sistema hace distinto de lo
escrito, y por qué, está en `cambios_para_documento.md`.

## Resumen

| | Inicial ✅ / 🟡 / ❌ | **Final ✅ / 🟡 / ❌** |
|---|---|---|
| RF (60) | 26 / 33 / 1 | **60 / 0 / 0** |
| RNF (14) | 6 / 7 / 1 | **12 / 2 / 0** |

- `manage.py check`: sin errores. `makemigrations --check`: sin cambios pendientes.
- Tests: **557 tests OK** (antes 396). La línea «OSError: SMTP caído» del log es la
  falla de correo simulada a propósito en un test de CU-25. Nuevos: matriz de permisos
  (`usuarios/tests_permisos.py`), flujo de punta a punta (`adquisiciones/tests_e2e.py`),
  reglas por módulo (`*/tests_rf.py`, `usuarios/tests_seguridad.py`).
- Las 12 migraciones nuevas se aplicaron sin errores sobre una **copia** de la base
  de desarrollo (sin perder filas: 24 SM, 12 OC, 5 facturas, 13 proveedores,
  102 registros de bitácora; de 7 salidas a obra antiguas, 5 recibieron partida y 2
  quedan «sin partida»). La base de desarrollo original **no** se migró.

Equivalencia de roles: Administrador/Administración = `ADMIN` · Jefe de Proyecto =
`JEFE_PROYECTO` · Adquisiciones = `ENCARGADO_ADQUISICIONES` · Bodega = `BODEGUERO` ·
Contabilidad = `CONTABILIDAD`. `ADMIN` pasa todos los controles de rol.

---

## Módulo 1 — Proveedores

| ID | Estado | Dónde está | Notas |
|---|---|---|---|
| RF-01 | ✅ | `proveedores/forms.py` `ProveedorForm` (`OBLIGATORIOS`, `clean_rut`); `usuarios/validators.py` | RUT chileno + DV + anti-duplicado (CU-01 Exc. 2 enlaza al existente). Giro, dirección, correo, teléfono y condición obligatorios. Materiales manuales o por Excel. |
| RF-02 | ✅ | `ProveedorUpdateView`; `Proveedor.modificado` | Fecha de última modificación visible en la ficha. El RUT no se edita. |
| RF-03 | ✅ | `proveedor_material_agregar` | — |
| RF-04 | ✅ | `proveedor_material_disponibilidad` | Con confirmación; historial intacto. |
| RF-05 | ✅ | `proveedor_material_editar`; `ProveedorMaterial.modificado` | — |
| RF-06 | ✅ | `proveedor_inactivar` | Inactivos fuera de cotización, SM, OC y factura. |

## Módulo 2 — Proyectos e itemizado

| ID | Estado | Dónde está | Notas |
|---|---|---|---|
| RF-07 | ✅ | `proyectos/views.py` `ProyectoCreateView` (`ROLES_OBRA`); `ProyectoForm` | **Decisión del grupo:** ADMIN y JEFE_PROYECTO registran obras; el JP que la registra queda asignado. Todos los campos obligatorios; centro de costo único; nace «En planificación». Editar datos: ADMIN en todas, JP sólo en sus obras (`exigir_acceso_proyecto`). |
| RF-08 | ✅ | `ItemizadoFormSet`, `itemizado_crear/editar`, `auditar_itemizado` | ADMIN en todas las obras; JP sólo en las suyas. Cada alta, cambio o baja de partida queda en la bitácora con usuario, fecha y operación. Una partida con salidas imputadas no se elimina. |
| RF-09 | ✅ | `Proyecto.jefes`; `ProyectoForm(usuario=…)` | Sólo ADMIN: al JP el formulario no le ofrece el campo (tampoco entra por POST). Único o compartido. CU-09 Exc. 1: aviso + enlace a crear usuario. |
| RF-10 | ✅ | `proyecto_cambiar_estado`, `CambioEstadoProyectoForm` | Sólo ADMIN. Sólo los 3 estados, con confirmación. Se eliminó «Suspendido» (migración). |
| RF-11 | ✅ | `SolicitudForm.clean_proyecto`, `solicitud_emitir` | Finalizado bloquea crear y emitir, con mensaje (CU-11 Exc. 1). |

## Módulo 3 — Solicitud de materiales

| ID | Estado | Dónde está | Notas |
|---|---|---|---|
| RF-12 | ✅ | `solicitudes/views.py` `solicitud_crear`, `solicitud_emitir`; `SolicitudMaterial._siguiente_correlativo` | Sólo JP, obra «En ejecución» asignada, partida obligatoria, material del catálogo. Al emitir: correlativo SM-000001 único, secuencial, no editable, y estado «Emitida». |
| RF-13 | ✅ | `SolicitudDetalleForm.clean`; `Itemizado.saldo_restante`; JS `_buscador_material.html` | El saldo descuenta lo pedido en otras SM emitidas (o lo ejecutado, lo que sea mayor); se revalida al emitir. |
| RF-14 | ✅ | `SolicitudAdjunto`, acción `adjuntar`, `adjunto_eliminar` | 3 archivos, PDF/JPG, 5 MB; sólo el JP responsable. |
| RF-15 | ✅ | `SolicitudMaterial.cambiar_estado`; `usuarios/notificaciones.py`; `Notificacion` | Los 6 estados del documento; cada cambio notifica (campana + correo) a los jefes de la obra, con descripción opcional (CU-15 Exc. 1). |

## Módulo 4 — Adquisiciones y cotizaciones

| ID | Estado | Dónde está | Notas |
|---|---|---|---|
| RF-16 | ✅ | `cotizacion_bandeja` | Emitidas, de la más antigua a la más reciente; mensaje si está vacía. |
| RF-17 | ✅ | `cotizacion_sm` acción `agregar_cotizacion` | Nace «Pendiente». |
| RF-18 | ✅ | `Cotizacion.valor_total` | Σ(cant × VU) + despacho. |
| RF-19 | ✅ | `CotizacionLinea.aprobar` | Aprueba una por material y descarta el resto. |
| RF-20 | ✅ | `_refrescar_estado_cotizacion` | «En cotización» + notificación al JP + habilita generar OC. |

## Módulo 5 — Órdenes de compra

| ID | Estado | Dónde está | Notas |
|---|---|---|---|
| RF-21 | ✅ | `_generar_ordenes_compra`, `OrdenCompra.datos_faltantes`, `_asignar_folio` | Una por proveedor; datos de M5 y del proveedor (incl. dirección) copiados; CU-21 Exc. 1 bloquea si faltan; folio automático, único y no editable. |
| RF-22 | ✅ | `orden_detalle` (`aprobar`/`rechazar`) | Sólo el JP de la obra; motivo obligatorio; notifica a quien generó la OC. |
| RF-23 | ✅ | `orden_editar`, `devolver_borrador` | — |
| RF-24 | ✅ | `orden_pdf`; `adquisiciones/pdf.py` | Sólo OC aprobadas (CU-24 Exc. 1), con logo; JP sólo las de su obra. |
| RF-25 | ✅ | `_enviar_orden_al_proveedor` | PDF adjunto; «Enviada» sólo si el correo salió. Sin correo o con falla queda «Aprobada» y avisa a Adquisiciones (reintentar / registrar entrega manual). Requiere SMTP configurado en producción. |

## Módulo 6 — Inventario y bodega

| ID | Estado | Dónde está | Notas |
|---|---|---|---|
| RF-26 | ✅ | `entrada_crear`, `EntradaForm` | Sólo Bodega; contra OC enviada (CU-26 Exc. 1) o proyecto (CU-27 Exc. 1); ubicación física; sin precios para Bodega (OC, SM, catálogo). |
| RF-27 | ✅ | `EntradaForm.clean` | No supera lo pendiente de la línea. |
| RF-28 | ✅ | `SalidaForm`; `MovimientoInventario.partida` | Material, cantidad, proyecto, JP (obligatorio y asignado a la obra), guía y **partida obligatoria de la obra elegida** (selector filtrado por obra). |
| RF-29 | ✅ | `MovimientoInventario.save` | Stock en tiempo real con bloqueo de fila; nunca negativo (CU-30 Exc. 1); el stock ya no se edita a mano. |
| RF-30 | ✅ | `prestamo_crear`, `_avisar_administracion` | Valida herramienta en bodega (CU-31 Exc. 1); notifica a Administración. |
| RF-31 | ✅ | `prestamo_devolver` | — |
| RF-32 | ✅ | `merma_crear`, `MermaForm` | Daño/Robo obligatorio; registra proyecto; descuenta stock. |
| RF-33 | ✅ | `devolucion_proveedor_crear`, `DevolucionProveedorForm` | OC con material recibido, material de la OC, cantidad ≤ recibido − devuelto; motivo obligatorio. |
| RF-34 | ✅ | `bodega_panel`, `Material.bajo_stock_minimo` | — |
| RF-35 | ✅ | `orden_detalle` acción `recepcion`, `RecepcionEstadoForm`, `notificar_recepcion` | El estado debe calzar con lo recibido por Bodega (CU-36 Exc. 1); aviso al JP con cantidades. |
| RF-36 | ✅ | `solicitud_detail.html` | Estado de recepción de cada OC por separado; mensaje si aún no hay OC (CU-37 Exc. 1). |

## Módulo 7 — Facturación

| ID | Estado | Dónde está | Notas |
|---|---|---|---|
| RF-37 | ✅ | `factura_crear`, `Factura.total_ordenes` | Compara contra el total **con IVA** de las OC (antes contra el neto). Fuera de tolerancia queda «Bloqueada» y la OC no se marca facturada. |
| RF-38 | ✅ | `factura_desbloquear` | Sólo ADMIN, con justificación auditada. |
| RF-39 | ✅ | `cuentas_por_pagar` | — |
| RF-40 | ✅ | `factura_export_csv` | Sin facturas informa (CU-41 Exc. 1). |

## Módulo 8 — Reportes y trazabilidad

| ID | Estado | Dónde está | Notas |
|---|---|---|---|
| RF-41 | ✅ | `reportes/consultas.py` `consumo_por_proyecto` | JP restringido a sus obras. |
| RF-42 | ✅ | `desviacion_presupuestaria`; migración `inventario/0008` | Gráfico + tabla. «Comprado» = OC aprobadas o posteriores (incluye compras anticipadas). «Consumido» = salidas a obra imputadas a cada partida. Salidas antiguas sin partida: se completan si el material se pidió en esa obra contra una sola partida; el resto va en la fila «(sin partida)», fuera del gráfico. |
| RF-43 | ✅ | `mermas_y_perdidas` | Filtro por proyecto y fechas funcional; valorizado. |
| RF-44 | ✅ | `compras_por_proveedor` | — |
| RF-45 | ✅ | `reportes/exportar.py` | XLSX y PDF. |
| RF-46 | ✅ | `adquisiciones/trazabilidad.py` | Por SM, folio de OC, código interno, código del proveedor o nombre; JP sólo sus obras; Bodega/Contabilidad no entran. |

## Módulo 9 — Seguridad, auditoría y gestión documental

| ID | Estado | Dónde está | Notas |
|---|---|---|---|
| RF-47 | ✅ | `usuarios/backends.py` `CorreoOUsuarioBackend`; `LoginForm` | **Decisión del grupo:** nombre de usuario **o** correo institucional (sin distinguir mayúsculas), más contraseña. Campo «Usuario o correo». El error no dice qué campo falló (CU-48 Exc. 1). |
| RF-48 | ✅ | `UsuarioCreateView/UpdateView`, `usuario_cambiar_estado` | — |
| RF-49 | ✅ | `usuarios/correos.py` | — |
| RF-50 | ✅ | `auditoria/models.py` (`Operacion`, `OPERACION_DE`), `signals.py` | ID de usuario, fecha, hora y Crear/Editar/Eliminar. |
| RF-51 | ✅ | `ArchivoProyecto`, `archivo_subir`, migración `0009_tipos_documento_rf51` | Seis tipos iniciales; planos 3D y videos aceptados; cuota 10 GB. |
| RF-52 | ✅ | `SESSION_COOKIE_AGE`, `SESSION_SAVE_EVERY_REQUEST`, `rol_requerido` | Al vencer, redirige al login (antes 403 en vistas de función). |
| RF-53 | ✅ | `PasswordResetView` | — |
| RF-54 | ✅ | `archivo_subir`, JS en `proyecto_detail.html` | Advierte sobre el umbral; para fotos ofrece reducir la resolución en el navegador; para otros formatos sugiere comprimir. |
| RF-55 | ✅ | `archivo_bloquear` | Bloquea y descarga. |
| RF-56 | ✅ | `archivo_subir_version` | — |
| RF-57 | ✅ | `parametros_sistema`; `tipo_documento_crear/editar` | Tipos: agregar, editar, deshabilitar (CU-60 Exc. 2 sin tocar archivos). |

## Módulo 10 — Catálogo maestro

| ID | Estado | Dónde está | Notas |
|---|---|---|---|
| RF-58 | ✅ | `Material.tipo`, `MaterialForm` | Clasificación explícita; stock mínimo; sólo ADMIN registra/edita; stock no editable a mano. |
| RF-59 | ✅ | `Material._generar_codigo_interno` | — |
| RF-60 | ✅ | `MaterialListView` | — |

---

## Requerimientos no funcionales

| ID | Estado | Dónde está | Notas |
|---|---|---|---|
| RNF-01 | ✅ | PostgreSQL, FK `PROTECT` | — |
| RNF-02 | 🟡 | Web cliente-servidor; RF-55/56 | **Pendiente:** el trabajo sin conexión existe sólo para archivos (descargar-bloquear-subir). Una sincronización offline general (PWA/cola local) no está implementada. |
| RNF-03 | ✅ | — | Medido sobre copia de datos reales: búsquedas de proveedor/stock 5–7 ms, trazabilidad 58 ms (sin red). |
| RNF-04 | ✅ | Bootstrap local | Pantallas de SM ≈ 25 KB de HTML + ≈ 620 KB de estáticos cacheables. |
| RNF-05 | ✅ | `ArchivoProyecto.CUOTA_PROYECTO_GB`, `TAM_MAX_MB`; `nginx-m5.conf` | 10 GB por proyecto; 2 GB por archivo. |
| RNF-06 | ✅ | Django PBKDF2-SHA256 | Hash unidireccional SHA-256 (ver stack: no es Bcrypt). |
| RNF-07 | 🟡 | `USAR_HTTPS` en `settings.py`; `despliegue/nginx-m5.conf` | **Listo en el código**; falta instalar el certificado en el servidor de M5 y poner `USAR_HTTPS=True`. |
| RNF-08 | ✅ | `usuarios/backends.py`, `IntentoAcceso` | 5 fallos → 15 min, también en el admin. El contador es por cuenta: suman los fallos con usuario y con correo, y el bloqueo cierra ambas entradas. |
| RNF-09 | ✅ | `usuarios/integridad.py` | OC, proveedores, facturas y movimientos no se borran (instancia, queryset ni admin). |
| RNF-10 | ✅ | `despliegue/instalar.sh` → `/etc/cron.d/m5-backup` | 00:00 diario (requiere correr `instalar.sh` en el servidor). |
| RNF-11 | ✅ | `FacturaForm.clean_archivo`, `factura_archivo` | Descarga protegida. |
| RNF-12 | ✅ | Bootstrap 5 | No probado en dispositivo físico. |
| RNF-13 | ✅ | HTML/CSS/JS estándar | El JS nuevo usa `DataTransfer` (soportado en los 4 navegadores en versiones de los últimos 2 años). No probado en Safari. |
| RNF-14 | ✅ | Git | Un commit por módulo en esta rama. |

---

## Matriz rol × funcionalidad (final, verificada por `usuarios/tests_permisos.py`)

✅ entra · ⛔ 403 por URL directa · (propias) = sólo sus obras.

| Funcionalidad | Admin | JP | Adq. | Bodega | Contab. |
|---|---|---|---|---|---|
| Usuarios, parámetros, tipos de documento (gestión) | ✅ | ⛔ | ⛔ | ⛔ | ⛔ |
| Proveedores | ✅ | ⛔ | ✅ | ⛔ | ⛔ |
| Registrar obra (RF-07) | ✅ | ✅ (queda asignado) | ⛔ | ⛔ | ⛔ |
| Editar datos de la obra e itemizado (RF-07, RF-08) | ✅ | ✅ (propias) | ⛔ | ⛔ | ⛔ |
| Asignar/quitar jefes, cambiar estado, eliminar obra (RF-09, RF-10) | ✅ | ⛔ | ⛔ | ⛔ | ⛔ |
| Consultar obra / archivos de obra | ✅ | ✅ (propias) | ✅ | ⛔ | ✅ |
| Crear, emitir, adjuntar, corregir SM | ✅ | ✅ (propias) | ⛔ | ⛔ | ⛔ |
| Ver SM | ✅ | ✅ (propias) | ✅ | ✅ sin precios | ✅ |
| Bandeja, cotizar, generar OC, rechazar SM | ✅ | ⛔ | ✅ | ⛔ | ⛔ |
| Aprobar/rechazar OC | ✅ | ✅ (propias) | sólo compra anticipada | ⛔ | ⛔ |
| PDF de OC aprobada | ✅ | ✅ (propias) | ✅ | ⛔ | ⛔ |
| Estado de recepción de OC | ✅ | ⛔ | ✅ | ⛔ | ⛔ |
| Movimientos de bodega y préstamos | ✅ | ⛔ | ⛔ (sólo consulta) | ✅ | ⛔ |
| Catálogo: consultar / registrar | ✅ / ✅ | ✅ / ⛔ | ✅ / ⛔ | ✅ / ⛔ | ⛔ / ⛔ |
| Facturas, cuentas por pagar, CSV | ✅ | ⛔ | ⛔ | ⛔ | ✅ |
| Desbloquear factura | ✅ | ⛔ | ⛔ | ⛔ | ⛔ |
| Reportes RF-41/42/43 · RF-44 | ✅ · ✅ | ✅ (propias) · ⛔ | ✅ · ✅ | ⛔ | ⛔ |
| Trazabilidad | ✅ | ✅ (propias) | ✅ | ⛔ | ⛔ |
| Bitácora de auditoría | ✅ | ⛔ | ⛔ | ⛔ | ✅ |

## Trazabilidad de punta a punta

`adquisiciones/tests_e2e.py::CadenaCompletaTest` recorre la cadena con el rol que
corresponde en cada paso y verifica estados, correlativos y que nada se pierda:
proveedores → obra con itemizado y JP → SM (sin número en borrador, SM-xxxxxx al
emitir) → dos cotizaciones → aprobación por material de proveedores distintos →
dos OC con folios distintos → rechazo, notificación y corrección → aprobación y
envío con PDF → recepción parcial, intento de exceso bloqueado, recepción total
→ SM «Entregada» y stock correcto → factura con IVA (OC facturada e
independiente de la recepción) → cuentas por pagar → reportes → el buscador
reconstruye la cadena por SM, por folio de OC y por código de material.

## Integridad de datos

- Borrado lógico: proveedores (inactivar), materiales de proveedor (no
  disponible), usuarios (deshabilitar), tipos de documento (deshabilitar).
- Sin borrado físico: OC, proveedores, facturas, movimientos (RNF-09).
- Fecha de última modificación: proveedor y material de proveedor.
- Bitácora: sólo lectura, con tipo de operación; movimientos de bodega
  auditados por señal (ninguno queda fuera); cambios del itemizado auditados.
- Partidas con salidas imputadas no se borran (PROTECT).
- Stock: sólo cambia con movimientos, con bloqueo de fila y sin negativos.

## Stack

| Comprometido | Real | Estado |
|---|---|---|
| Django 4.2+ / Python 3.10+ | Django 5.2.17 / Python 3.11.9 | ✅ |
| HTML5 + CSS3 + Bootstrap 5 + JS vanilla | Igual (Bootstrap servido localmente) | ✅ |
| PostgreSQL 14+ | PostgreSQL 18 | ✅ |
| Django auth + RBAC | `RolRequeridoMixin`, `rol_requerido`, backend propio | ✅ |
| HTTPS/SSL-TLS, CSRF | CSRF ✅; HTTPS configurable (`USAR_HTTPS` + nginx) | 🟡 falta certificado en servidor |
| Bcrypt | PBKDF2-SHA256 (Django) | Diferencia documentada |
| Soft delete + backup diario | ✅ | ✅ |
| DRF (integración futura) | No instalado | Diferencia documentada |
| — | reportlab, openpyxl, pillow, python-dotenv, psycopg2-binary, gunicorn + nginx | Ver informe |
