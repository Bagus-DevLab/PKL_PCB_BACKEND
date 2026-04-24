from slowapi import Limiter
from slowapi.util import get_remote_address

# Shared rate limiter instance — digunakan oleh semua router.
# Satu instance memastikan rate limit dihitung secara konsisten.
limiter = Limiter(key_func=get_remote_address)
