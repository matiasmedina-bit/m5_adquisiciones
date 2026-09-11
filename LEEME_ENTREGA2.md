# Entrega 2 — Proveedor primero en la solicitud

**Se aplica encima de la entrega 1**, no la reemplaza. Verificado con **118 tests**
(entrega 1 dejó 100), todos en verde contra PostgreSQL 16 y Django 5.2.17.

## Cómo aplicarlo

Descomprime sobre la carpeta del proyecto y después:

```powershell
python manage.py migrate
python manage.py test
python manage.py runserver
```

## La línea de la solicitud, ahora

```
PROVEEDOR          MATERIAL               CANTIDAD     VALOR      DETALLE
Ferretería Andes ▾ cemen|                 20  saco    $ 5.490    para la losa 3er piso
                   ┌────────────────────────────────┐
Lo ofrecen:        │ CEM-001 Cemento 25kg    $5.490 │
[Comercial Sur     │ Ferretería Andes · saco · 30 d │
 · $5.200]         │ CEM-004 Cemento alta    $6.900 │
                   └────────────────────────────────┘
```

**En los dos sentidos, como pediste:**

- **Eliges proveedor** → el buscador queda restringido a su catálogo. Si después
  cambias de proveedor, la elección anterior se descarta sola (era de otro catálogo).
- **Escribes el material primero** → bajo el selector de proveedor aparece
  «Lo ofrecen: …» con cada proveedor y su precio, **ordenados del más barato al más
  caro**. Un clic y la línea queda completa con ese proveedor.

Al elegir un ítem del catálogo se completan solos la **unidad**, el **valor** y el
**proveedor**. El valor queda editable: si negociaste otro precio, lo escribes encima.

Si el material no está en ningún catálogo, escribes el nombre y se agrega igual —
el comportamiento de antes no se perdió.

## La unidad dejó de pedirse

Tenías razón: nadie debería escribir "kg" a mano. Ahora se hereda del catálogo y se
muestra **pegada a la cantidad** (`20 saco`, `5 caja`), en gris, como contexto y no
como campo. Esa columna la ocupa **Detalle**: texto libre opcional para "para la losa
del 3er piso" o "urgente, obra parada".

El campo sigue existiendo en la base porque la orden de compra lo imprime; lo que
cambió es que ya no se le pide a una persona.

## El flujo del borrador

- El botón **Guardar** pasó a ser **Siguiente →**, con una línea que explica que la
  solicitud queda en borrador.
- En el borrador, el panel de Acciones ahora ofrece **Editar datos generales** y
  **Enviar para aprobación**.
- **Total estimado** en vivo mientras cargas las líneas, y también en el detalle.
  Con esto el Jefe de Proyecto aprueba sabiendo el monto, que antes no pasaba.

### Un bug que apareció en el camino

El panel de Acciones te salía vacío porque las plantillas comparaban
`user.rol == 'ENCARGADO_ADQUISICIONES'` a mano, y tú entras como **Administrador**.
El decorador de permisos sí deja pasar al ADMIN, pero el botón nunca se dibujaba —
así que el sistema te dejaba enviar la solicitud pero no te mostraba cómo.

Ahora la vista calcula `puede_gestionar` y `puede_resolver` con la misma regla que
`usuarios.permisos` (ADMIN siempre puede) y las plantillas usan eso. Corregido en el
listado de materiales, en el formulario de agregar, en las acciones y en la cotización.

## Detalle técnico

**`SolicitudDetalle`** gana `proveedor`, `proveedor_material`, `valor_unitario` y
`detalle`, más las propiedades `valor_total` y `condicion_pago`.
**`SolicitudMaterial`** gana `total_estimado` y `proveedores_sugeridos`.

**`ProveedorMaterial`** gana un FK opcional a `Material` que se completa solo la
primera vez que ese ítem se usa en una solicitud (`resolver_material()`). Sin eso,
cada solicitud crearía un material nuevo y el catálogo general terminaría lleno de
duplicados: "Cemento 25kg", "Cemento Portland 25 kg", "cemento portland"…

**`solicitudes/api.py`** — dos endpoints JSON, ambos con control de rol y tope de 12
resultados:

| Endpoint | Para qué |
|---|---|
| `api/materiales/?q=&proveedor=` | Buscar material, restringido al proveedor si hay uno |
| `api/proveedores/?q=` ó `?material=` | Quién ofrece ese material y a qué precio |

**`templates/solicitudes/_buscador_material.html`** — el buscador, compartido por la
pantalla de creación (varias filas) y la de detalle (una fila). Sin librerías externas:
delega eventos en `document`, así las filas que se agregan después funcionan igual.

## Lo que queda pendiente

- **Precargar la cotización** con el proveedor y los precios de la solicitud. Ya están
  los datos para hacerlo; falta la pantalla.
- **Llevar la condición de pago del material a la orden de compra.** Ahora sí es
  posible, porque la línea ya guarda el `proveedor_material`.
