import binascii
from contextlib import contextmanager

from django.db import connection


@contextmanager
def acquire_database_transaction_lock(lock_name: str) -> bool:
    """
    Try to acquire a database lock, return false if the
    lock is already held by another session.

    :param lock_name: A name for the transaction lock
    """
    lock_id = binascii.crc32(lock_name.encode("utf-8")) % (1 << 32)
    cursor = connection.cursor()
    cursor.execute("BEGIN")
    cursor.execute("SELECT pg_try_advisory_xact_lock(%s)", (lock_id,))
    acquired = cursor.fetchone()[0]
    try:
        yield acquired
    finally:
        cursor.execute("COMMIT")
        cursor.close()
