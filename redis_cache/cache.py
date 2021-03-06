# -*- coding: utf-8 -*-

from django.conf import settings
from django.core.cache.backends.base import BaseCache
from django.core.exceptions import ImproperlyConfigured
from django.core.cache import get_cache

from .util import load_class
from .exceptions import ConnectionInterrupted

import functools

DJANGO_REDIS_IGNORE_EXCEPTIONS = getattr(settings,
            "DJANGO_REDIS_IGNORE_EXCEPTIONS", False)

def omit_exception(method):
    """
    Simple decorator that intercepts connection
    errors and ignores these if settings specify this.

    Note: this doesn't handle the `default` argument in .get().
    """

    @functools.wraps(method)
    def _decorator(self, *args, **kwargs):
        if self._ignore_exceptions:
            try:
                return method(self, *args, **kwargs)
            except ConnectionInterrupted:
                return None
        else:
            return method(self, *args, **kwargs)

    return _decorator


class RedisCache(BaseCache):
    def __init__(self, server, params):
        super(RedisCache, self).__init__(params)
        self._server = server
        self._params = params

        options = params.get("OPTIONS", {})
        self._client_cls = options.get("CLIENT_CLASS", "redis_cache.client.DefaultClient")
        self._client_cls = load_class(self._client_cls)
        self._client = None

        self._ignore_exceptions = options.get("IGNORE_EXCEPTIONS", DJANGO_REDIS_IGNORE_EXCEPTIONS)

    @property
    def client(self):
        """
        Lazy client connection property.
        """
        if self._client is None:
            self._client = self._client_cls(self._server, self._params, self)
        return self._client

    @property
    def raw_client(self):
        """
        Return a raw redis client (connection). Not all
        pluggable clients supports this feature. If not supports
        this raises NotImplementedError
        """
        return self.client.get_client(write=True)

    @omit_exception
    def set(self, *args, **kwargs):
        return self.client.set(*args, **kwargs)

    @omit_exception
    def incr_version(self, *args, **kwargs):
        return self.client.incr_version(*args, **kwargs)

    @omit_exception
    def add(self, *args, **kwargs):
        return self.client.add(*args, **kwargs)

    @omit_exception
    def get(self, key, default=None, version=None, client=None):
        try:
            return self.client.get(key, default=default, version=version,
                                   client=client)
        except ConnectionInterrupted:
            if DJANGO_REDIS_IGNORE_EXCEPTIONS:
                return default
            raise

    @omit_exception
    def delete(self, *args, **kwargs):
        return self.client.delete(*args, **kwargs)

    @omit_exception
    def delete_pattern(self, *args, **kwargs):
        return self.client.delete_pattern(*args, **kwargs)

    @omit_exception
    def delete_many(self, *args, **kwargs):
        return self.client.delete_many(*args, **kwargs)

    @omit_exception
    def clear(self):
        return self.client.clear()

    @omit_exception
    def get_many(self, *args, **kwargs):
        return self.client.get_many(*args, **kwargs)

    @omit_exception
    def set_many(self, *args, **kwargs):
        return self.client.set_many(*args, **kwargs)

    @omit_exception
    def incr(self, *args, **kwargs):
        return self.client.incr(*args, **kwargs)

    @omit_exception
    def decr(self, *args, **kwargs):
        return self.client.decr(*args, **kwargs)

    @omit_exception
    def has_key(self, *args, **kwargs):
        return self.client.has_key(*args, **kwargs)

    @omit_exception
    def keys(self, *args, **kwargs):
        return self.client.keys(*args, **kwargs)

    @omit_exception
    def close(self, **kwargs):
        self.client.close(**kwargs)
