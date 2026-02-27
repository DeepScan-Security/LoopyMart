"""
CTF flags loader. Reads challenge flags from backend/flags.yml.
Supports single-flag and multi-part (joined) flags per challenge.
"""

import logging
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)

_BACKEND_ROOT = Path(__file__).resolve().parent.parent.parent
_FLAGS_PATH = _BACKEND_ROOT / "flags.yml"
_FLAGS_EXAMPLE_PATH = _BACKEND_ROOT / "flags.example.yml"
_CACHED: dict[str, Any] | None = None
_CACHED_MTIME: float | None = None
_CACHED_PATH: Path | None = None


def _effective_flags_path() -> Path | None:
    """Return the flags file to read: prefer flags.yml, fall back to flags.example.yml."""
    if _FLAGS_PATH.exists():
        return _FLAGS_PATH
    if _FLAGS_EXAMPLE_PATH.exists():
        logger.warning(
            "flags.yml not found — falling back to %s (for production, copy to flags.yml "
            "and set real flag values)",
            _FLAGS_EXAMPLE_PATH,
        )
        return _FLAGS_EXAMPLE_PATH
    return None


def _load_flags_yaml() -> dict[str, Any]:
    """Load flags.yml (or flags.example.yml as fallback); return empty dict if missing or invalid.

    Cached at module level and invalidated automatically whenever the effective
    flags file changes (path switch or mtime change), so edits take effect
    without a server restart."""
    global _CACHED, _CACHED_MTIME, _CACHED_PATH
    path = _effective_flags_path()
    if path is None:
        logger.warning(
            "No flags file found at %s or %s — all get_flag() calls return None",
            _FLAGS_PATH,
            _FLAGS_EXAMPLE_PATH,
        )
        _CACHED = {}
        _CACHED_MTIME = None
        _CACHED_PATH = None
        return _CACHED
    try:
        current_mtime = path.stat().st_mtime
    except OSError:
        current_mtime = None
    if _CACHED is not None and path == _CACHED_PATH and current_mtime == _CACHED_MTIME:
        return _CACHED
    try:
        with open(path, "r") as f:
            data = yaml.safe_load(f) or {}
        _CACHED = data
        _CACHED_MTIME = current_mtime
        _CACHED_PATH = path
        return _CACHED
    except Exception as e:
        logger.exception("Failed to load flags from %s: %s", path, e)
        _CACHED = {}
        _CACHED_MTIME = None
        _CACHED_PATH = None
        return _CACHED


def _resolve_flag_value(challenge: dict[str, Any]) -> str | None:
    """
    Resolve one challenge entry to a single flag string.
    Prefer 'flag' if present; otherwise use 'parts' joined by 'separator' (default "").
    """
    if not isinstance(challenge, dict):
        return None
    if "flag" in challenge and challenge["flag"] is not None:
        val = challenge["flag"]
        return str(val).strip() if isinstance(val, str) else None
    if "parts" in challenge and isinstance(challenge["parts"], list):
        parts = [str(p).strip() for p in challenge["parts"] if p is not None]
        if not parts:
            return None
        sep = challenge.get("separator")
        if sep is None:
            sep = ""
        return str(sep).join(parts)
    return None


def get_flag(challenge_id: str) -> str | None:
    """
    Return the flag string for the given challenge_id, or None if missing/invalid.
    """
    data = _load_flags_yaml()
    challenges = data.get("challenges")
    if not isinstance(challenges, dict):
        return None
    entry = challenges.get(challenge_id)
    return _resolve_flag_value(entry) if entry is not None else None


def get_all_challenge_ids() -> list[str]:
    """Return list of challenge IDs defined in flags.yml."""
    data = _load_flags_yaml()
    challenges = data.get("challenges")
    if not isinstance(challenges, dict):
        return []
    return list(challenges.keys())


def get_chat_system_prompt() -> str | None:
    """Return the AI chat system prompt from flags.yml, or None if not configured."""
    data = _load_flags_yaml()
    chat_cfg = data.get("chat")
    if not isinstance(chat_cfg, dict):
        return None
    prompt = chat_cfg.get("system_prompt")
    return str(prompt).strip() if prompt else None
