"""
Key rotation and full-database re-encryption.
Ротация ключей и перешифрование всей базы данных.
Ротація ключів та перешифрування всієї бази даних.
"""
from __future__ import annotations
import sqlite3
from typing import Optional

from utils.logger import get_logger
from security.encryption.exceptions import KeyDerivationError, KeyRotationError, EncryptionError
from security.encryption.memory import zero as _zero
from security.encryption.key_management import (
    set_key_from_master, _master_key,
)
from security.encryption.cipher import encrypt, decrypt

logger = get_logger("encryption.rotation")


# ── Key-rotation strategy ────────────────────────────────────
# Re-encryption is a two-phase commit:
#  Phase 1 — read: decrypt every field with the OLD key into plain-text RAM
#  Phase 2 — write: encrypt every field with the NEW key and persist
#
# ⚠ Risk window: if the process is killed between phase 1 and phase 2,
#   some records will be encrypted with the old key and some with the new.
#   The next rotation will re-attempt and fix any stragglers.
#
# ⚠ Memory: all plaintext values are held in RAM simultaneously during
#   phase 1. For large vaults (10 000+ records) this can be several MB.
# Mitigations: a future version should chunk the work and wipe each row
#   from memory after writing its re-encrypted version.
def reencrypt_all(old_master: Optional[str], new_master: Optional[str]) -> None:
    """Re-encrypt every sensitive field using a new master password.

    Перешифровывает все чувствительные поля новым мастер-паролем.
    Перешифровує всі чутливі поля новим майстер-паролем.
    """
    import security.encryption.key_management as _km

    from storage.database import get_db_path

    if old_master:
        try:
            set_key_from_master(old_master)
        except KeyDerivationError as e:
            raise KeyRotationError(f"Cannot reencrypt: {e}") from e
    else:
        _zero(_km._master_key)
        _km._master_key = None

    db_path = get_db_path()
    if not db_path:
        logger.info("Database file not found, nothing to reencrypt")
        return

    import os
    if not os.path.exists(db_path):
        logger.info("Database file not found, nothing to reencrypt")
        return

    conn = None
    try:
        conn = sqlite3.connect(db_path)
        rows = conn.execute(
            "SELECT id, label, password, notes FROM passwords ORDER BY id"
        ).fetchall()
    except sqlite3.Error as e:
        raise KeyRotationError(f"Cannot read database: {e}") from e
    finally:
        if conn:
            conn.close()

    if not rows:
        logger.info("No records to reencrypt")
        return

    # ── Phase 1: decrypt everything with the OLD key ──────────
    # We collect ALL plaintext values into memory before touching the DB
    # so that if decryption of any record fails, we abort before corrupting
    # any existing data.
    decrypted_records = []
    for record_id, label, encrypted_password, notes in rows:
        try:
            decrypted_records.append((
                record_id,
                decrypt(label or ""),
                decrypt(encrypted_password or ""),
                decrypt(notes or ""),
            ))
        except (ValueError, TypeError, EncryptionError) as e:
            logger.error("Decrypt error for id %s: %s", record_id, e)

    # ── Key switch ────────────────────────────────────────────
    # set_key_from_master() replaces _master_key in memory with a new
    # SCrypt-derived value.  After this line, encrypt() will use the new key.
    if new_master:
        try:
            set_key_from_master(new_master)
        except KeyDerivationError as e:
            raise KeyRotationError(f"Cannot set new key: {e}") from e
    else:
        _zero(_km._master_key)
        _km._master_key = None

    # ── Phase 2: re-encrypt and write back ───────────────────
    # Each UPDATE is batched into a single transaction (conn.commit() at end).
    # If the write fails mid-way, SQLite's ACID guarantees roll back the
    # entire batch, keeping the DB consistent (though with OLD key values).
    conn = None
    try:
        conn = sqlite3.connect(db_path)
        cur  = conn.cursor()
        for record_id, plain_label, plain_password, plain_notes in decrypted_records:
            try:
                cur.execute(
                    "UPDATE passwords SET label=?, password=?, notes=? WHERE id=?",
                    (
                        encrypt(plain_label),
                        encrypt(plain_password),
                        encrypt(plain_notes),
                        record_id,
                    ),
                )
            except (sqlite3.Error, EncryptionError) as e:
                logger.error("Reencrypt error for id %s: %s", record_id, e)
        conn.commit()
        logger.info("Reencrypted %d records", len(decrypted_records))
    except sqlite3.Error as e:
        raise KeyRotationError(f"Cannot write reencrypted data: {e}") from e
    finally:
        if conn:
            conn.close()
