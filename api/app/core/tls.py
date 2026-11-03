"""TLS verification against the operating system's certificate store.

certifi's bundle rejects networks that re-sign traffic with their own root (corporate
SSL inspection); the OS store already trusts that root. Verification stays fully on.
"""

import ssl
from functools import lru_cache

import truststore


@lru_cache(maxsize=1)
def ssl_context() -> ssl.SSLContext:
    return truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
