"""Open UX — cited UX rules agents audit against."""

from __future__ import annotations

try:
    from open_ux._version import __version__
except ImportError:  # pragma: no cover - editable tree before first build
    try:
        from importlib.metadata import version

        __version__ = version("open-ux")
    except Exception:
        __version__ = "0.0.0"
