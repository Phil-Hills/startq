"""
startq.brain - Local Filesystem Persistence Driver + Cloud Sync
"""

import json
import os
import uuid
import datetime
import getpass
import shutil
import subprocess
from pathlib import Path

from .credentials import load_cloud_api_key, write_cloud_api_key
from .integrity import get_or_create_signing_key, sign_receipt, verify_receipt

class SecureBootViolation(Exception):
    pass

class BrainManager:
    def __init__(self, root_dir: str = ".startq"):
        self.root_dir = Path(root_dir)
        self.brain_dir = self.root_dir / "brain"
        self.state_file = self.root_dir / "state.json"
        self.cloud = None  # Set by CLI when --cloud or auto-enabled

    def _load_cloud_config(self):
        """Load cloud config if present and enabled."""
        config = self.get_config()
        cloud_cfg = config.get("cloud", {})
        if cloud_cfg.get("enabled", False) and cloud_cfg.get("brain_url"):
            try:
                from .cloud_brain import CloudBrainClient
                api_key = load_cloud_api_key(self.root_dir, cloud_cfg)
                if cloud_cfg.get("api_key"):
                    write_cloud_api_key(self.root_dir, cloud_cfg["api_key"])
                    cloud_cfg.pop("api_key", None)
                    cloud_cfg.pop("api_key_file", None)
                    cloud_cfg["api_key_storage"] = "user-config"
                    config["cloud"] = cloud_cfg
                    self.save_config(config)
                self.cloud = CloudBrainClient(
                    brain_url=cloud_cfg["brain_url"],
                    api_key=api_key,
                )
                return True
            except Exception:
                pass
        return False

    def init_brain(self):
        """Bootstrap the local startq working directory."""
        if self.brain_dir.exists():
            print("  [DISK] StartQ Brain already formatted.")
            return False
            
        self.brain_dir.mkdir(parents=True, exist_ok=True)
        get_or_create_signing_key(self.root_dir)
        self.state_file.write_text(json.dumps({
            "initialized_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
        }))
        
        config_file = self.root_dir / "config.json"
        if not config_file.exists():
            user = getpass.getuser()
            config_file.write_text(json.dumps({
                "identity": user,
                "role": "ai-operator",
                "daemons": {}
            }, indent=2))
            
        print(f"  [DISK] StartQ Memory mapped at {self.brain_dir.absolute()}")
        return True

    def check_health(self):
        """Execute physical POST hardware diagnostics."""
        if not self.brain_dir.exists():
            raise FileNotFoundError("Local Brain not found. Run `startq init` first.")
            
        if not os.access(self.brain_dir, os.R_OK | os.W_OK):
            raise PermissionError(f"FATAL: Insufficient IO permissions on {self.brain_dir}")
            
        free_space = shutil.disk_usage(self.brain_dir).free
        if free_space < 50 * 1024 * 1024:
            raise OSError(f"FATAL: NVMe buffer exhausted. Only {free_space} bytes free.")
            
        return True

    def get_config(self):
        """Retrieve the user's local StartQ configuration."""
        config_file = self.root_dir / "config.json"
        if config_file.exists():
            try:
                return json.loads(config_file.read_text())
            except Exception:
                pass
        return {"identity": "unknown-operator"}

    def save_config(self, config: dict):
        """Write config back to disk."""
        config_file = self.root_dir / "config.json"
        config_file.write_text(json.dumps(config, indent=2))

    def boot_session(self, use_cloud: bool = False, allow_legacy: bool = False):
        """Load context from the Brain and create a new session."""
        self.check_health()
        
        # Load cloud client if requested or auto-enabled
        if use_cloud or self._load_cloud_config():
            pass  # self.cloud is now set
        
        # Load previous context (latest local session)
        sessions = sorted(self.brain_dir.glob("*.json"), key=os.path.getmtime, reverse=True)
        recent_context = None
        if sessions:
            try:
                data = json.loads(sessions[0].read_text())
                
                stored_signature = data.get("signature")
                if stored_signature:
                    valid, profile = verify_receipt(data, self.root_dir)
                    if not valid:
                        raise SecureBootViolation(f"Receipt verification failed ({profile})")
                    if profile == "legacy-sha256":
                        if not allow_legacy:
                            raise SecureBootViolation(
                                "Legacy receipt blocked; rerun with --allow-legacy after review"
                            )
                        print("  [!] kernel_warning: legacy unkeyed SHA-256 receipt loaded")
                else:
                    print("  [!] kernel_warning: legacy unsigned session loaded")
                    
                recent_context = data.get("context")
            except json.JSONDecodeError as e:
                print(f"  [!] kernel_panic: recent session blocked (corrupted format: {e})")
            except SecureBootViolation as e:
                print(f"  [!] kernel_panic: Secure Boot Signature Violation: {e}")
                recent_context = None
        
        # Try cloud context if local is empty and cloud is configured
        cloud_context = None
        if self.cloud and not recent_context:
            config = self.get_config()
            cloud_data = self.cloud.load_latest(identity=config.get("identity"))
            if cloud_data:
                cloud_context = cloud_data.get("context", cloud_data.get("note", ""))
                print(f"  --> cloud-daemon: Context loaded from cloud Brain.")
                
        session_id = str(uuid.uuid4())
        
        print(f"  --> memory-daemon: Indexed {len(sessions)} historical blocks.")
        if recent_context:
            print(f"  --> context-daemon: Active state injected ({len(recent_context)} bytes).")
        if cloud_context and not recent_context:
            recent_context = cloud_context
            
        return {
            "session_id": session_id,
            "recent_context": recent_context,
            "sessions_found": len(sessions),
            "cloud_connected": self.cloud is not None,
        }

    def end_session(self, context_summary: str, use_cloud: bool = False):
        """Write the session context back to the Brain to prevent amnesia."""
        self.check_health()
        
        # Load cloud client if requested or auto-enabled
        if use_cloud or self._load_cloud_config():
            pass
        
        session_id = str(uuid.uuid4())
        
        payload = {
            "session_id": session_id,
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "context": context_summary,
            "type": "session_receipt",
            "source": "startq",
        }
        
        try:
            branch = subprocess.check_output(
                ["git", "branch", "--show-current"], stderr=subprocess.DEVNULL
            ).decode().strip()
            status = subprocess.check_output(
                ["git", "status", "--porcelain"], stderr=subprocess.DEVNULL
            ).decode().splitlines()
            payload["hibernation_state"] = {"branch": branch, "modified_files": status}
        except Exception:
            payload["hibernation_state"] = None
            
        payload = sign_receipt(payload, self.root_dir)
        
        # Write locally (always)
        receipt_path = self.brain_dir / f"{session_id}.json"
        receipt_path.write_text(json.dumps(payload, indent=2))
        print(f"\n  [SHUTDOWN] State persistently synced to local memory.")
        print(f"  [RECEIPT]  {session_id}")
        
        # Sync to cloud (if configured)
        if self.cloud:
            sync_result = self.cloud.sync_session(payload)
            if sync_result["synced"]:
                print(f"  [CLOUD]    Synced to cloud Brain: {sync_result['cloud_id']}")
            else:
                print(f"  [CLOUD]    Cloud sync failed (local copy safe): {sync_result.get('error', 'unknown')}")
        
        print()
        return session_id
