# Entrega 4 — Incrementos 3 y 4, y el flujo corregido

Con esto el sistema queda **completo**: los 60 RF del Documento 0 implementados.
Verificado con **288 tests** (la entrega 3 dejó 177), todos en verde contra
PostgreSQL 16 y Django 5.2.17.

## Cómo aplicarlo

```powershell
python manage.py migrate
python manage.py seed_demo
python manage.py test
python manage.py runserver
```

Trae **seis migraciones nuevas**, así que el `migrate` no es opcional. Una de
ellas rellena el código interno de los materiales que ya existían.

---

# Parte 1 — Los cortes de flujo que me pediste revisar

Antes de agregar nada, recorrí el sistema como los cinco roles buscando dónde se
quedaba trabajo atascado. Aparecieron tres cortes duros en la cadena de estados.
Los tres estaban en producción y ninguno daba error: simplemente dejaban algo
detenido sin decir por qué.

### 1. Una OC a un proveedor sin correo quedaba muerta

El cambio de estado `APROBADA → ENVIADA` estaba **dentro** del `if` que verificaba
el correo del proveedor. Si el proveedor no tenía correo registrado, el Jefe
aprobaba, salía un aviso, y la orden se quedaba en `APROBADA` para siempre:

- Bodega no la veía en el selector de recepción → no podía recibir el material.
- Contabilidad no la veía en el selector de factura → no podía facturarla.
- La solicitud quedaba en `OC_GENERADA` esperando algo que nunca iba a llegar.

**Arreglado.** La orden se da por emitida aunque el correo falle, y el sistema te
dice que hay que hacérsela llegar por otra vía. El correo es el medio de aviso,
no el acto de emitir.

### 2. «No recibida» era un estado terminal

Cuando el Encargado marcaba una OC como no recibida —el caso normal cuando el
proveedor no llegó a tiempo— no había forma de volver atrás. Si el proveedor
entregaba al día siguiente, el sistema no lo dejaba registrar.

**Arreglado.** Una OC no recibida acepta la entrega atrasada, y la solicitud
vuelve a `OC_GENERADA` para que se vea que sigue pendiente en vez de quedarse muda.

### 3. Una solicitud rechazada no se podía corregir

El Jefe rechazaba por un detalle —una cantidad mal puesta, una justificación que
faltaba— y el Encargado tenía que **rehacer la solicitud completa**: perdía el
correlativo, las líneas y los adjuntos. La Orden de Compra ya tenía su vuelta a
borrador; la Solicitud no, y no había razón para la asimetría.

**Arreglado.** Ahora el rechazo **pide un motivo** (que el Encargado ve en pantalla)
y hay un botón «Corregir y volver a enviar» que la devuelve a borrador conservando
todo.

### Y además

| Qué pasaba | Quién lo sufría | Arreglo |
|---|---|---|
| Desde la trazabilidad, los enlaces a la solicitud y la OC daban 403 | Bodega y Contabilidad | Lectura abierta; las acciones de escritura siguen protegidas |
| Desde una factura no se podía abrir la OC a validar | Contabilidad | Lo mismo |
| Tenía permiso para subir documentos al proyecto pero no había cómo llegar | Contabilidad | «Proyectos» en la barra y en el listado |
| El botón «Editar datos» no aparecía | Administrador | La plantilla comparaba el rol a mano y se olvidaba de ADMIN |
| Siete acciones que cambian estado viajaban por GET | Todos | Ahora son formularios POST con CSRF |
| «Inactivar proveedor» era un enlace sin confirmación | Adquisiciones | Formulario POST con confirmación |
| El inicio salía vacío | Bodega y Contabilidad | Métricas y módulos propios de cada rol |

**Verificación:** un recorrido automático de tres niveles de profundidad desde el
inicio, con cada uno de los cinco roles, abriendo todos los enlaces visibles.
**Cero enlaces rotos** en las 176 páginas que se alcanzan.

---

# Parte 2 — Incremento 3

## CU-60 (RF-57) — Parámetros generales del sistema
**Dónde:** barra superior → **Parámetros** (sólo Administración).

Los cuatro valores que gobiernan las validaciones automáticas, configurables sin
tocar código:

- **Tolerancia de facturación** — cuánto puede diferir una factura de su OC antes
  de bloquearse.
- **Stock mínimo por defecto** — el que toma un material nuevo si nadie le pone uno.
- **Umbral de tamaño de archivo** — sobre cuánto el sistema advierte al subir.
- **Catálogo de tipos de documento** — resumen y acceso a su pantalla.

Antes la tolerancia vivía en `settings.py` y en el `.env`: para cambiarla de 5% a
8% había que entrar por SSH a la VM, editar un archivo y reiniciar gunicorn. Eso
no es configurable, es modificable por quien tenga la llave del servidor.

Excepción 1: un valor fuera de rango o no numérico no se guarda y el campo queda
marcado. El cambio queda en la bitácora de auditoría.

## CU-42 a CU-46 (RF-41 a RF-45) — Módulo de reportes
**Dónde:** barra superior → **Reportes**.

| Reporte | Qué muestra |
|---|---|
| **Consumo consolidado por proyecto** | Material por material: solicitado, despachado, pendiente, costo unitario y total |
| **Desviación presupuestaria** | Itemizado original vs. comprado y consumido, con gráfico, partidas sobregiradas marcadas |
| **Mermas y pérdidas** | Material perdido, filtrable por proyecto y fechas, **valorizado en pesos** |
| **Historial de compras por proveedor** | Volumen de órdenes y monto total por periodo |

**Los cuatro se exportan a Excel y a PDF** con un clic (CU-46). La exportación es
una sola implementación para los cuatro, no cuatro: todos los reportes salen con
la misma estructura, así que el exportador no sabe cuál está imprimiendo.

Detalles que vale la pena que sepas defender:

- **El Jefe de Proyecto sólo ve sus proyectos.** No es un filtro de pantalla, es
  el queryset — tampoco llega a otro escribiendo el id en la URL.
- **Solicitado y despachado son cosas distintas** a propósito: la diferencia es
  material aprobado que sigue en bodega, y es justo lo que el Jefe quiere ver.
- **Un borrador no es una compra.** El historial excluye borradores y rechazadas;
  si no, inflaría el reporte con plata que nunca salió.
- **El gráfico se dibuja con CSS, sin librería externa.** El appliance corre en la
  red interna de la constructora y puede no tener salida a internet.
- **Un reporte vacío lo dice con palabras.** «No hay mermas registradas con estos
  filtros. Es una buena noticia, no un error del reporte.»

## CU-52 (RF-49) — Enlace de activación de cuenta
Al crear una cuenta, el Administrador ya **no elige la contraseña**: el sistema
manda un enlace temporal al correo institucional para que el usuario la defina.

Que el administrador no conozca la clave no es comodidad: una contraseña que pasó
por un tercero deja de servir como prueba de quién hizo qué, y la bitácora de
auditoría depende de eso.

Excepción 1: si el envío falla se reintenta, y si persiste se le avisa al
Administrador que creó la cuenta. Hay botón para reenviar el enlace.

## CU-55 (RF-52) — Cierre de sesión por inactividad
30 minutos exactos. La clave está en que el reloj cuenta desde la **última
actividad**, no desde el login: sin eso el sistema echaría a alguien que está
trabajando (que es la Excepción 1 del caso de uso).

## CU-56 (RF-53) — Recuperación de contraseña
«¿Olvidaste tu contraseña?» en la pantalla de inicio de sesión.

Excepción 1: el mensaje es **el mismo exista o no la cuenta**. Decir «ese correo
no está registrado» le confirmaría a un atacante qué direcciones tienen cuenta.

## CU-57 (RF-54) — Advertencia de tamaño de archivo
Sobre el umbral configurado, el sistema **advierte y ofrece comprimir**, pero no
prohíbe: hay que marcar «subir de todas formas». Un plano pesado a veces tiene
que subir pesado.

## CU-58 y CU-59 (RF-55, RF-56) — Edición offline con bloqueo
En los documentos del proyecto: **«Editar offline»** bloquea el archivo a tu
nombre; cuando subes la versión editada se libera y sube el número de versión.

- Si otro lo tiene, el sistema dice **quién** y desde cuándo. Decir sólo «está
  bloqueado» obliga a preguntar por el pasillo.
- La versión editada tiene que volver **en el mismo formato**: cambiar un `.dwg`
  por un `.pdf` no es una versión nueva, es otro documento.
- El Administrador puede destrabar un archivo que quedó tomado por alguien que
  ya no está en la empresa.

---

# Parte 3 — Incremento 4: el catálogo maestro

## CU-61 (RF-58) — Clasificación explícita
Al registrar un ítem, el selector **no viene preseleccionado**: hay que indicar si
es material o herramienta. Un desplegable que ya trae «Material consumible»
marcado no es una decisión, es un descuido esperando a pasar — y de ese campo
dependen el préstamo de herramientas, el stock mínimo y el prefijo del código.

Se agregó **categoría** (áridos, cementos, fierro, albañilería, eléctrica…) y una
herramienta exige su código de activo, sin el cual no se puede prestar.

## CU-62 (RF-59) — Código interno único
Cada ítem recibe un código propio de la empresa al crearse: `MAT-00001`,
`HER-00001`. Es **independiente del código que use cada proveedor** para el mismo
material en sus cotizaciones — ese vive en el catálogo del proveedor.

El código no cambia nunca al editar: se imprime en órdenes de compra y guías.
Si el correlativo colisiona, avanza al siguiente libre (Excepción 1).

## CU-63 (RF-60) — Búsqueda y filtros
El catálogo ahora filtra por los cinco ejes que pide el requisito: **código,
descripción, categoría, disponibilidad y ubicación**, combinables entre sí. La
caja de búsqueda cubre código y descripción a la vez, y el listado pagina de a 40.

Disponibilidad distingue «con stock», «agotado» y «bajo stock mínimo», que no es
lo mismo que activo/inactivo.

---

## Detalle técnico

| Archivo | Qué es |
|---|---|
| `reportes/` (app completa) | CU-42 a CU-46: consultas, exportación, vistas |
| `reportes/consultas.py` | Las cuatro consultas, con una estructura común |
| `reportes/exportar.py` | XLSX y PDF, una implementación para los cuatro |
| `usuarios/correos.py` | CU-52: enlace de activación con reintentos |
| `templates/registration/password_reset_*` | CU-56: las cuatro pantallas |
| `templates/usuarios/parametros.html` | CU-60 |

**Migraciones nuevas: 6.** `inventario` 0004-0006 (categoría y código interno, con
el relleno de los existentes en medio), `usuarios` 0004, `proyectos` 0006,
`solicitudes` 0005, `auditoria` 0002.

**Tests nuevos: 111** — 36 de reportes, 21 de usuarios y sesión, 14 de archivos,
19 del catálogo maestro, 21 de los cortes de flujo.

## Lo que queda pendiente

- **Bootstrap se carga desde un CDN.** Si el servidor de M5 queda sin salida a
  internet, el sistema funciona pero se ve sin estilos. Conviene bajar Bootstrap
  a `static/` antes de instalar en producción. Los reportes nuevos ya no dependen
  de ningún CDN.
- **Exportar la bitácora de auditoría** a CSV/PDF. Los filtros están, falta el botón.
- **`createsuperuser` no pregunta el rol** y crea al administrador como BODEGUERO.
  Se corrige con `REQUIRED_FIELDS = ["email", "rol"]` en `usuarios/models.py`.
