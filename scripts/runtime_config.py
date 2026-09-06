"""Central runtime target for model staging and validation."""
from __future__ import annotations

import sys

PYTHON_TARGET = "3.12.3"
PYTHON_REQUIRES = ">=3.12.3,<3.13"
EXPECTED_VERSION = (3, 12, 3)


def require_target_python() -> None:
    """Fail fast unless the active interpreter is exactly Python 3.12.3."""
    current = sys.version_info[:3]
    if current != EXPECTED_VERSION:
        detected = ".".join(str(part) for part in current)
        raise RuntimeError(
            f"Este repositorio requiere Python {PYTHON_TARGET} para preparar y validar modelos; "
            f"se detectó Python {detected}."
        )
