# Entrega 3 — Los cuatro CU que faltaban

**Se aplica encima de la entrega 2**, no la reemplaza. Verificado con **177 tests**
(la entrega 2 dejó 118), todos en verde contra PostgreSQL 16 y Django 5.2.17.

## Un arreglo extra: el `.env` que dejaba la VM caída

`config/settings.py` ahora **deduce `CSRF_TRUSTED_ORIGINS` de `ALLOWED_HOSTS`**.

Esa era la línea que se corrompía al pegarla por SSH (los `http://` se convertían
en `http//` y las comas se comían), y el sistema caía con un `4_0.E001` que no
explica nada. Con esto el `.env` necesita **una sola** variable de hosts:

```
ALLOWED_HOSTS=26.213.46.53,192.168.3.37,127.0.0.1
```

y los orígenes salen solos (`http://` y `https://` de cada uno). Si algún día
hace falta forzar un origen distinto —un dominio, HTTPS con otro puerto— se
escribe `CSRF_TRUSTED_ORIGINS` en el `.env` y esa manda.

**En la VM hay que borrar la línea vieja**, que quedó corrupta:

```bash
sudo sed -i '/^CSRF_TRUSTED_ORIGINS/d' /opt/m5/app/.env
```

## Cómo aplicarlo

```powershell
python manage.py migrate
python manage.py seed_demo
python manage.py test
python manage.py runserver
```

`seed_demo` ahora también carga el catálogo de tipos de documento y deja la
bitácora de auditoría poblada, así las pantallas nuevas no aparecen vacías
cuando vayas a sacar las capturas.

---

## CU-13 — Justificando exceso de itemizado

**Dónde:** Solicitudes → Nueva solicitud (y también al agregar ítems a un borrador).

El modelo ya tenía `partida`, `justificacion` y `excede_itemizado`, y el formulario
ya exigía la justificación. Lo que faltaba era que **el campo `partida` nunca se
dibujaba en la pantalla de nueva solicitud**, así que la regla no se podía activar
nunca. Por eso no te salía.

Ahora la línea tiene una columna **Partida del itemizado**. El selector se llena
por API al elegir el proyecto (`/solicitudes/api/partidas/`), y cada opción trae
su **saldo disponible**. Cuando escribes una cantidad mayor a ese saldo:

```
Partida del itemizado
[OG-02 · Albañilería (saldo 20 m2) ▾]
⚠ Excede el itemizado. Pides 35 m2 y la partida OG-02 tiene 20 m2 disponible.

Justificación
[Rectificación de metraje en terreno...]
```

La alerta salta **mientras escribes**, no al guardar. Y el servidor la exige igual
aunque alguien desactive el JavaScript: sin justificación, la línea no se confirma
y el formulario devuelve el error con el código de la partida y los números.

Una partida de otro proyecto se descarta sola al guardar (si cambias de proyecto a
mitad de camino, no queda colgada una partida ajena).

**Para la captura:** el proyecto demo tiene `OG-02 · Albañilería` con **saldo 20**.
Pide 35 y la alerta aparece.

---

## CU-54 — Almacenando archivo y clasificándolo por tipo de documento

**Dónde:** Proyectos → (un proyecto) → **Documentos del proyecto**.

Dos modelos nuevos:

- **`TipoDocumento`** — catálogo administrable: Plano, Contrato, Permiso municipal,
  Cotización, Factura, Acta de recepción, Informe técnico. Está en
  Proyectos → *Catálogo de tipos* (`/proyectos/tipos-documento/`) y en el admin.
- **`ArchivoProyecto`** — el archivo contra el proyecto, con **tipo obligatorio**,
  nombre, observaciones, quién lo subió y cuándo.

Es catálogo y no una lista fija en el código porque cada obra llega con su propia
papelería, y porque el caso de uso pide explícitamente "seleccionar el tipo desde
un catálogo".

Lo suben Administrador, Adquisiciones, Contabilidad y Jefe de Proyecto. Formatos:
pdf, jpg, png, dwg, xlsx, docx · máx. 10 MB.

### Excepción 1, que es lo que te van a pedir mostrar

Son dos caras de la misma regla:

1. **Sin tipo seleccionado** → no se almacena nada y sale
   *«Debes clasificar el archivo: selecciona un tipo de documento.»*
2. **Catálogo vacío** → el formulario de carga ni siquiera se dibuja; en su lugar
   sale un aviso amarillo con el enlace a cargar el catálogo.

**Para la captura de la excepción:** entra a *Catálogo de tipos*, desactiva todos
(o bórralos desde el admin) y vuelve a la ficha del proyecto.

---

## CU-53 — Registrando en bitácora de auditoría

**Dónde:** barra superior → **Auditoría** (`/auditoria/`). La ven Administración y
Contabilidad.

App nueva `auditoria` con el modelo **`RegistroAuditoria`** y una única función de
escritura, `registrar(usuario, accion, descripcion, referencia)`.

Cada línea guarda **quién, cuándo (fecha y hora), qué acción y sobre qué**. Las
acciones auditables son exactamente las que enumera el RF-50:

| Módulo | Qué se registra |
|---|---|
| Inventario | entradas, salidas, mermas, devoluciones, préstamo y devolución de herramientas |
| Solicitudes | emisión, aprobación y rechazo de SM |
| Adquisiciones | emisión, aprobación y envío de OC |
| Facturación | recepción, bloqueo y desbloqueo de facturas |
| Usuarios | alta, aprobación, rechazo y modificación de cuentas |

**Excepción 1:** una acción que no está en ese catálogo **no genera registro**.
`registrar()` valida la acción y devuelve `None` sin escribir nada. Callar es lo
correcto: una bitácora con entradas inventadas no sirve como evidencia.

Dos decisiones que vale la pena que sepas defender si te preguntan:

- **Los movimientos de bodega se capturan por señal** (`post_save`), no llamando a
  `registrar()` en cada una de las cuatro pantallas que los crean. Así ningún
  movimiento puede existir sin su línea de auditoría, ni siquiera uno creado desde
  el admin de Django. Las emisiones de SM/OC, las facturas y las cuentas sí se
  auditan desde sus vistas, porque ahí lo auditable es el cambio de estado y quién
  lo hizo — dato que el modelo no guarda.
- **La bitácora sólo se lee.** No hay pantalla de edición, y en el admin están
  desactivados agregar, cambiar y borrar. Si se pudiera retocar, dejaría de servir
  para lo que existe.

La cuenta del usuario se puede dar de baja y la bitácora igual sigue diciendo quién
fue: el nombre se guarda además en texto.

**Filtros de la pantalla:** módulo, acción, usuario, rango de fechas y búsqueda
libre sobre descripción, referencia y nombre. Paginada de a 50.

---

## CU-47 — Buscando trazabilidad de material u Orden de Compra

**Dónde:** barra superior → **Trazabilidad** (`/adquisiciones/trazabilidad/`).

Una sola caja de búsqueda con **tres puertas de entrada**, porque la pregunta es
siempre la misma pero cada uno la entra por donde tiene el dato a mano:

- `SM-000003` → la cadena de esa solicitud
- `OC-000001` → la misma cadena, con la OC que buscaste marcada
- `cemento` → los materiales que calzan, con lo pedido, los movimientos y el stock
  de hoy, más la cadena de cada solicitud donde aparece

La cadena se muestra como línea de tiempo de cinco eslabones:

```
1 · Solicitud de material    SM-000003 · Edificio Residencial Las Condes
2 · Cotizaciones             Ferretería El Constructor · Aceros del Sur
3 · Órdenes de compra        OC-000001 Ferretería · Enviada · $577.000
4 · Recepción en bodega      12/09 14:30 · Entrada 80 saco de Cemento (bodega)
5 · Facturas                 Factura F-9001 · $577.000 · Registrada
```

Cuando la cadena está cortada **lo dice**, en vez de dejar el hueco mudo:
*«Sin orden de compra emitida»*, *«No se ha recibido nada todavía»*, *«Sin factura
asociada»*. Eso es lo que te deja ver de un vistazo dónde se quedó pegada una compra.

Una búsqueda sin resultados tampoco muestra una tabla vacía: dice *«Sin resultados
para X»*.

---

## Detalle técnico

**Archivos nuevos**

| Archivo | Qué es |
|---|---|
| `auditoria/` (app completa) | CU-53: modelo, `registrar()`, señales, vista, urls, admin |
| `adquisiciones/trazabilidad.py` | CU-47: la búsqueda y el armado de la cadena, aparte de las vistas |
| `templates/auditoria/bitacora_list.html` | pantalla de la bitácora con filtros |
| `templates/adquisiciones/trazabilidad.html` | pantalla de trazabilidad |
| `templates/proyectos/tipodocumento_list.html` | catálogo de tipos de documento |

**Migraciones**: `proyectos/0005_tipodocumento_archivoproyecto` y
`auditoria/0001_initial`.

**Tests nuevos: 59** (11 del CU-13, 13 del CU-54, 23 del CU-53, 12 del CU-47).

## Lo que queda pendiente

- **Exportar la bitácora a CSV/PDF** para adjuntarla a una auditoría externa. Los
  filtros ya están; falta el botón.
- **Versionado de archivos del proyecto** (plano rev. B → rev. C). Hoy se sube uno
  nuevo y conviven los dos; el nombre los distingue, no el sistema.
