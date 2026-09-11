# Entrega 1 — Proveedores, usuarios y ficha de proyecto

Cambios sobre `m5_adquisiciones` verificados con **100 tests** (antes 66), todos en verde
contra PostgreSQL 16 y Django 5.2.17.

## Cómo aplicarlo

Descomprime este paquete **sobre la carpeta del proyecto**, respetando las rutas. Después,
en tu PC:

```powershell
git status                       # revisa qué cambió antes de nada
pip install -r requirements.txt  # agrega openpyxl
python manage.py migrate
python manage.py test
python manage.py runserver
```

Cuando lo pruebes y te guste, lo commiteas y lo mandas a la VM con el mismo
`git archive` + `scp` de siempre. En la VM:

```bash
/opt/m5/venv/bin/pip install -r /opt/m5/app/requirements.txt
cd /opt/m5/app && /opt/m5/venv/bin/python manage.py migrate
/opt/m5/venv/bin/python manage.py collectstatic --noinput
sudo systemctl restart gunicorn
```

## Qué cambió

### 1 · El registro de proveedor ya no pide condición de pago

`ProveedorForm` perdió ese campo. En su lugar aparece **Catálogo del proveedor (Excel)**,
con un botón para descargar la plantilla y una tabla de ejemplo de las columnas.

El campo `condicion_pago` sigue existiendo en el modelo `Proveedor`, pero pasó a ser
un **valor por defecto**: se usa sólo cuando el material no define el suyo. Así ninguna
orden de compra ya emitida se rompe y no hubo que migrar datos.

### 2 · Precio y condición de pago por material

`ProveedorMaterial` tiene dos campos nuevos:

- `precio` — valor unitario en CLP (opcional, queda en 0 si no se conoce)
- `condicion_pago` — si va vacío, hereda la del proveedor

La propiedad `condicion_pago_efectiva` resuelve cuál aplica. En la ficha del proveedor
se ve la condición real y, cuando es heredada, se indica «(del proveedor)».

### 3 · Carga del catálogo desde Excel

`proveedores/catalogo_excel.py`. Lee `.xlsx` con openpyxl y es deliberadamente tolerante,
porque las planillas de los proveedores nunca vienen iguales:

- Busca la fila de encabezados **en las primeras 10 filas** (las planillas traen logo y
  datos de contacto arriba).
- Reconoce sinónimos: `Cod.`, `SKU`, `Referencia` · `Detalle`, `Material`, `Glosa` ·
  `U.M.`, `Unidad` · `Valor unitario`, `Neto` · `Forma de pago`.
- Entiende precios chilenos: `$ 1.234.500` → `1234500`.
- Mapea condiciones escritas libremente: `60 dias corridos` → `60_DIAS`.
- Sólo **Código** y **Descripción** son obligatorias.

**Qué hace con los datos:** un código que ya existe se actualiza, uno nuevo se agrega.
**Nunca borra nada** (RF-06: rompería el historial de órdenes de compra). Con la casilla
«reemplazar», lo que no venga en la planilla queda marcado como *no disponible*.

Se puede cargar desde dos lugares: al registrar el proveedor, o desde su ficha en
cualquier momento (los proveedores mandan listas nuevas). Devuelve un resumen —
cuántos creados, actualizados, omitidos — y explica fila por fila qué se omitió y por qué.

También hay una **plantilla descargable** (`/proveedores/plantilla-catalogo.xlsx`) con los
encabezados y dos filas de ejemplo, para enviársela al proveedor.

### 4 · El listado de proveedores muestra el catálogo

Se fue la columna «Cond. pago» y entró **Materiales**, con el número de materiales
disponibles (o «sin catálogo» en ámbar, que es el dato accionable). El filtro pasó a ser
*con materiales cargados / sin catálogo*, y la búsqueda ahora también entra **dentro del
catálogo**: buscar "cemento" te devuelve los proveedores que lo venden.

### 5 · Ficha del proyecto en PDF

`proyectos/pdf.py` + botón **Exportar PDF** en el detalle del proyecto. Mismo criterio
gráfico que la Orden de Compra: logo, cabecera con los datos de M5, azul institucional.

Incluye: mandante destacado, centro de costo, jefe de proyecto, estado, fechas,
presupuesto, el **itemizado completo** con saldos (en rojo los sobregirados) y las
**solicitudes asociadas**. Funciona aunque el proyecto no tenga itemizado ni jefe.

### 7 · Usuarios sin aprobar no aparecen para asignarles nada

Helper nuevo `usuarios.models.usuarios_asignables(rol)`: filtra por `estado=True` y
`pendiente_aprobacion=False`. Aplicado en el selector de jefe de proyecto, en los
movimientos de inventario, en los préstamos de herramienta y en el aviso a Administración.
Los `limit_choices_to` de los modelos también quedaron alineados, así que el admin de
Django respeta la misma regla.

**Detalle que evita un bug silencioso:** `con_seleccion_actual()` conserva en el selector
al jefe que un proyecto ya tenía asignado, aunque hoy esté inactivo. Sin eso, editar un
proyecto antiguo le habría borrado el jefe sin avisar.

### 8 · Revisar una solicitud de acceso antes de aprobarla

Pantalla nueva: **Usuarios → Solicitudes pendientes → Revisar** (o clic en el nombre de
usuario). Muestra todo lo que declaró el solicitante, con la fecha de la solicitud, y
permite corregirlo antes de decidir. Tres botones:

- **Guardar y aprobar** — aplica las correcciones y activa la cuenta. Si cambiaste el rol,
  el mensaje lo deja explícito: «aprobada como Jefe de Proyecto (había solicitado Bodeguero)».
- **Sólo guardar cambios** — corrige y deja la solicitud pendiente, para decidir después.
- **Rechazar** — elimina la solicitud, con confirmación.

El caso que esto resuelve es el rol mal elegido: el formulario público lo pide al
solicitante, y se equivoca. Antes había que aprobar primero y editar la cuenta después;
ahora es un solo paso. A diferencia del formulario público, aquí **sí** se puede asignar
el rol Administrador: quien revisa ya lo es, y concederlo es decisión suya.

**Corrección de seguridad de paso:** aprobar y rechazar eran enlaces `GET`. Un enlace que
borra un usuario es peligroso —el prefetch del navegador, un bot o un antivirus pueden
dispararlo sin que nadie haga clic—, así que ahora son formularios `POST` con CSRF. Un
`GET` a esas rutas responde 405.

## Lo que queda para la entrega 2

- **Punto 6** — En la solicitud: elegir proveedor primero, buscar en su catálogo mientras
  se escribe, y valor unitario editable. Más la precarga de la cotización desde esos datos.
- Propagar la condición de pago **del material** a la orden de compra. Hoy la OC sigue
  usando la del proveedor, porque sus líneas todavía no referencian al `ProveedorMaterial`
  — ese vínculo se crea justamente en el punto 6.

## Archivos

**Nuevos:** `proveedores/catalogo_excel.py`, `proyectos/pdf.py`, y tres migraciones.

**Modificados:** modelos, formularios, vistas, urls, admin y tests de `proveedores`,
`proyectos` e `inventario`; `usuarios/models.py`; cuatro plantillas; `requirements.txt`
(Django 5.2.17 + openpyxl 3.1.5).
