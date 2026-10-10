"""EZStudio declarative gene runtime.

This package is intentionally region-agnostic. PROFILE is the first migration
consumer, but STEMS, CHORDS/N and LYRICS must use the same contracts.
"""

from .gene_spec import ModuleConfigDocument, GeneSpecError, load_module_config
from .engine_registry import EngineAdapterRegistry, EngineAdapterError
from .decision import apply_decision

__all__ = [
    "ModuleConfigDocument",
    "GeneSpecError",
    "load_module_config",
    "EngineAdapterRegistry",
    "EngineAdapterError",
    "apply_decision",
]
