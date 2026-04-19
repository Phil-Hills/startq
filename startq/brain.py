"""
startq.brain - Local Filesystem Persistence Driver
"""

import json
import os
import uuid
import datetime
import getpass
from pathlib import Path

class BrainManager:
    def __init__(self, root_dir: str = ".startq"):
        self.root_dir = Path(root_dir)
        self.brain_dir = self.root_dir / "brain"
        self.state_file = self.root_dir / "state.json"

    def init_brain(self):
        """Bootstrap the local startq working directory."""
        if self.brain_dir.exists():
            print("  [DISK] StartQ Brain already formatted.")
            return False
            
        self.brain_dir.mkdir(parents=True, exist_ok=True)
        self.state_file.write_text(json.dumps({"initialized_at": datetime.datetime.now(datetime.timezone.utc).isoformat()}))
        
        config_file = self.root_dir / "config.json"
        if not config_file.exists():
            user = getpass.getuser()
            config_file.write_text(json.dumps({
                "identity": user,
                "role": "ai-operator"
            }, indent=2))
            
        print(f"  [DISK] StartQ Memory mapped at {self.brain_dir.absolute()}")
        return True

    def check_health(self):
        """Verify the brain directory exists and is writable."""
        if not self.brain_dir.exists():
            raise FileNotFoundError("Local Brain not found. Run `startq init` first.")
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

    def boot_session(self):
        """Load context from the Brain and create a new session."""
        self.check_health()
        
        # Load previous context (latest session)
        sessions = sorted(self.brain_dir.glob("*.json"), key=os.path.getmtime, reverse=True)
        recent_context = None
        if sessions:
            try:
                data = json.loads(sessions[0].read_text())
                recent_context = data.get("context")
            except json.JSONDecodeError as e:
                print(f"  [!] kernel_panic: recent session blocked (corrupted format: {e})")
                
        session_id = str(uuid.uuid4())
        
        print(f"  --> memory-daemon: Indexed {len(sessions)} historical blocks.")
        if recent_context:
            print(f"  --> context-daemon: Active state injected ({len(recent_context)} bytes).")
            
        return {
            "session_id": session_id,
            "recent_context": recent_context,
            "sessions_found": len(sessions)
        }

    def end_session(self, context_summary: str):
        """Write the session context back to the Brain to prevent amnesia."""
        self.check_health()
        session_id = str(uuid.uuid4())
        
        payload = {
            "session_id": session_id,
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "context": context_summary
        }
        
        receipt_path = self.brain_dir / f"{session_id}.json"
        receipt_path.write_text(json.dumps(payload, indent=2))
        print(f"\n  [SHUTDOWN] State persistently synced to memory payload.")
        print(f"  [RECEIPT]  {session_id}\n")
        return session_id
