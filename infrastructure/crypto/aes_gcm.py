"""Szyfrowanie pól wrażliwych AES-GCM (Prompt 3.2).

Implementuje port `ICryptoService`. Format BLOB-a: `nonce (12 B) || ciphertext+tag`.
AES-256-GCM zapewnia poufność i integralność (manipulacja → błąd przy odszyfrowaniu).
Zły/uszkodzony klucz lub naruszony szyfrogram dają kontrolowany `DecryptionError`,
nigdy cichy crash (spec §12; CLAUDE - reguły bezpieczeństwa).
"""

from __future__ import annotations

import os

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from application.ports.security import ICryptoService

NONCE_BYTES = 12
KEY_BYTES = 32  # AES-256


class DecryptionError(Exception):
    """Nie udało się odszyfrować (zły klucz lub naruszony/uszkodzony szyfrogram)."""


class AesGcmCryptoService(ICryptoService):
    def __init__(self, key: bytes) -> None:
        if not isinstance(key, (bytes, bytearray)) or len(key) != KEY_BYTES:
            raise ValueError(
                f"Klucz AES-GCM musi mieć dokładnie {KEY_BYTES} bajtów."
            )
        self._aes = AESGCM(bytes(key))

    def encrypt(self, plaintext: str) -> bytes:
        nonce = os.urandom(NONCE_BYTES)
        ciphertext = self._aes.encrypt(nonce, plaintext.encode("utf-8"), None)
        return nonce + ciphertext

    def decrypt(self, blob: bytes) -> str:
        if not isinstance(blob, (bytes, bytearray)) or len(blob) <= NONCE_BYTES:
            raise DecryptionError("Nieprawidłowy lub zbyt krótki szyfrogram.")
        nonce = bytes(blob[:NONCE_BYTES])
        ciphertext = bytes(blob[NONCE_BYTES:])
        try:
            plaintext = self._aes.decrypt(nonce, ciphertext, None)
        except InvalidTag as exc:
            raise DecryptionError(
                "Odszyfrowanie nieudane (zły klucz lub naruszone dane)."
            ) from exc
        return plaintext.decode("utf-8")
