"""Shared utility functions for address models.

This module re-exports address formatting utilities from the core module
for backwards compatibility. New code should import directly from
`ryandata_address_utils.core.address_formatter`.

.. deprecated::
    Import from `ryandata_address_utils.core.address_formatter` instead.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

# Re-export from core for backwards compatibility
from ryandata_address_utils.core.address_formatter import (
    compute_full_address_from_parts as compute_full_address,
)
from ryandata_address_utils.core.address_formatter import (
    recompute_full_address as recompute_address_full_address,
)

if TYPE_CHECKING:
    pass

__all__ = [
    "compute_full_address",
    "recompute_address_full_address",
]
