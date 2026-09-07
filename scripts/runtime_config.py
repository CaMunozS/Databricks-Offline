"""Corporate runtime profile used as a compatibility target, not a hard lock."""
from __future__ import annotations

import platform
from typing import Any

# Fuente de verdad para metadata, manifest y entorno de staging.
PYTHON_TARGET = ">=3.11,<3.13"
PYTHON_REQUIRES = PYTHON_TARGET
DATABRICKS_RUNTIME_TARGET = "17.3 ML Runtime (Python 3.12.3)"

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


def require_target_python() -> None:
    """Reject a staging dependency mismatch; allow Python 3.12 maintenance releases."""
    actual = current_runtime()
    differences = runtime_differences(actual)
    python_version = actual.get("python", "")
    if python_version.split(".")[:2] == RUNTIME_TARGET["python"].split(".")[:2]:
        differences.pop("python", None)
    if differences:
        detail = ", ".join(
            f"{key}: esperado={value['target']} detectado={value['detected']}"
            for key, value in differences.items()
        )
        raise RuntimeError(f"El entorno de staging no coincide con el runtime objetivo: {detail}")
    report_runtime()


def python_minor_warning(metadata_target: str | None) -> str | None:
    """Return an explicit warning when this Python is outside metadata's range."""
    if not metadata_target:
        return "Advertencia: falta python_target en la metadata."
    try:
        from packaging.specifiers import SpecifierSet
        from packaging.version import Version

        current = Version(platform.python_version())
        if current not in SpecifierSet(metadata_target):
            return (
                f"ADVERTENCIA: Python {current} queda fuera de python_target "
                f"{metadata_target}; la evidencia no prueba compatibilidad con este intérprete."
            )
    except Exception as exc:
        return f"ADVERTENCIA: no se pudo validar python_target={metadata_target}: {exc}"
    return None
