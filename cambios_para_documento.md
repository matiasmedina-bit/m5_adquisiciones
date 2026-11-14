# Cambios para el Documento 0 — alinear documento y sistema

Rama `revision-requerimientos`, 14-11-2026 (incluye los cambios finales decididos
por el grupo antes del merge: puntos 1.10, 1.14 y 1.18). Cada punto indica
qué dice el documento, qué hace el sistema y por qué. Las redacciones propuestas usan
el mismo formato del documento y se pueden copiar tal cual.

---

## 1. RF, CU o RNF cuya implementación difiere de lo escrito

### 1.1 RF-12 / RF-15 — Estado «Borrador» antes de confirmar la SM
- **Documento:** «Al confirmar se le asigna a la SM automáticamente un número correlativo […] y la SM queda en estado "Emitida"». RF-15 lista seis estados y ninguno es previo a la confirmación.
- **Sistema:** la SM se guarda primero como **Borrador** (sin número, sólo la ve su Jefe de Proyecto); en ese estado se agregan líneas y adjuntos. Al presionar «Emitir solicitud» recibe el correlativo y queda «Emitida».
- **Por qué:** «al confirmar» implica un estado anterior a la confirmación; permite adjuntar los respaldos (RF-14) antes de emitir.
- **Redacción propuesta RF-12 (final):** «… Mientras no se confirma, la SM queda en estado "Borrador", visible sólo para su Jefe de Proyecto. Al confirmar se le asigna […] y la SM queda en estado "Emitida".»
- **RF-15:** agregar «Borrador» como estado previo («Borrador» → «Emitida» → …).

### 1.2 RF-15 — Quién rechaza una SM
- **Documento:** RF-15 incluye «Rechazada», pero ningún RF ni CU dice quién rechaza una SM ni cuándo.
- **Sistema:** **Adquisiciones** rechaza una SM «Emitida» o «En cotización» (mientras no tenga OC), con motivo obligatorio que se notifica al Jefe de Proyecto. El Jefe de Proyecto puede devolverla a «Borrador», corregirla y volver a emitirla conservando su número.
- **Propuesta:** ver RF nuevo N-03 y CU nuevo CU-64 (sección 2).

### 1.3 RF-13 — Qué es el «saldo restante del itemizado»
- **Documento:** «si la cantidad solicitada supera el saldo restante del itemizado presupuestado».
- **Sistema:** saldo restante = cantidad presupuestada − el mayor entre (lo ya pedido en SM emitidas de esa partida) y (la cantidad ejecutada registrada). Se revalida al emitir.
- **Por qué:** con sólo «presupuestado − ejecutado», dos SM que juntas excedían la partida pasaban sin alerta. Se toma el mayor y no la suma para no contar dos veces el mismo material (lo pedido termina ejecutándose).
- **Redacción propuesta:** «… supera el saldo restante de la partida, entendido como la cantidad presupuestada menos lo ya solicitado en Solicitudes emitidas o lo ya ejecutado, lo que sea mayor.»

### 1.4 RF-12 — Material que viene del catálogo de un proveedor
- **Documento:** «selección del material desde el catálogo maestro».
- **Sistema:** se elige del catálogo maestro **o** de un ítem del catálogo de un proveedor. En este último caso el ítem queda vinculado a su material del catálogo maestro (si no existía, el sistema lo registra en el catálogo con su código interno). Ya no se puede crear un material escribiendo texto libre.
- **Propuesta:** agregar a RF-12: «… o desde el listado de materiales de un proveedor, que queda vinculado al material correspondiente del catálogo maestro (RF-59).»

### 1.5 RF-20 — Nombre del estado «En Cotización»
- **Documento:** la SM pasa a «En Cotización» *cuando todos sus materiales ya tienen una línea aprobada*.
- **Sistema:** implementado tal cual. Mientras se cotiza, la SM sigue «Emitida».
- **Observación:** el nombre confunde (la cotización ya terminó cuando entra a ese estado). Sugerencia: renombrar a «Cotización aprobada» o aclarar en RF-20: «"En Cotización" indica que la cotización está completa y lista para generar la OC».

### 1.6 RF-25 / CU-25 — OC que no se pudo enviar
- **Documento:** CU-25 Exc. 1: si el proveedor no tiene correo o el envío falla, la OC queda «Aprobada» y se notifica a Adquisiciones «para que gestione el envío manualmente».
- **Sistema:** implementado así (antes quedaba «Enviada» igual). Además, Adquisiciones puede **reintentar el envío** o **registrar la entrega manual** (indicando el medio), que deja la OC «Enviada» y auditada.
- **Propuesta:** agregar a la Excepción 1 de CU-25: «Adquisiciones puede reintentar el envío o registrar que la entregó por otro medio, lo que cambia la OC a "Enviada".»

### 1.7 RF-35 / CU-36 — De dónde salen las cantidades recibidas
- **Documento:** Adquisiciones actualiza el estado de la OC «junto con la cantidad recibida de cada material».
- **Sistema:** las cantidades las registra **Bodega** al recibir (RF-26), porque son las que mueven el stock. Adquisiciones elige el estado y el sistema exige que calce: «Recepción parcial» requiere cantidades registradas (CU-36 Exc. 1), «Recibida» requiere todo recibido y «No recibida» que no haya llegado nada. Además, cuando una entrada de Bodega completa o inicia la recepción, el estado de la OC se actualiza solo y se notifica al Jefe de Proyecto.
- **Por qué:** si Adquisiciones escribiera cantidades distintas de las de Bodega, el stock y la OC quedarían en desacuerdo.
- **Redacción propuesta RF-35:** «… a Recibida, Recepción Parcial o No Recibida, de acuerdo con las cantidades registradas por Bodega en la recepción (RF-26), notificando […]. El sistema también actualiza este estado automáticamente al registrarse la entrada en bodega.»

### 1.8 RF-37 — Monto de la factura y monto de la OC
- **Documento:** «validar el monto total de la factura ingresada contra el monto total de la OC asociada».
- **Sistema:** compara el total de la factura **con IVA** contra el total **con IVA** de las OC vinculadas. Antes comparaba contra el neto y bloqueaba todas las facturas correctas (19 % de diferencia).
- **Propuesta:** «… contra el monto total, IVA incluido, de la o las OC asociadas …».

### 1.9 RF-37 / RF-38 — Qué significa «bloquear su registro»
- **Documento:** RF-37 «bloquear su registro»; RF-38 «desbloquear el registro de una factura que haya sido bloqueada».
- **Sistema:** la factura fuera de tolerancia **se guarda en estado «Bloqueada»** (no aparece en Cuentas por Pagar y no marca la OC como facturada) hasta que Administración la desbloquea con una justificación.
- **Por qué:** para que RF-38 tenga algo que desbloquear, la factura tiene que quedar registrada en algún estado.
- **Propuesta:** «… y dejarla en estado "Bloqueada", sin marcar la OC como Facturada, si la diferencia supera …».

### 1.10 RF-47 — Credencial de acceso
- **Documento:** RF-47 «El sistema debe requerir autenticación de usuarios mediante credenciales únicas, correo electrónico institucional y contraseña.» CU-48 pide ingresar el correo.
- **Sistema (decisión del grupo):** se entra con el **nombre de usuario o el correo institucional**, más la contraseña. El campo del login se llama «Usuario o correo». El correo no distingue mayúsculas; el nombre de usuario sí. Ambos son únicos en el sistema, así que cada uno identifica una sola cuenta.
- **Bloqueo (RNF-08):** se mantiene igual para las dos formas: 5 intentos fallidos dejan la cuenta bloqueada 15 minutos. Los fallos se cuentan por **cuenta**, no por el texto escrito, así que alternar entre usuario y correo no da intentos extra, y mientras dura el bloqueo no se entra de ninguna de las dos formas, ni con la contraseña correcta.
- **Redacción propuesta RF-47:** «El sistema debe requerir autenticación de usuarios mediante credenciales únicas: nombre de usuario o correo electrónico institucional, y contraseña.»

**CU-48 propuesto — Autenticándose en el sistema**
- **Nombre:** Autenticándose en el sistema.
- **Actores:** Usuario.
- **Requerimiento:** RF-47.
- **Resumen:** El usuario se autentica con su nombre de usuario o su correo electrónico institucional, y su contraseña, para acceder a las funciones de su rol.
- **Frecuencia:** Alta.
- **Precondiciones:** El usuario debe tener una cuenta creada y habilitada en el sistema.
- **Flujo Principal:** El actor accede a la pantalla de inicio de sesión e ingresa su nombre de usuario o su correo electrónico institucional, y su contraseña. El sistema valida las credenciales ingresadas [Excepción 1] [Excepción 2]. El sistema autentica al actor y lo redirige a la pantalla principal correspondiente a su rol.
- **Excepciones:**
  - Excepción 1: Las credenciales ingresadas son incorrectas. El sistema rechaza el acceso y muestra un mensaje de error, sin especificar cuál campo es incorrecto.
  - Excepción 2: La cuenta acumula 5 intentos fallidos consecutivos, ingresados con el nombre de usuario o con el correo (RNF-08). El sistema bloquea el acceso a esa cuenta durante 15 minutos, por cualquiera de las dos formas, e informa la hora en que podrá volver a intentarlo.
- **Poscondiciones:** El actor queda autenticado en el sistema, con acceso a las funcionalidades correspondientes a su rol.
- **Dependencias:** —

### 1.11 RF-52 / CU-55 — Redirección al vencer la sesión
- **Sistema:** implementado; además se corrigió que varias pantallas devolvían «403» en vez de llevar al inicio de sesión. Sin cambios en el documento.

### 1.12 RF-54 — «Comprimir o reducir la resolución»
- **Sistema:** advierte al elegir el archivo; para fotos (JPG/PNG) ofrece reducir la resolución en el propio navegador; para otros formatos recomienda comprimirlo antes. Si se sube igual, pide confirmación. El sistema no comprime en el servidor.
- **Propuesta RF-54:** «… ofreciendo reducir la resolución de las imágenes y recomendando comprimir los demás formatos antes de completar la carga.»
- **CU-57 Poscondición:** hoy dice «La carga se completa dentro del umbral permitido», lo que contradice que se pueda subir igual. Propuesta: «La carga se completa, reducida si el actor lo eligió, o sobre el umbral si el actor lo confirmó.»

### 1.13 RF-55 / RF-56 vs RNF-02 — Alcance del trabajo sin conexión
- **Documento:** RNF-02 pide «un mecanismo de sincronización que permita a los usuarios trabajar de forma local sin conexión directa al servidor».
- **Sistema:** lo implementado es el de RF-55/56 (descargar con bloqueo y subir la versión editada) para los **archivos de proyecto**. No hay trabajo offline para SM, bodega ni otras pantallas.
- **Propuesta RNF-02:** «… e incorporar un mecanismo de descarga con bloqueo y posterior subida (RF-55, RF-56) que permita editar los archivos de trabajo sin conexión al servidor.» Si el grupo quiere mantener el alcance amplio, queda como pendiente.

### 1.14 RF-28 / RF-42 — Partida en la salida y «lo realmente consumido»
- **Documento:** RF-42 compara el itemizado «versus lo realmente comprado y consumido por obra»; RF-28 no pide la partida en la salida de bodega, así que no había cómo saber a qué partida se consumió cada material.
- **Sistema:** la salida a obra exige la **partida del itemizado** (sólo se ofrecen las de la obra elegida). En el reporte de desviación, «consumido» = suma de las salidas imputadas a cada partida; «comprado» = OC aprobadas o posteriores de la obra, incluidas las compras anticipadas. La cantidad ejecutada que se escribe a mano en el itemizado queda como dato informativo y ya no entra al reporte.
- **Salidas antiguas sin partida:** una migración les asigna la partida **sólo cuando no hay duda** (en esa obra el material se pidió contra una única partida). Las demás quedan sin partida y el reporte las muestra en una fila aparte «(sin partida)», fuera del gráfico. Así el consumo total de la obra no pierde nada y no se inventa a qué partida correspondía. En la copia de los datos reales: 5 de 7 salidas recibieron partida y 2 quedaron «sin partida».
- **Integridad:** una partida que ya tiene salidas imputadas no se puede eliminar del itemizado.
- **Redacción propuesta RF-28:** «El sistema debe permitir al rol Bodega registrar la salida de materiales o herramientas de bodega, exigiendo ingresar material, cantidad, proyecto destino, partida del itemizado del proyecto destino a la que se imputa la salida, jefe de proyecto asignado y número de guía de despacho asociado al traslado.»
- **Redacción propuesta RF-42:** «El sistema debe generar, para los roles Jefe de Proyecto, Adquisiciones y Administración, un reporte gráfico y tabular de Desviación Presupuestaria que compare, por partida del itemizado de cada proyecto, la cantidad presupuestada con la cantidad comprada en Órdenes de Compra aprobadas y con la cantidad consumida, entendida como la suma de las salidas de bodega imputadas a esa partida (RF-28). Las salidas sin partida se informan por separado.»

### 1.15 RNF-06 — Algoritmo de hash
- **Documento:** «por ejemplo, Bcrypt o SHA-256»; en el stack, «Bcrypt».
- **Sistema:** PBKDF2 con SHA-256, el algoritmo por defecto de Django (unidireccional, con sal y 1.000.000 de iteraciones). Cumple el RNF, pero no coincide con «Bcrypt» del stack.
- **Propuesta:** cambiar en el stack «Bcrypt» por «PBKDF2-SHA256 (Django)».

### 1.16 RNF-10 — Hora del respaldo
- **Sistema:** el respaldo antes corría en `cron.daily` (≈06:25); ahora corre a las 00:00 con `/etc/cron.d`. Respalda la base **y** la carpeta de archivos subidos, con 30 días de retención.
- **Propuesta:** agregar «incluyendo los archivos subidos, con retención de 30 días». Sugerencia: el RNF guarda el respaldo en el mismo servidor; conviene una copia fuera de él.

### 1.17 Actores ajustados al documento (antes el sistema daba más permisos)
Sin cambio de redacción, pero el sistema ahora sigue el documento:
- RF-09 y RF-10 (asignar/quitar jefes, cambiar estado) y eliminar obras: sólo Administrador. Antes lo hacía cualquier Jefe de Proyecto. (RF-07 y RF-08: ver 1.18, decisión del grupo.)
- RF-12 (crear SM): sólo Jefe de Proyecto. Antes también Adquisiciones.
- RF-26 a RF-33 (movimientos de bodega): sólo Bodega. Antes también Adquisiciones.
- CU-61 (registrar ítems del catálogo): sólo Administración. Antes también Bodega y Adquisiciones.
- RF-46 (trazabilidad): Jefe de Proyecto (sus obras), Adquisiciones y Administración. Antes también Bodega y Contabilidad.
- RF-57 (tipos de documento): sólo Administración. Antes los creaba el Jefe de Proyecto.

### 1.18 RF-07 / RF-08 / CU-07 / CU-08 — El Jefe de Proyecto también registra obras (decisión del grupo)
- **Documento:** RF-07 «permitir al perfil Administrador registrar un nuevo proyecto»; CU-07 y CU-08 tienen como único actor al Administrador.
- **Sistema (decisión del grupo):**
  - **Registrar obra:** Administrador y Jefe de Proyecto. El JP que la registra queda asignado automáticamente como jefe de esa obra.
  - **Editar los datos de la obra y su itemizado:** el Administrador en todas; el JP sólo en las obras donde está asignado. El centro de costo sigue siendo único.
  - **Asignar o quitar jefes (RF-09) y cambiar el estado (RF-10):** sólo el Administrador. Al JP el formulario no le ofrece esos campos, ni siquiera si los envía a mano.
  - Un JP nunca ve ni modifica obras a las que no está asignado (403 por URL directa).
  - Cada alta, cambio o baja de una partida del itemizado queda en el log de auditoría con usuario, fecha y operación.
- **Redacción propuesta RF-07:** «El sistema debe permitir a los perfiles Administrador y Jefe de Proyecto registrar un nuevo proyecto ingresando nombre de la obra, cliente mandante, centro de costo, fecha de inicio, fecha de término proyectada y presupuesto total, validando que el centro de costo ingresado no se repita en otro proyecto registrado. Cuando lo registra un Jefe de Proyecto, éste queda asignado automáticamente como responsable de la obra. El Administrador puede editar los datos de cualquier proyecto; el Jefe de Proyecto, sólo los de los proyectos a los que está asignado.»
- **Redacción propuesta RF-08:** «El sistema debe permitir al Administrador, en cualquier proyecto, y al Jefe de Proyecto, en los proyectos a los que está asignado, cargar y modificar el itemizado presupuesto base, requiriendo ingresar: código de partida, descripción del material, cantidad total presupuestada y unidad de medida. Cada alta, modificación o eliminación de una partida debe quedar registrada en el log de auditoría con el usuario y la fecha. No se puede eliminar una partida que tenga salidas de bodega imputadas.»
- **RF-09 y RF-10:** sin cambios (siguen siendo sólo del Administrador); conviene agregar a RF-09 «El Jefe de Proyecto no puede asignar ni quitar responsables».
- **RF-50:** agregar «modificaciones del itemizado de los proyectos» a la lista de acciones auditadas.

**CU-07 propuesto — Registrando nuevo proyecto en el sistema**
- **Nombre:** Registrando nuevo proyecto en el sistema.
- **Actores:** Administrador o Jefe de Proyecto.
- **Requerimiento:** RF-07.
- **Resumen:** El actor registra un nuevo proyecto de obra con sus datos básicos, incluido el centro de costo. Si el actor es Jefe de Proyecto, queda asignado como responsable de la obra.
- **Frecuencia:** Baja.
- **Precondiciones:** El usuario debe estar autenticado con rol Administrador o Jefe de Proyecto.
- **Flujo Principal:** El actor accede al módulo Proyectos y selecciona la opción "Registrar Nuevo Proyecto". El sistema despliega el formulario de ingreso con los campos obligatorios: nombre de la obra, cliente mandante, centro de costo, fecha de inicio, fecha de término proyectada y presupuesto total; si el actor es Administrador, despliega además la selección de Jefes de Proyecto responsables. El actor completa todos los campos obligatorios [Excepción 1], incluyendo el centro de costo, el cual el sistema valida que no se repita en otro proyecto registrado [Excepción 2]. El actor confirma el registro. El sistema almacena el proyecto en estado "En planificación" y, si el actor es Jefe de Proyecto, lo asigna como responsable. El proyecto queda disponible para la carga del itemizado.
- **Excepciones:**
  - Excepción 1: Algún campo obligatorio queda vacío. El sistema marca los campos faltantes y bloquea el guardado.
  - Excepción 2: El centro de costo ya existe en otro proyecto. El sistema bloquea el guardado e informa la duplicidad.
- **Poscondiciones:** El proyecto queda registrado en estado En planificación, con su responsable asignado si lo registró un Jefe de Proyecto, disponible para la carga del itemizado.
- **Dependencias:** —

**CU-08 propuesto — Cargando itemizado presupuestado de proyecto**
- **Nombre:** Cargando itemizado presupuestado de proyecto.
- **Actores:** Administrador o Jefe de Proyecto.
- **Requerimiento:** RF-08.
- **Resumen:** El actor carga o modifica las partidas del presupuesto (itemizado) de un proyecto. El Jefe de Proyecto sólo puede hacerlo en los proyectos a los que está asignado. Cada cambio queda en el log de auditoría.
- **Frecuencia:** Baja.
- **Precondiciones:** El proyecto debe estar registrado en el sistema. Si el actor es Jefe de Proyecto, debe estar asignado al proyecto.
- **Flujo Principal:** El actor accede al proyecto y selecciona la opción "Cargar Itemizado" [Excepción 1]. El sistema despliega una interfaz de ingreso de partidas con los campos: código de partida, descripción del material, cantidad total presupuestada y unidad de medida. El actor ingresa, modifica o elimina partidas completando los campos obligatorios [Excepción 2] [Excepción 3]. El actor confirma la carga. El sistema almacena las partidas vinculadas al proyecto, registra en el log de auditoría cada partida agregada, modificada o eliminada con el usuario y la fecha, y las deja disponibles para el cruce con las Solicitudes de Materiales.
- **Excepciones:**
  - Excepción 1: El actor es Jefe de Proyecto y no está asignado al proyecto. El sistema impide el acceso.
  - Excepción 2: Los campos obligatorios de una partida están incompletos. El sistema impide agregar la línea y marca los campos faltantes.
  - Excepción 3: El actor intenta eliminar una partida que ya tiene salidas de bodega imputadas. El sistema impide la eliminación e informa el motivo.
- **Poscondiciones:** El itemizado queda cargado y vinculado al proyecto, con cada cambio registrado en el log de auditoría.
- **Dependencias:** CU-07.

### 1.19 Lectura que el documento no menciona
- Bodega y Contabilidad pueden **leer** SM emitidas y OC (Bodega sin precios), para saber qué van a recibir y cruzar facturas. No modifican nada.
- Adquisiciones puede **consultar** el panel y los movimientos de bodega para cerrar la recepción de la OC (RF-35).
- **Propuesta:** agregar una línea en RF-26 o en el módulo de seguridad: «Bodega y Contabilidad consultan, sin modificarlas, las Solicitudes y Órdenes de Compra; Bodega lo hace sin precios.»

---

## 2. Funcionalidades nuevas que no están en el documento

Algunas existían antes de esta revisión y nunca se documentaron (N-01, N-05 a N-09); otras se agregaron ahora (N-02 a N-04, N-10).

**N-01 — RF nuevo (Módulo 5): Compra anticipada**
> El sistema debe permitir al rol Adquisiciones emitir una Orden de Compra sin Solicitud de Materiales asociada, indicando obligatoriamente el proyecto al que se imputa el gasto, el proveedor y los materiales con su cantidad y valor unitario. La Orden queda en estado Borrador y la autoriza el propio usuario de Adquisiciones.

**CU nuevo — Emitiendo compra anticipada**
- **Actores:** Adquisiciones. **Requerimiento:** N-01. **Frecuencia:** Baja.
- **Precondiciones:** Debe existir al menos un proyecto no finalizado y un proveedor activo con sus datos de facturación completos.
- **Flujo Principal:** El actor selecciona «Nueva compra anticipada». Indica proyecto, proveedor, costo de despacho y una o más líneas de material, cantidad y valor unitario [Excepción 1]. Confirma. El sistema crea la OC en Borrador con folio automático. El actor la aprueba y el sistema la envía al proveedor (RF-25).
- **Excepciones:** Excepción 1: No se ingresa ningún material, o faltan datos del proveedor. El sistema bloquea la emisión e indica qué falta.
- **Poscondiciones:** La OC queda imputada al proyecto y aparece en reportes y trazabilidad.

**N-02 — RF nuevo (Módulo 9): Notificaciones dentro del sistema**
> El sistema debe mostrar a cada usuario, en un indicador de la barra superior, las notificaciones que le generan los cambios de estado de sus Solicitudes de Materiales, el rechazo de Órdenes de Compra, las fallas de envío, los cambios de recepción y los préstamos de herramientas, permitiendo abrir cada aviso y marcarlos como leídos. Cada notificación se envía además al correo del usuario.

**N-03 — RF nuevo (Módulo 4): Rechazo y corrección de una SM**
> El sistema debe permitir al rol Adquisiciones rechazar una Solicitud de Materiales en estado "Emitida" o "En Cotización" que aún no tenga Orden de Compra, exigiendo un motivo que se notifica al Jefe de Proyecto. El Jefe de Proyecto puede devolver la SM rechazada a "Borrador", corregirla y volver a emitirla conservando su número correlativo.

**CU-64 (propuesto) — Rechazando Solicitud de Materiales**
- **Actores:** Adquisiciones. **Requerimiento:** N-03. **Frecuencia:** Baja.
- **Precondiciones:** La SM está en estado «Emitida» o «En Cotización» y no tiene OC generada.
- **Flujo Principal:** El actor abre la SM y selecciona «Rechazar solicitud». Ingresa el motivo [Excepción 1] y confirma. El sistema cambia la SM a «Rechazada» y notifica al Jefe de Proyecto con el motivo.
- **Excepciones:** Excepción 1: El motivo queda vacío. El sistema impide el rechazo.
- **Poscondiciones:** La SM queda «Rechazada»; el Jefe de Proyecto puede devolverla a Borrador para corregirla.
- **Dependencias:** CU-12, CU-15.

**N-04 — RF nuevo (Módulo 5): Gestión de envío manual de la OC.** Ver punto 1.6. Si el grupo prefiere no crear un RF, basta con la ampliación de CU-25.

**N-05 — RF nuevo (Módulo 5): Folio configurable de la OC**
> El sistema debe permitir al rol Adquisiciones fijar el número con que sale la próxima Orden de Compra, para continuar la numeración que la empresa usaba antes del sistema, impidiendo fijar un número ya utilizado o menor. Desde ese número el folio sigue en ascenso automático.

**N-06 — RF nuevo (Módulo 1): Carga del catálogo del proveedor desde Excel**
> El sistema debe permitir cargar o actualizar el listado de materiales de un proveedor desde una planilla .xlsx (código, descripción, unidad y precio), al registrarlo o desde su ficha, ofreciendo una planilla de ejemplo para enviar al proveedor.

**N-07 — RF nuevo (Módulo 9): Solicitud de acceso y aprobación de cuentas**
> El sistema debe permitir que una persona solicite una cuenta desde la pantalla de inicio de sesión indicando nombre, correo institucional y rol pedido; la cuenta queda pendiente y sin acceso hasta que el Administrador la aprueba (pudiendo corregir sus datos o rol) o la rechaza.

**N-08 — RF nuevo (Módulo 9): Mi perfil y solicitudes de cambio de datos**
> El sistema debe permitir a cada usuario editar su nombre, teléfono y foto. El cambio de correo, nombre de usuario o rol lo solicita el usuario y lo resuelve el Administrador.

**N-09 — RF nuevo (Módulo 2): Ficha del proyecto en PDF**
> El sistema debe permitir exportar a PDF la ficha de un proyecto con sus datos, itemizado y solicitudes asociadas.

**N-10 — Descarga protegida de archivos (Módulo 9, complementa RF-51, RF-14 y RNF-11).** Planos, adjuntos de SM y archivos de factura se descargan por una vista que revisa permisos; ya no por una URL pública. Propuesta para RF-51: «… y entregar los archivos sólo a usuarios con acceso al proyecto».

---

## 3. Cambios o agregados al stack tecnológico

| Componente | Documento | Sistema | Comentario |
|---|---|---|---|
| Backend | Django 4.2+, Python 3.10+ | Django 5.2.17, Python 3.11 | Cumple («4.2+»). Se sugiere escribir la versión real. |
| Base de datos | PostgreSQL 14+ | PostgreSQL 18 (desarrollo) | Cumple. |
| Hash de contraseñas | Bcrypt | PBKDF2-SHA256 | Ver 1.15. |
| API externa | Django REST Framework | **No instalado** | Los únicos endpoints JSON son los del buscador de materiales (`solicitudes/api.py`), en Django puro. Proponer «DRF: previsto para integración futura (no incluido en esta versión)». |
| Generación de PDF | — | **reportlab 4.2** | Agregar: OC (RF-24), ficha de proyecto y exportación de reportes (RF-45). |
| Excel | — | **openpyxl 3.1** | Agregar: exportación XLSX (RF-45) e importación del catálogo del proveedor (N-06). |
| Imágenes | — | **Pillow 10.4** | Agregar: foto de perfil (`ImageField`). |
| Configuración | — | **python-dotenv** | Agregar: lectura del `.env`. |
| Driver BD | — | **psycopg2-binary** | Agregar. |
| Servidor | «servidor M5 existente» | **gunicorn + nginx** (VM appliance Ubuntu) | Agregar; nginx atiende HTTPS (`despliegue/nginx-m5.conf`) y la descarga protegida (X-Accel-Redirect). |
| Correo | — | SMTP configurable por `.env` | Agregar: envío de OC (RF-25), activación (RF-49), recuperación (RF-53), notificaciones. |

No se agregaron librerías nuevas en esta revisión: todo lo nuevo (notificaciones,
bloqueo por intentos, reducción de imágenes) usa Django y JavaScript nativos.

---

## 4. Errores o inconsistencias encontradas en los documentos

1. **CU-48 (Autenticándose):** el *Resumen* es copia del CU-49 («El Administrador crea una nueva cuenta…»). Propuesta: ver el CU-48 completo en el punto 1.10.
2. **CU-13:** la *Poscondición* contiene una excepción («El actor deja el campo de Justificación vacío. El sistema bloquea…») y *Excepciones* dice «—». Moverla a Excepción 1 y escribir como poscondición «La línea queda registrada con su justificación».
3. **CU-31 (Préstamo):** la *Precondición* es copia del CU-30 («Se ha confirmado el registro de una entrada o salida»). Propuesta: «La herramienta debe estar disponible en bodega.»
4. **CU-35:** la *Excepción 1* describe el flujo principal (stock ≤ mínimo → alerta). La excepción real sería «el stock queda sobre el mínimo: no se genera alerta».
5. **CU-22:** la *Excepción 1* («El actor rechaza el borrador») es parte del flujo principal. La excepción es «el rechazo sin motivo se bloquea».
6. **RF-51 vs CU-54 / CU-58 / CU-59:** RF-51 da la carga de archivos a «Administrador y Jefe de Proyecto»; CU-54, CU-58 y CU-59 agregan «Adquisición, Contabilidad». El sistema sigue los CU (más amplio). Unificar.
7. **RF-51 vs RF-57:** RF-51 fija una lista cerrada de tipos de documento y RF-57 dice que el catálogo es configurable. Propuesta RF-51: «… tipo de documento, seleccionado del catálogo configurable (RF-57), que inicialmente incluye Contrato, Especificación Técnica, Plano 2D, Plano 3D, Fotografía y Videos.»
8. **«Administrador» y «Administración»** se usan indistintamente (RF-07 vs RF-30, RF-38, RF-57, CU-60). Es un solo rol en el sistema. Usar un único nombre y definirlo en el glosario.
9. **RF-15 «Rechazada»** sin actor ni CU que la produzca (ver 1.2 y N-03).
10. **RF-12 «Al confirmar»** implica un estado previo que no está en RF-15 (ver 1.1).
11. **RF-26 vs RF-35:** ambos asignan la cantidad recibida (Bodega registra, Adquisiciones «indica»). Ver 1.7.
12. **RF-58:** «catálogo maestro de materiales, independiente del catálogo de herramientas» y a la vez «diferenciar ambos tipos mediante un atributo de clasificación». Son dos ideas distintas (dos catálogos o uno con clasificación). El sistema usa **un catálogo con el atributo Tipo** (como dice CU-61). Propuesta: «… un catálogo maestro único de materiales y herramientas, diferenciados explícitamente mediante un atributo de clasificación …».
13. **Dependencias entre CU con sentido mezclado:** a veces listan el CU *incluido* (CU-12 → CU-13, CU-17 → CU-18, CU-49 → CU-52, CU-61 → CU-62) y a veces el *prerrequisito* (CU-20 → CU-19, CU-23 → CU-22). Conviene separar «Incluye/Extiende» de «Requiere».
14. **CU-24** limita la exportación del PDF a Adquisiciones, pero RF-24 no restringe el rol; el sistema permite también al Jefe de Proyecto (sólo de sus obras). Unificar.
15. **RF-20:** el estado se llama «En Cotización» cuando la cotización ya terminó (ver 1.5).
16. **RNF-02** pide sincronización offline general y RF-55/56 sólo cubren archivos (ver 1.13).
17. **Stack:** «Bcrypt» y «DRF» no calzan con la implementación (ver sección 3).
18. **Glosario — términos que faltan:** **SM** (Solicitud de Materiales; la sigla se usa en todo el documento y no está definida), Cotización, Línea de cotización, Partida, Centro de costo, Correlativo / Folio, Guía de despacho, Borrador, Tolerancia de facturación, Borrado lógico (*soft delete*), Bitácora / log de auditoría, Notificación, Compra anticipada, Herramienta / activo fijo, Bodega central.
19. **Glosario — definición imprecisa:** «API REST: permite la comunicación entre la vista y el controlador» — en la arquitectura real las vistas no se comunican con el controlador por API REST. Propuesta: «Interfaz para integrar el sistema con otros sistemas mediante solicitudes web (prevista para integración futura).»

---

## 5. Roles o estados nuevos, o con otro nombre

### Roles

| Documento | Sistema (código / pantalla) | Acción sugerida |
|---|---|---|
| Administrador / Administración | `ADMIN` / «Administrador» | Unificar el nombre en el documento. |
| Adquisiciones | `ENCARGADO_ADQUISICIONES` / «Encargado de Adquisiciones» | Usar «Encargado de Adquisiciones» o anotar la equivalencia. |
| Bodega | `BODEGUERO` / «Bodeguero» | Usar «Bodeguero» o anotar la equivalencia. |
| Jefe de Proyecto | `JEFE_PROYECTO` | Sin cambios. |
| Contabilidad | `CONTABILIDAD` | Sin cambios. |

No hay roles nuevos.

### Estados

| Entidad | Documento | Sistema | Diferencia |
|---|---|---|---|
| Solicitud de Materiales | Emitida, En Cotización, OC Generada, Rechazada, Entregada parcialmente, Entregada | **Borrador**, Emitida, En cotización, OC generada, Rechazada, Entregada parcialmente, Entregada | Se agrega Borrador (1.1). Se eliminaron los estados internos «Enviada» y «Aprobada» del sistema anterior (migrados a «Emitida»). |
| Proyecto | En planificación, En ejecución, Finalizado | Igual | Se eliminó «Suspendido» (migrado a «En planificación»). |
| Cotización | Pendiente | Pendiente, **Con líneas aprobadas**, Descartada | Estados de la cabecera; las líneas usan Pendiente / Aprobada / Descartada como el documento. |
| Orden de Compra | Borrador, Aprobada, Rechazada, Enviada, Recibida, Recepción Parcial, No Recibida + marca Facturada | Igual | Sin diferencias. |
| Factura | (no definidos) | **Registrada**, **Bloqueada** | Agregar al documento (1.9). |
| Préstamo de herramienta | Prestada, Disponible en Bodega | Prestada, **Devuelta / disponible en bodega** | Sólo cambia la etiqueta. |
| Cuenta de usuario | Habilitada / Deshabilitada | Activa / Inactiva + **Pendiente de aprobación** | Agregar el pendiente si se documenta N-07. |
| Notificación | — | Leída / No leída | Nuevo (N-02). |
