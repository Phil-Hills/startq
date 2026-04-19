"""
startq.cli - The Command Line Interface
"""

import argparse
import sys
from .brain import BrainManager

CUBE = "\u25c8"
CYAN = "\033[96m"
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
            config = brain.get_config()
            identity = config.get("identity")
            if identity and identity != "unknown-operator":
                print(f"  --> LOCAL IDENTITY ... ok [{identity}]")
            else:
                print(f"  --> LOCAL IDENTITY ... missing (run init, or edit config.json)")
            
            if brain.state_file.exists():
                print("  --> SESSION STATE  ... ok")
            else:
                print("  --> SESSION STATE  ... missing")
                
            boot_data = brain.boot_session()
            session_id = boot_data["session_id"]
            print(f"\nStartQ Boot Sequence Complete. Runtime active. [Session ID: {session_id}]\n")
        except FileNotFoundError as e:
            print(f"\n[!] FATAL: {e}")
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
