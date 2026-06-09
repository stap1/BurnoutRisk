"""Warstwa domeny - czysta logika biznesowa, ZERO I/O.

Czas, baza, losowość są wstrzykiwane przez parametr/port - nigdy wołane wprost.
Domena musi być w 100% testowalna w izolacji (patrz CLAUDE.md, spec §1.2.1).
"""
