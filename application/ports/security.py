"""Porty bezpieczeństwa: szyfrowanie pól i magazyn klucza (warstwa aplikacji).

Implementacje (AES-GCM, keyring/Argon2id) powstają w infrastrukturze (Faza 3.2,
3.4). Aplikacja zna tylko kontrakt.
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class ICryptoService(ABC):
    """Szyfrowanie pól wrażliwych (notes, comments) - AES-GCM."""

    @abstractmethod
    def encrypt(self, plaintext: str) -> bytes:
        """Szyfruje tekst do BLOB (nonce + ciphertext + tag)."""

    @abstractmethod
    def decrypt(self, blob: bytes) -> str:
        """Odszyfrowuje BLOB. Zły/uszkodzony klucz → kontrolowany błąd, nie crash."""


class IKeyStore(ABC):
    """Magazyn klucza szyfrującego (systemowy keyring)."""

    @abstractmethod
    def get_or_create_key(self) -> bytes:
        """Zwraca klucz bazy; przy 1. uruchomieniu generuje losowy i zapisuje."""

    @abstractmethod
    def delete_key(self) -> None:
        """Usuwa klucz (część operacji wipe - spec §2.4)."""

    @abstractmethod
    def is_backend_safe(self) -> bool:
        """False dla niebezpiecznego backendu (null/fail/plaintext) - fail-fast §12.6."""
