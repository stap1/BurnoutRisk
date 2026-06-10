"""Tryb PIN: envelope encryption klucza bazy (Prompt 3.4).

Idea (CLAUDE - reguły bezpieczeństwa, spec §2.2.2):
PIN → Argon2id (z losową solą) → KEK (key-encryption-key) → AES-GCM szyfruje
klucz bazy. Gdy PIN włączony, klucz bazy **nigdy** nie leży jawnie obok - w
magazynie jest tylko "koperta" (sól + zaszyfrowany klucz). Utrata PIN = utrata
zaszyfrowanych pól (komunikowane w UI).

Błędny PIN → kontrolowany `WrongPinError` (nie crash). Uszkodzona koperta →
`KeyRecoveryNeeded`, by warstwa wyżej zaproponowała recovery zamiast cichego
wywrócenia (spec §2.2.2, §12.4).

PIN jest opcjonalny i domyślnie wyłączony (równowaga ochrona ↔ wypełnialność).
"""

from __future__ import annotations

import os
from dataclasses import dataclass

from argon2.low_level import Type, hash_secret_raw
from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from infrastructure.crypto.aes_gcm import KEY_BYTES, NONCE_BYTES

SALT_BYTES = 16

# Parametry Argon2id (rząd wielkości wg zaleceń OWASP: t=2, m≈19 MiB, p=1).
ARGON_TIME_COST = 2
ARGON_MEMORY_COST_KIB = 19_456
ARGON_PARALLELISM = 1


class WrongPinError(Exception):
    """Podano błędny PIN (koperta nie odszyfrowała się)."""


class KeyRecoveryNeeded(Exception):
    """Koperta/klucz są uszkodzone lub niedostępne - wymagane recovery, nie crash."""


@dataclass(frozen=True)
class Envelope:
    """Koperta klucza bazy: losowa sól + zaszyfrowany kluczem z PIN klucz bazy."""

    salt: bytes
    wrapped: bytes


def _derive_kek(pin: str, salt: bytes) -> bytes:
    return hash_secret_raw(
        secret=pin.encode("utf-8"),
        salt=salt,
        time_cost=ARGON_TIME_COST,
        memory_cost=ARGON_MEMORY_COST_KIB,
        parallelism=ARGON_PARALLELISM,
        hash_len=KEY_BYTES,
        type=Type.ID,
    )


def wrap_db_key(pin: str, db_key: bytes) -> Envelope:
    """Szyfruje klucz bazy kluczem wyprowadzonym z PIN (włączenie trybu PIN)."""
    if not pin:
        raise ValueError("PIN nie może być pusty.")
    if len(db_key) != KEY_BYTES:
        raise ValueError(f"Klucz bazy musi mieć {KEY_BYTES} bajtów.")

    salt = os.urandom(SALT_BYTES)
    kek = _derive_kek(pin, salt)
    nonce = os.urandom(NONCE_BYTES)
    wrapped = nonce + AESGCM(kek).encrypt(nonce, db_key, None)
    return Envelope(salt=salt, wrapped=wrapped)


def unwrap_db_key(pin: str, envelope: Envelope) -> bytes:
    """Odzyskuje klucz bazy z koperty. Błędny PIN → WrongPinError."""
    if len(envelope.salt) != SALT_BYTES or len(envelope.wrapped) <= NONCE_BYTES:
        raise KeyRecoveryNeeded("Koperta klucza jest uszkodzona.")

    kek = _derive_kek(pin, envelope.salt)
    nonce = envelope.wrapped[:NONCE_BYTES]
    ciphertext = envelope.wrapped[NONCE_BYTES:]
    try:
        return AESGCM(kek).decrypt(nonce, ciphertext, None)
    except InvalidTag as exc:
        raise WrongPinError("Nieprawidłowy PIN.") from exc
