"""Validadores reutilizables del proyecto."""
from django.core.exceptions import ValidationError


def limpiar_rut(rut: str) -> str:
    """Normaliza un RUT: quita puntos, guion y pasa el dígito verificador a mayúscula."""
    return rut.replace(".", "").replace("-", "").strip().upper()


def calcular_dv(cuerpo: str) -> str:
    """Calcula el dígito verificador de un RUT chileno (módulo 11)."""
    reversed_digits = map(int, reversed(cuerpo))
    factors = [2, 3, 4, 5, 6, 7]
    s = 0
    for i, d in enumerate(reversed_digits):
        s += d * factors[i % 6]
    resto = 11 - (s % 11)
    if resto == 11:
        return "0"
    if resto == 10:
        return "K"
    return str(resto)


def validar_rut(rut: str) -> None:
    """
    Valida un RUT chileno (formato y dígito verificador).
    Usado en CU-02 'Validando RUT del proveedor'.
    Lanza ValidationError si es inválido.
    """
    rut_limpio = limpiar_rut(rut)
    if len(rut_limpio) < 2:
        raise ValidationError("El RUT es demasiado corto.")
    cuerpo, dv = rut_limpio[:-1], rut_limpio[-1]
    if not cuerpo.isdigit():
        raise ValidationError("El cuerpo del RUT debe ser numérico.")
    if calcular_dv(cuerpo) != dv:
        raise ValidationError("El dígito verificador del RUT no es válido.")


def formatear_rut(rut: str) -> str:
    """Devuelve el RUT con formato 12.345.678-9."""
    rut_limpio = limpiar_rut(rut)
    cuerpo, dv = rut_limpio[:-1], rut_limpio[-1]
    cuerpo_fmt = f"{int(cuerpo):,}".replace(",", ".")
    return f"{cuerpo_fmt}-{dv}"
