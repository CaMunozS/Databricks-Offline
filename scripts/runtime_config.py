"""Corporate runtime profile used as a compatibility target, not a hard lock."""
from __future__ import annotations

import platform
from typing import Any

PYTHON_TARGET = "3.12.3"
PYTHON_REQUIRES = ">=3.12.3,<3.13"

RUNTIME_TARGET = {
    "python": "3.12.3",
    "sentence_transformers": "4.0.1",
    "transformers": "4.51.3",
    "torch": "2.7.0+cpu",
    "numpy": "2.1.3",
}


def current_runtime() -> dict[str, str]:
    """Return the versions actually available in the current environment."""
    versions: dict[str, str] = {"python": platform.python_version()}
    modules: tuple[tuple[str, str], ...] = (
        ("sentence_transformers", "sentence_transformers"),
        ("transformers", "transformers"),
        ("torch", "torch"),
        ("numpy", "numpy"),
    )
    for key, module_name in modules:
        try:
            module: Any = __import__(module_name)
            versions[key] = str(getattr(module, "__version__", "unknown"))
        except Exception as exc:
            versions[key] = f"unavailable: {type(exc).__name__}"
    return versions


def runtime_differences(actual: dict[str, str] | None = None) -> dict[str, dict[str, str]]:
    """Compare current runtime with the corporate target without rejecting mismatches."""
    actual = actual or current_runtime()
    differences: dict[str, dict[str, str]] = {}
    for key, expected in RUNTIME_TARGET.items():
        detected = actual.get(key, "unavailable")
        if detected != expected:
            differences[key] = {"target": expected, "detected": detected}
    return differences


def report_runtime() -> dict[str, str]:
    """Print target vs detected versions. Mismatches are warnings, not blockers."""
    actual = current_runtime()
    differences = runtime_differences(actual)
    print("Corporate runtime target:")
    for key, expected in RUNTIME_TARGET.items():
        detected = actual.get(key, "unavailable")
        status = "MATCH" if detected == expected else "DIFFERENT"
        print(f"- {key}: target={expected} detected={detected} [{status}]")
    if differences:
        print("RUNTIME PROFILE WARNING: el entorno difiere del objetivo; se continúa y la compatibilidad real la determina la ejecución offline del modelo.")
    else:
        print("RUNTIME PROFILE MATCH")
    return actual
