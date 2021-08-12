from ..rest.client import RESTClient
from .cache import Cache

__all__ = ('ApplicationState',)


class ApplicationState:
    """Central management for the whole library."""

    cache: Cache
    rest: RESTClient

    __slots__ = ('cache', 'rest')

    def __init__(self, cache: Cache, rest: RESTClient) -> None:
        self.cache = cache
        self.rest = rest
