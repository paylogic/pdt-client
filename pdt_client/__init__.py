"""pdt-client public interface."""
__version__ = '1.3.0'

try:
    from .commands import migrate

    __all__ = [migrate.__name__]
except ImportError:  # pragma: no cover
    pass
