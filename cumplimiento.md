# Cumplimiento de requerimientos — Sistema de Adquisiciones M5

> **Estado: AUDITORÍA INICIAL (Fase 1).** Este archivo refleja el código tal como estaba
> el 14-11-2026 antes de las correcciones (commit `742ac1f`). La versión final, con el
> estado posterior a la Fase 2, reemplaza este contenido.

Fuentes de verdad: `requerimientos_funcionales.md`, `casos_de_uso.md`,
`requerimientos_no_funcionales.md`.

Equivalencia de roles usada en toda la auditoría:

| Documento | Código (`Usuario.Rol`) |
|---|---|
| Administrador / Administración | `ADMIN` (el documento usa los dos nombres para el mismo perfil) |
| Jefe de Proyecto | `JEFE_PROYECTO` |
| Adquisiciones | `ENCARGADO_ADQUISICIONES` |
| Bodega | `BODEGUERO` |
| Contabilidad | `CONTABILIDAD` |

`ADMIN` pasa todos los controles (`usuarios/permisos.py`: `RolRequeridoMixin`, `rol_requerido`).

Línea base: `manage.py check` sin errores, sin migraciones pendientes, **396 tests OK**.

---

## Módulo 1 — Proveedores

| ID | Estado | Dónde está | Qué falta o qué está mal |
|---|---|---|---|
| RF-01 | 🟡 | `proveedores/models.py` `Proveedor`; `forms.py` `ProveedorForm.clean_rut`; `usuarios/validators.py` `validar_rut` | RUT chileno + DV + anti-duplicado OK. **Giro, dirección, correo y teléfono son opcionales** (`blank=True`) y el RF los exige. CU-01 Exc. 2 no "sugiere localizar el registro existente" (no hay enlace). Materiales: alta manual o por Excel OK. |
| RF-02 | 🟡 | `ProveedorUpdateView` | **No se guarda fecha de última modificación** del proveedor (solo `creado`). |
| RF-03 | ✅ | `proveedor_material_agregar`, `ProveedorMaterialForm` | — |
| RF-04 | ✅ | `proveedor_material_disponibilidad` (toggle, `confirm()` en plantilla) | No borra; historial intacto. Cotización/SM filtran `disponible=True`. |
| RF-05 | ✅ | `proveedor_material_editar`, `ProveedorMaterial.modificado` (`auto_now`) | — |
| RF-06 | ✅ | `proveedor_inactivar` (POST + `confirm()`) | Inactivos excluidos de cotización, SM, OC directa y factura. |

## Módulo 2 — Proyectos e itemizado

| ID | Estado | Dónde está | Qué falta o qué está mal |
|---|---|---|---|
| RF-07 | 🟡 | `proyectos/views.py` `ProyectoCreateView`; `forms.py` `ProyectoForm.clean_centro_costo` | **Lo puede hacer el Jefe de Proyecto** (`ROLES_GESTION = ["JEFE_PROYECTO"]`); el RF dice solo Administrador. Centro de costo y fecha de término son **opcionales** (CU-07 los exige). El estado inicial se elige en el formulario (debería nacer "En planificación"). |
| RF-08 | 🟡 | `ItemizadoFormSet`, `itemizado_crear/editar` | Funciona, pero **lo carga el JP**; CU-08 dice Administrador. |
| RF-09 | 🟡 | `Proyecto.jefes` (M2M), `ProyectoForm` | Asignación múltiple OK. **Un JP puede asignarse a sí mismo a cualquier obra** (edita cualquier proyecto). CU-09 Exc. 1 (sin JP → redirigir a gestión de usuarios) no existe. |
| RF-10 | 🟡 | `ProyectoForm.estado` | Roles incorrectos (JP). **Estado extra "Suspendido"** no está en el documento. |
| RF-11 | 🟡 | `SolicitudForm.clean_proyecto` | Bloquea "Finalizado", pero deja pedir para "Planificación"/"Suspendido" (RF-12 exige "En ejecución"). |

## Módulo 3 — Solicitud de materiales

| ID | Estado | Dónde está | Qué falta o qué está mal |
|---|---|---|---|
| RF-12 | 🟡 | `solicitudes/views.py` `solicitud_crear`, `solicitud_enviar`; `forms.py` `SolicitudForm`, `SolicitudDetalleForm` | **Adquisiciones también puede crear SM** (RF: solo JP). Admite proyectos que no están "En ejecución" y **proyectos sin jefe asignado**. **Partida opcional** (RF: obligatoria). Se puede escribir un material libre y **se crea en el catálogo maestro** (RF: elegirlo del catálogo). El flujo es Borrador → Enviada → Aprobada en vez de quedar "Emitida" al confirmar. Correlativo `SM-000001` automático y no editable OK (pero se asigna en borrador). |
| RF-13 | 🟡 | `SolicitudDetalleForm.clean`, `templates/solicitudes/_buscador_material.html` (alerta JS) | Alerta + justificación obligatoria OK, pero el **"saldo restante" ignora lo ya pedido en otras SM**: `Itemizado.saldo_disponible = presupuestado − cant_ejecutada` (campo manual). Dos SM que juntas exceden la partida no disparan la alerta. |
| RF-14 | 🟡 | `SolicitudAdjunto`, `SolicitudAdjuntoForm`, acción `adjuntar` en `solicitud_detalle` | 3 archivos / PDF-JPG / 5 MB OK. **Cualquier rol que puede ver la SM (Bodega, Contabilidad, cualquier JP) puede adjuntar**; `adjunto_eliminar` no verifica dueño. |
| RF-15 | ❌ | — | **No existe notificación al Jefe de Proyecto** en ningún cambio de estado de la SM (solo se avisa a Adquisiciones por correo). No hay sistema de notificaciones en la aplicación. |

## Módulo 4 — Adquisiciones y cotizaciones

| ID | Estado | Dónde está | Qué falta o qué está mal |
|---|---|---|---|
| RF-16 | 🟡 | `adquisiciones/views.py` `cotizacion_bandeja` | Ordenada ascendente, mensaje de bandeja vacía OK. El estado se llama "Aprobada" en el código y no "Emitida". |
| RF-17 | ✅ | `cotizacion_sm` acción `agregar_cotizacion`; `Cotizacion`/`CotizacionLinea` | Proveedor, valor unitario, despacho y días hábiles; nace "Pendiente". |
| RF-18 | ✅ | `Cotizacion.valor_total` | Σ(cant × VU) + despacho. |
| RF-19 | ✅ | `CotizacionLinea.aprobar` | Aprueba una y descarta las demás del mismo material. |
| RF-20 | 🟡 | `_refrescar_estado_cotizacion` | Cambio a "En cotización" y botón de generar OC OK. **No notifica al JP** (CU-20). |

## Módulo 5 — Órdenes de compra

| ID | Estado | Dónde está | Qué falta o qué está mal |
|---|---|---|---|
| RF-21 | 🟡 | `_generar_ordenes_compra`, `OrdenCompra._asignar_folio` | Una OC por proveedor, folio automático, único (bloqueo `select_for_update`) y no editable OK. **No se copia ni se valida la dirección del proveedor**; CU-21 Exc. 1 (faltan datos de facturación/proveedor → bloquear) no existe. |
| RF-22 | ✅ | `orden_detalle` acciones `aprobar`/`rechazar` | Solo JP de la obra (o Adquisiciones en compra anticipada); motivo obligatorio; correo al creador. |
| RF-23 | ✅ | `orden_editar`, acción `devolver_borrador` | — |
| RF-24 | 🟡 | `orden_pdf`, `adquisiciones/pdf.py` | PDF con logo OK. **Se exporta en cualquier estado** (borrador/rechazada) — CU-24 Exc. 1. **Un JP puede descargar la OC de una obra ajena** (no hay control de propiedad). |
| RF-25 | 🟡 | `_enviar_orden_al_proveedor` | Envía PDF adjunto. **Si el proveedor no tiene correo o el envío falla, la OC queda "Enviada" igual** (CU-25 Exc. 1: debe quedar "Aprobada" y avisar a Adquisiciones). `fail_silently=True` oculta las fallas. |

## Módulo 6 — Inventario y bodega

| ID | Estado | Dónde está | Qué falta o qué está mal |
|---|---|---|---|
| RF-26 | 🟡 | `inventario/views.py` `entrada_crear`; `EntradaForm` | Entrada por OC o por devolución de obra + ubicación OK. **Adquisiciones también registra entradas** (RF: Bodega). **Bodega ve precios** en `orden_detalle` y en el detalle de la SM (plantillas no ocultan). |
| RF-27 | ✅ | `EntradaForm.clean` | Valida contra lo pendiente de la línea de OC. |
| RF-28 | 🟡 | `SalidaForm` | **Jefe de proyecto opcional** y no se valida que esté asignado a la obra. Adquisiciones también registra. |
| RF-29 | ✅ | `MovimientoInventario.save` (`F()`), validaciones de stock en formularios | — |
| RF-30 | 🟡 | `prestamo_crear`, `_avisar_administracion` | Registro + correo a Administración OK. **No valida que la herramienta esté en bodega**: descuenta 1 aunque el stock sea 0 (queda negativo) — CU-31 Exc. 1. |
| RF-31 | ✅ | `prestamo_devolver` | — |
| RF-32 | 🟡 | `merma_crear`, `MermaForm` | Daño/Robo y descuento OK. **No se registra el proyecto**, así que el reporte RF-43 no puede filtrar por proyecto. |
| RF-33 | 🟡 | `devolucion_proveedor_crear`, `DevolucionProveedorForm` | Motivos y guía OK. Acepta OC rechazadas/aprobadas sin despacho; **no valida que el material pertenezca a la OC** ni la cantidad recibida. |
| RF-34 | ✅ | `bodega_panel`, `Material.bajo_stock_minimo` | — |
| RF-35 | 🟡 | `orden_detalle` acción `recepcion`; `RecepcionEstadoForm` | Cambio de estado y correo al JP con cantidades OK. **CU-36 Exc. 1 no implementada**: se puede marcar "Recepción parcial" (o "Recibida") sin cantidades registradas. |
| RF-36 | ✅ | `solicitud_detalle` (`ordenes_compra`), plantilla | — |

## Módulo 7 — Facturación

| ID | Estado | Dónde está | Qué falta o qué está mal |
|---|---|---|---|
| RF-37 | 🟡 | `facturacion/views.py` `factura_crear`; `FacturaForm` | Vínculo a 1+ OC, campo `facturada` independiente, tolerancia parametrizable OK. **Compara el total de la factura (con IVA) contra el NETO de la OC**: una factura correcta de una OC de $500.000 + IVA ($595.000) da 19 % de diferencia y queda bloqueada. |
| RF-38 | ✅ | `factura_desbloquear` (solo ADMIN, con justificación, auditado) | — |
| RF-39 | ✅ | `cuentas_por_pagar` | Orden por vencimiento ascendente; mensaje de vista vacía. |
| RF-40 | 🟡 | `factura_export_csv` | CSV OK. CU-41 Exc. 1 (sin facturas → informar) no existe: baja un CSV vacío. |

## Módulo 8 — Reportes y trazabilidad

| ID | Estado | Dónde está | Qué falta o qué está mal |
|---|---|---|---|
| RF-41 | ✅ | `reportes/consultas.py` `consumo_por_proyecto`, `proyectos_visibles` | JP restringido a sus obras. |
| RF-42 | 🟡 | `desviacion_presupuestaria` | Gráfico + tabla OK. **"Comprado" ignora las compras anticipadas** (filtra `orden__solicitud__proyecto`). |
| RF-43 | 🟡 | `mermas_y_perdidas` | Valoriza OK, filtro de fechas OK, pero **el filtro por proyecto nunca encuentra nada** (las mermas no guardan proyecto, ver RF-32). |
| RF-44 | ✅ | `compras_por_proveedor` | Solo Adquisiciones/Admin. |
| RF-45 | ✅ | `reportes/exportar.py` | XLSX (openpyxl) y PDF (reportlab). |
| RF-46 | 🟡 | `adquisiciones/trazabilidad.py` `buscar` | SM/OC por correlativo y folio OK. **No busca por código de material** (solo nombre). **Bodega y Contabilidad entran** (RF: JP, Adquisiciones, Administración) y **el JP ve cadenas de obras ajenas**. |

## Módulo 9 — Seguridad, auditoría y gestión documental

| ID | Estado | Dónde está | Qué falta o qué está mal |
|---|---|---|---|
| RF-47 | 🟡 | `config/urls.py` `LoginView` | **Se entra con nombre de usuario**, no con correo institucional. |
| RF-48 | ✅ | `usuarios/views.py` `UsuarioCreateView/UpdateView`, `usuario_cambiar_estado` | Correo único validado. (Extras no documentados: auto-registro con aprobación, eliminación de cuentas sin historial.) |
| RF-49 | ✅ | `usuarios/correos.py` `enviar_enlace_activacion` | Token de un solo uso; reintentos y aviso al admin (CU-52 Exc. 1). |
| RF-50 | 🟡 | `auditoria/models.py` `registrar`, `signals.py` | Usuario, fecha y hora OK. **No se registra el tipo de operación Crear/Editar/Eliminar** que pide el RF. |
| RF-51 | 🟡 | `ArchivoProyecto`, `archivo_subir` | Metadatos OK. **El catálogo no trae los tipos del RF** (Contrato, Especificación Técnica, Plano 2D, Plano 3D, Fotografía, Videos) y **no se aceptan formatos de video**. El archivo se sirve por URL directa de `/media/` sin control de acceso. |
| RF-52 | ✅ | `SESSION_COOKIE_AGE=1800`, `SESSION_SAVE_EVERY_REQUEST` | — |
| RF-53 | ✅ | `PasswordResetView` | Mensaje genérico (CU-56 Exc. 1). |
| RF-54 | 🟡 | `archivo_subir` (`confirmar_tamano`) | Advierte y pide confirmar, pero **no ofrece reducir la resolución**; además un tope fijo de 10 MB (`TAM_MAX_MB`) bloquea antes del umbral configurable. |
| RF-55 | 🟡 | `archivo_bloquear` | El bloqueo existe, pero **no descarga** el archivo (el usuario debe bajarlo aparte por un enlace sin control). |
| RF-56 | ✅ | `archivo_subir_version` | Mismo formato exigido; libera el bloqueo. |
| RF-57 | 🟡 | `parametros_sistema`; `TipoDocumentoListView`, `tipo_documento_crear` | Tolerancia, stock mínimo y umbral OK. **Tipos de documento: no se pueden editar ni deshabilitar**, y **los crea el JP** (RF: Administración). |

## Módulo 10 — Catálogo maestro

| ID | Estado | Dónde está | Qué falta o qué está mal |
|---|---|---|---|
| RF-58 | 🟡 | `inventario/models.py` `Material.tipo`, `MaterialForm` | Clasificación explícita OK. **El stock se edita a mano** en el formulario del catálogo (se salta los movimientos y la auditoría). CU-61 dice Administración; hoy también Bodega y Adquisiciones. |
| RF-59 | ✅ | `Material._generar_codigo_interno` | MAT-/HER- únicos con reintento (CU-62 Exc. 1). |
| RF-60 | ✅ | `MaterialListView` | Código, descripción, categoría, disponibilidad, ubicación. |

---

## Requerimientos no funcionales

| ID | Estado | Dónde está | Qué falta o qué está mal |
|---|---|---|---|
| RNF-01 | ✅ | `settings.DATABASES` PostgreSQL | FK con `PROTECT`. |
| RNF-02 | 🟡 | Web cliente-servidor | Solo existe trabajo offline para archivos (RF-55/56). No hay sincronización general offline. |
| RNF-03 | 🟡 | — | No medido. |
| RNF-04 | 🟡 | Bootstrap servido localmente | No medido. |
| RNF-05 | 🟡 | `ArchivoProyecto.TAM_MAX_MB = 10` | Tope por archivo de 10 MB; no hay control de cuota por proyecto. |
| RNF-06 | ✅ | Django PBKDF2-SHA256 | Hash unidireccional con SHA-256 (no Bcrypt, ver stack). |
| RNF-07 | 🟡 | — | No hay `SECURE_*` en settings ni configuración TLS en `despliegue/`. |
| RNF-08 | ❌ | — | **No existe bloqueo tras 5 intentos fallidos.** |
| RNF-09 | 🟡 | Sin vistas de borrado para OC/proveedor/factura/movimiento | **El admin de Django permite borrado físico** de OC, proveedores, facturas y movimientos. |
| RNF-10 | 🟡 | `despliegue/m5-backup` en `/etc/cron.daily` | Respaldo diario OK, pero `cron.daily` corre ~06:25, **no a las 00:00**. |
| RNF-11 | ✅ | `FacturaForm.clean_archivo` | PDF/XML. |
| RNF-12 | ✅ | Bootstrap 5 + `style.css` | Grilla responsive. |
| RNF-13 | ✅ | HTML/CSS estándar, sin APIs exóticas | No probado en Safari. |
| RNF-14 | ✅ | Git | — |

---

## Matriz rol × funcionalidad (estado inicial, verificada por URL directa)

Leyenda: ✅ = puede (200) · ⛔ = 403 · **⚠** = puede pero el documento no lo permite · **✗** = debería poder y no puede.

| Funcionalidad (URL) | Admin | JP | Adq. | Bodega | Contab. |
|---|---|---|---|---|---|
| Usuarios / Parámetros | ✅ | ⛔ | ⛔ | ⛔ | ⛔ |
| Proveedores (listar/crear) | ✅ | ⛔ | ✅ | ⛔ | ⛔ |
| Crear/editar proyecto, itemizado, asignar JP | ✅ | **⚠** | ⛔ | ⛔ | ⛔ |
| Tipos de documento (alta) | ✅ | **⚠** | ⛔ | ⛔ | ⛔ |
| Catálogo maestro (alta/edición) | ✅ | ⛔ | **⚠** | **⚠** | ⛔ |
| Movimientos de bodega / préstamos | ✅ | ⛔ | **⚠** | ✅ | ⛔ |
| Crear SM | ✅ | ✅ | **⚠** | ⛔ | ⛔ |
| Adjuntar / agregar línea a SM ajena | ✅ | **⚠** | ✅ | **⚠** | **⚠** |
| Bandeja / cotizar / generar OC | ✅ | ⛔ | ✅ | ⛔ | ⛔ |
| Aprobar/rechazar OC | ✅ | ✅ (su obra) | anticipada | ⛔ | ⛔ |
| Ver OC con precios | ✅ | su obra | ✅ | **⚠** | ✅ |
| PDF de OC | ✅ | **⚠ (cualquier obra)** | ✅ | ⛔ | ⛔ |
| Trazabilidad | ✅ | **⚠ (obras ajenas)** | ✅ | **⚠** | **⚠** |
| Facturas / cuentas por pagar / CSV / auditoría | ✅ | ⛔ | ⛔ | ⛔ | ✅ |
| Reportes RF-41..43 / RF-44 | ✅ | ✅ / ⛔ | ✅ / ✅ | ⛔ | ⛔ |

La protección está en el backend (decoradores/mixins) en todas las vistas revisadas; los
problemas son de **reglas mal definidas** (roles de más) y de **falta de control de propiedad**
en acciones POST de `solicitud_detalle`, `adjunto_eliminar`, `orden_pdf` y `trazabilidad`.

## Trazabilidad de punta a punta (estado inicial)

Proveedor → proyecto con itemizado → SM → cotización → aprobación de líneas → OC → aprobación
→ envío → recepción parcial/total → stock → factura → cuentas por pagar → reportes:
**el flujo completo funciona** (lo cubre `adquisiciones/tests.py` y el seed). Cortes encontrados:

1. La SM no pasa por el estado "Emitida" del documento (pasa por Borrador/Enviada/Aprobada).
2. El JP no se entera de ningún cambio de estado de su SM (RF-15).
3. Una OC a un proveedor sin correo queda "Enviada" aunque nunca salió (RF-25).
4. Una factura correcta con IVA se bloquea (RF-37).
5. El buscador no reconstruye la cadena desde el código del material (RF-46).

## Integridad de datos (estado inicial)

- Proveedor y material de proveedor: borrado lógico ✅. Usuario: inactivación ✅.
- OC, factura, movimiento: sin vistas de borrado, pero **borrables desde el admin** ❌.
- Fecha de última modificación: material de proveedor ✅, **proveedor ❌**.
- Bitácora: solo lectura (también en admin) ✅; falta tipo Crear/Editar/Eliminar.

## Stack

| Comprometido | Real | Estado |
|---|---|---|
| Django 4.2+ / Python 3.10+ | Django 5.2.17 / Python 3.11.9 | ✅ |
| Bootstrap 5 + JS vanilla | Bootstrap 5 local + JS vanilla | ✅ |
| PostgreSQL 14+ | PostgreSQL 18 | ✅ |
| Django auth + RBAC | `RolRequeridoMixin` / `rol_requerido` | ✅ |
| Bcrypt | PBKDF2-SHA256 (por defecto de Django) | 🟡 |
| HTTPS/SSL-TLS | No configurado en el repo | 🟡 |
| Django REST Framework (futuro) | No instalado; endpoints JSON propios en `solicitudes/api.py` | 🟡 (es "integración futura") |
| — | Extras: reportlab, openpyxl, pillow, python-dotenv | ver informe |

## Resumen inicial

| | ✅ | 🟡 | ❌ |
|---|---|---|---|
| RF (60) | 26 | 33 | 1 |
| RNF (14) | 6 | 7 | 1 |
