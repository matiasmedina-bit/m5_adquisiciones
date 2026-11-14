"""
RNF-09 — Sin borrado físico de registros críticos.

Órdenes de compra, proveedores, facturas y movimientos de inventario no se
borran nunca de la base: los proveedores se inactivan, las OC se rechazan o
quedan en su estado final, y las facturas y movimientos son registro contable
y de bodega. Este módulo hace que el borrado físico sea imposible por error:

  · ``SinBorradoFisicoMixin`` en el modelo bloquea ``instancia.delete()``;
  · ``SinBorradoFisicoQuerySet`` bloquea ``Modelo.objects.filter(...).delete()``;
  · el admin de Django además oculta el botón de borrar (ver cada ``admin.py``).

La única salida es explícita y deliberada: ``with borrado_fisico_permitido():``.
La usa sólo ``preparar_produccion``, que limpia los datos de demostración antes
de entregar el sistema y por definición no toca datos reales.
"""
from contextlib import contextmanager
from contextvars import ContextVar

from django.db import models

_permitido = ContextVar("borrado_fisico_permitido", default=False)


class BorradoFisicoNoPermitido(Exception):
    """Se intentó borrar físicamente un registro crítico (RNF-09)."""


@contextmanager
def borrado_fisico_permitido():
    token = _permitido.set(True)
    try:
        yield
    finally:
        _permitido.reset(token)


def _verificar(modelo):
    if not _permitido.get():
        raise BorradoFisicoNoPermitido(
            f"{modelo._meta.verbose_name_plural.capitalize()} no se eliminan de la base "
            f"de datos (RNF-09): usa la anulación o inactivación correspondiente.")


class SinBorradoFisicoQuerySet(models.QuerySet):
    def delete(self):
        _verificar(self.model)
        return super().delete()


class SinBorradoFisicoMixin(models.Model):
    objects = SinBorradoFisicoQuerySet.as_manager()

    class Meta:
        abstract = True

    def delete(self, *args, **kwargs):
        _verificar(type(self))
        return super().delete(*args, **kwargs)


class SinBorradoAdminMixin:
    """Para los ModelAdmin de registros críticos: sin botón ni acción de borrar."""

    def has_delete_permission(self, request, obj=None):
        return False
