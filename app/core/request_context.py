"""
Request Context menggunakan contextvars.
Menyimpan request_id unik per request agar bisa diakses dari mana saja
tanpa perlu passing parameter manual.
"""

import contextvars
import uuid
import logging

# ContextVar untuk menyimpan request_id per-request (thread/async safe)
request_id_var: contextvars.ContextVar[str] = contextvars.ContextVar("request_id", default="-")


def generate_request_id() -> str:
    """Generate request ID pendek (8 karakter dari UUID4)"""
    return uuid.uuid4().hex[:8]


def get_request_id() -> str:
    """Ambil request_id dari context saat ini"""
    return request_id_var.get()


class RequestIdFilter(logging.Filter):
    """
    Custom logging filter yang otomatis inject request_id ke setiap log record.
    Dengan ini, semua logger di app otomatis punya %(request_id)s di formatnya.
    """
    def filter(self, record):
        record.request_id = request_id_var.get()
        return True
