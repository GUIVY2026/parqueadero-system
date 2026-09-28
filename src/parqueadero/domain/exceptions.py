"""Excepciones de dominio. Las interfaces las mapean a HTTP."""


class ErrorDeDominio(Exception):
    """Error de negocio; no usar para fallos de infraestructura."""


class RecursoNoEncontrado(ErrorDeDominio):
    """Agregado o entidad inexistente."""


class ConflictoDeDominio(ErrorDeDominio):
    """Violación de invariante o estado incompatible (p. ej. ticket ya cerrado)."""


class DatosInvalidos(ErrorDeDominio):
    """Value object o comando con datos que no cumplen el formato de negocio."""


class VehiculoYaEnPatio(ConflictoDeDominio):
    """Ya existe un ticket abierto para la misma placa en la sede."""


class TicketYaCerrado(ConflictoDeDominio):
    """No se puede cerrar ni modificar un ticket que ya está cerrado."""
