"""Local credential storage helpers for optional StartQ cloud sync."""

from __future__ import annotations

import os
import hashlib
from pathlib import Path


def cloud_api_key_path(root_dir: str | Path) -> Path:
    """Return the user-protected cloud credential path for a workspace."""
    override = os.environ.get("STARTQ_CLOUD_KEY_FILE")
    if override:
        return Path(override).expanduser()
    workspace = str(Path(root_dir).resolve())
    workspace_id = hashlib.sha256(workspace.encode("utf-8")).hexdigest()[:16]
    if os.name == "nt":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    else:
        base = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    return base / "startq" / "credentials" / f"{workspace_id}.key"


def write_cloud_api_key(root_dir: str | Path, api_key: str) -> Path | None:
    """Store a cloud key outside config.json with owner-only permissions."""
    if not api_key:
        return None
    path = cloud_api_key_path(root_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(api_key.strip() + "\n", encoding="utf-8")
    try:
        path.chmod(0o600)
    except OSError:
        pass
    return path


def load_cloud_api_key(root_dir: str | Path, cloud_config: dict) -> str | None:
    """Load a cloud key from the environment, key file, or legacy config."""
    environment_key = os.environ.get("STARTQ_CLOUD_API_KEY")
    if environment_key:
        return environment_key

    key_name = cloud_config.get("api_key_file")
    if key_name:
        configured_path = Path(key_name).expanduser()
        key_path = configured_path if configured_path.is_absolute() else Path(root_dir) / configured_path
    else:
        key_path = cloud_api_key_path(root_dir)
    if key_path.exists():
        value = key_path.read_text(encoding="utf-8").strip()
        return value or None

    # Read-only compatibility for StartQ <= 0.4. The caller migrates this value.
    return cloud_config.get("api_key") or None
