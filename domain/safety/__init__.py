"""Safety-net: zweryfikowane zasoby wsparcia (spec §8). Encje domenowe, zero I/O."""

from domain.safety.resources import CrisisResource, CrisisResources

__all__ = ["CrisisResource", "CrisisResources"]
