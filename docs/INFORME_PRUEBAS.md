# Informe de Pruebas Unitarias — Incrementos 1 y 2

**Grupo 23 — Sistema de Gestión de Adquisiciones e Inventario — Constructora M5 SpA**

La rúbrica exige dejar **evidencia de cada prueba**. Este documento lista las pruebas
unitarias del sistema con su trazabilidad al requerimiento / caso de uso, y deja un
espacio para pegar la **captura de pantalla** del resultado de la ejecución.

En el Incremento 2 el sistema pasa de 27 a **66 pruebas** (`python manage.py test`).

---

## Cómo ejecutar y capturar la evidencia

```bash
python manage.py test --verbosity=2
```

1. Ejecuta el comando con el entorno virtual activado.
2. Toma una **captura de pantalla** de la salida completa (debe verse `OK` y `Ran 66 tests`).
3. Pega la captura en la sección 3 de este documento.
4. (Opcional) ejecuta módulo por módulo, p. ej. `python manage.py test adquisiciones --verbosity=2`.

---

## 1. Resumen de cobertura

| Módulo | N° de pruebas | Requerimientos cubiertos |
|---|---|---|
| usuarios | 8 | RF-50, RF-51, RF-52 (RBAC, 5 roles) |
| proveedores | 10 | RF-01..03, RF-05, RF-06, RF-07 |
| proyectos | 6 | RF-09, RF-13, **RF-14** |
| inventario | 8 | RF-29, RF-32, RF-33, RF-34, RF-37 (+ smoke de bodega) |
| solicitudes | 13 | RF-11..17 — incl. **RF-16** (justificación) y **RF-17** (adjuntos) |
| adquisiciones | 9 | RF-19, RF-21, RF-22, RF-23, RF-24, RF-25 (+ smoke) |
| facturacion | 7 | RF-40, RF-41, RF-42, RF-43, RF-44 |
| **TOTAL** | **66** | 48 RF acumulados (75 % del proyecto) |

---

## 2. Detalle de pruebas del Incremento 2 (trazabilidad)

### `proveedores` — Listado de materiales del proveedor
| Prueba | Verifica | RF |
|---|---|---|
| `ProveedorMaterialTest.test_rf05_agregar_material` | Se agrega un material al listado del proveedor | RF-05 |
| `ProveedorMaterialTest.test_rf05_codigo_duplicado_por_proveedor` | No se repite el código dentro del proveedor | RF-05 |
| `ProveedorMaterialTest.test_rf06_marcar_no_disponible_no_borra` | Marcar "no disponible" no elimina el registro | RF-06 |
| `ProveedorMaterialTest.test_rf07_editar_actualiza_fecha_modificacion` | Editar guarda la fecha de última modificación | RF-07 |

### `proyectos` — Centro de costo
| Prueba | Verifica | RF |
|---|---|---|
| `CentroCostoTest.test_centro_costo_duplicado_es_invalido` | El centro de costo no se repite entre proyectos | RF-14 |
| `CentroCostoTest.test_centro_costo_nuevo_es_valido` | Un centro de costo nuevo se acepta | RF-14 |

### `solicitudes` — Justificación y adjuntos
| Prueba | Verifica | RF |
|---|---|---|
| `JustificacionItemizadoTest.test_exceso_sin_justificacion_es_invalido` | Sin justificación al exceder el itemizado → error | RF-16 |
| `JustificacionItemizadoTest.test_exceso_con_justificacion_es_valido` | Con justificación se acepta la línea | RF-16 |
| `JustificacionItemizadoTest.test_dentro_del_saldo_no_requiere_justificacion` | Dentro del saldo no pide justificación | RF-16 |
| `AdjuntosSolicitudTest.test_formato_no_permitido_es_rechazado` | Solo PDF/JPG | RF-17 |
| `AdjuntosSolicitudTest.test_archivo_pdf_valido` | Un PDF válido se acepta | RF-17 |
| `AdjuntosSolicitudTest.test_maximo_3_adjuntos` | Máximo 3 archivos por solicitud | RF-17 |

### `adquisiciones` — Cotizaciones y Órdenes de Compra
| Prueba | Verifica | RF |
|---|---|---|
| `CotizacionTest.test_rf19_bandeja_muestra_sm_aprobadas` | La bandeja lista las SM aprobadas | RF-19 |
| `CotizacionTest.test_rf21_valor_total_cotizacion` | Valor total = Σ(cant×VU) + despacho | RF-21 |
| `CotizacionTest.test_rf22_aprobar_linea_descarta_las_demas` | Aprobar una línea descarta las demás del material | RF-22 |
| `CotizacionTest.test_rf23_generar_oc_una_por_proveedor` | Se genera una OC por proveedor; SM → "OC generada" | RF-23 |
| `OrdenCompraTest.test_rf23_correlativo_automatico` | Correlativo `OC-000001` automático | RF-23 |
| `OrdenCompraTest.test_rf24_jefe_aprueba_y_se_envia` | El Jefe aprueba y la OC pasa a "Enviada" | RF-24 / RF-27 |
| `OrdenCompraTest.test_rf24_rechazo_exige_motivo` | El rechazo exige motivo | RF-24 |
| `OrdenCompraTest.test_rf25_devolver_rechazada_a_borrador` | La OC rechazada vuelve a borrador | RF-25 |

### `inventario` — Bodega
| Prueba | Verifica | RF |
|---|---|---|
| `StockTiempoRealTest.test_entrada_suma_stock` | La entrada suma stock al instante | RF-32 |
| `StockTiempoRealTest.test_salida_resta_stock` | La salida descuenta stock | RF-31 / RF-32 |
| `StockTiempoRealTest.test_merma_resta_stock` | La merma descuenta stock | RF-35 |
| `StockTiempoRealTest.test_rf37_bajo_stock_minimo` | Detecta material bajo su stock mínimo | RF-37 |
| `EntradaOCTest.test_cantidad_excedida_es_invalida` | No se recibe más que lo pedido en la OC | RF-29 |
| `EntradaOCTest.test_cantidad_dentro_de_la_oc_es_valida` | Recepción dentro de la OC es válida | RF-29 |
| `PrestamoTest.test_prestamo_descuenta_una_unidad_y_devolucion_la_repone` | Préstamo y devolución de herramienta | RF-33 / RF-34 |

### `facturacion` — Facturas y Cuentas por Pagar
| Prueba | Verifica | RF |
|---|---|---|
| `FacturaTest.test_rf40_monto_ok_marca_oc_facturada` | Factura dentro de tolerancia marca la OC como facturada | RF-40 |
| `FacturaTest.test_rf41_diferencia_excesiva_bloquea` | Diferencia > tolerancia → factura bloqueada | RF-41 |
| `FacturaTest.test_rf42_admin_desbloquea` | Administración desbloquea la factura | RF-42 |
| `FacturaTest.test_rf43_cuentas_por_pagar_ordena_por_vencimiento` | Vista de Cuentas por Pagar | RF-43 |
| `FacturaTest.test_rf44_export_csv` | Exportación del listado a CSV | RF-44 |

> Además, cada módulo incluye un `test_paginas_renderizan` / `test_detalle_renderiza_en_varios_estados`
> que verifica que **todas las plantillas nuevas se renderizan sin error** (HTTP 200).

---

## 3. Evidencia de ejecución

### 3.1. Ejecución completa

> **[ PEGAR AQUÍ LA CAPTURA DE `python manage.py test --verbosity=2` ]**
>
> La captura debe mostrar la línea final:
> ```
> Ran 66 tests in X.XXXs
>
> OK
> ```

### 3.2. Capturas por módulo (opcional)

| Módulo | Captura |
|---|---|
| usuarios | _[ pegar captura ]_ |
| proveedores | _[ pegar captura ]_ |
| proyectos | _[ pegar captura ]_ |
| inventario | _[ pegar captura ]_ |
| solicitudes | _[ pegar captura ]_ |
| adquisiciones | _[ pegar captura ]_ |
| facturacion | _[ pegar captura ]_ |

---

## 4. Conclusión

> _[ Redactar 2-3 líneas: 66 pruebas ejecutadas, todas OK, cobertura sobre los 32 RF
> nuevos del Incremento 2 (48 RF acumulados = 75 % del proyecto). ]_
