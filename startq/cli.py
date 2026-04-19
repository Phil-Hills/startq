"""
startq.cli - The Command Line Interface
"""

import argparse
import sys
import time
import subprocess
import shlex
from .brain import BrainManager

CUBE = "\u25c8"
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
DIM = "\033[2m"
BOLD = "\033[1m"
RESET = "\033[0m"

def banner():
    print(f"\n{CYAN}{CUBE}{RESET} {BOLD}StartQ{RESET} \u2014 Persist session context across AI agent runs\n")

def main():
    parser = argparse.ArgumentParser(description="StartQ - Local-first, zero dependencies.")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Command: init
    init_parser = subparsers.add_parser("init", help="Initialize the local StartQ Brain")
    
    # Command: boot
    boot_parser = subparsers.add_parser("boot", help="Boot a new agent session with verified context")
    
    # Command: end
    end_parser = subparsers.add_parser("end", help="Sync active session context back to the Brain")
    end_parser.add_argument("--context", "-c", type=str, required=True, help="Summary of what the agent learned/did in this session")

    args = parser.parse_args()
    
    if args.command is None:
        parser.print_help()
        sys.exit(1)
        
    banner()
    brain = BrainManager()

    if args.command == "init":
        brain.init_brain()
        
    elif args.command == "boot":
        try:
            print(f"{DIM}  [BIOS] System Check ................ OK{RESET}")
            brain.check_health()
            print(f"{DIM}  [POST] Reading physical memory ..... OK{RESET}")
            
            config = brain.get_config()
            identity = config.get("identity")
            if identity and identity != "unknown-operator":
                print(f"{DIM}  [AUTH] Identity verified ........... [{identity}]{RESET}")
            else:
                print(f"{YELLOW}  [AUTH] Identity missing! ........... [run init, or edit config.json]{RESET}")
            
            if brain.state_file.exists():
                print(f"{DIM}  [DISK] Session state block ......... attached{RESET}")
            else:
                print(f"{YELLOW}  [DISK] Session state block ......... missing{RESET}")
            
            daemons = config.get("daemons", {})
            if daemons:
                print(f"{DIM}  [MESH] Waking local agent daemons..{RESET}")
                for daemon_name, daemon_cmd in daemons.items():
                    print(f"{DIM}    \u251c\u2500\u2500> [ACTIVE] {daemon_name}{RESET}")
                    try:
                        cmd_args = shlex.split(daemon_cmd)
                        subprocess.Popen(cmd_args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    except Exception as e:
                        print(f"{YELLOW}    \u2514\u2500\u2500> [FAILED] {daemon_name}: {e}{RESET}")
            
            print(f"{DIM}  [BOOT] Handing off to local kernel..{RESET}\n")    
                
            boot_data = brain.boot_session()
            session_id = boot_data["session_id"]
            print(f"\n{GREEN}\u25b6 StartQ OS Loaded. System Active.{RESET} [Session ID: {session_id}]\n")
        except FileNotFoundError as e:
            print(f"\n[!] FATAL: {e}")
            sys.exit(1)
        except Exception as e:
            print(f"\n[!] FATAL KERNEL PANIC: {e}")
            sys.exit(1)
            
    elif args.command == "end":
        try:
            brain.end_session(args.context)
        except Exception as e:
            print(f"\n[!] FATAL: {e}")
            sys.exit(1)
            
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
