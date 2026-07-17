"""
startq.cli - The Command Line Interface
=========================================
Commands:
    startq init         Initialize the local brain
    startq boot         Boot a session (load context)
    startq record       Record an activity (AutoQ)
    startq log          View recorded activities (AutoQ)
    startq end          Quick session close
    startq shutdown     Full graceful shutdown (EndQ)
    startq upgrade      Connect to cloud brain
    startq status       Show current status
"""

import argparse
import getpass
import sys
import subprocess
import shlex
import json
from pathlib import Path
from .brain import BrainManager

CUBE = "\u25c8"
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
DIM = "\033[2m"
BOLD = "\033[1m"
RESET = "\033[0m"

def banner():
    print(f"\n{CYAN}{CUBE}{RESET} {BOLD}StartQ{RESET} \u2014 Boot, monitor, and shut down your AI workflow\n")

def main():
    parser = argparse.ArgumentParser(
        description="StartQ - Your AI workflow is a computer. Boot it like one."
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # ─── init ────────────────────────────────────────────────────────────
    subparsers.add_parser("init", help="Initialize the local StartQ Brain")

    # ─── boot (StartQ) ──────────────────────────────────────────────────
    boot_p = subparsers.add_parser("boot", help="Boot a new session (StartQ)")
    boot_p.add_argument("--cloud", action="store_true", help="Enable cloud sync")
    boot_p.add_argument("--local", action="store_true", help="Force local-only")
    boot_p.add_argument(
        "--allow-legacy",
        action="store_true",
        help="Allow one reviewed StartQ <=0.4 unkeyed receipt",
    )

    # ─── record (AutoQ) ─────────────────────────────────────────────────
    rec_p = subparsers.add_parser("record", help="Record an activity (AutoQ)")
    rec_p.add_argument("message", type=str, help="What happened")
    rec_p.add_argument("--category", "-t", type=str, default="note",
                       choices=["note", "decision", "bug", "milestone", "action", "idea"],
                       help="Category of the record")

    # ─── log (AutoQ) ────────────────────────────────────────────────────
    log_p = subparsers.add_parser("log", help="View recorded activities (AutoQ)")
    log_p.add_argument("--last", "-n", type=int, default=20, help="Number of records")
    log_p.add_argument("--search", "-s", type=str, help="Search records")
    log_p.add_argument("--date", "-d", type=str, help="Filter by date (YYYY-MM-DD)")
    log_p.add_argument("--export", type=str, choices=["json", "text", "jsonl"],
                       help="Export format")
    log_p.add_argument("--summary", action="store_true", help="Show recording summary")

    # ─── end (quick close) ──────────────────────────────────────────────
    end_p = subparsers.add_parser("end", help="Quick session close")
    end_p.add_argument("--context", "-c", type=str, required=True,
                       help="Session summary")
    end_p.add_argument("--cloud", action="store_true")
    end_p.add_argument("--local", action="store_true")

    # ─── shutdown (EndQ - full graceful) ─────────────────────────────────
    shut_p = subparsers.add_parser("shutdown", help="Full graceful shutdown (EndQ)")
    shut_p.add_argument("--context", "-c", type=str, required=True,
                        help="Session summary")
    shut_p.add_argument("--archive", action="store_true",
                        help="Embed today's recordings in the receipt")
    shut_p.add_argument("--cloud", action="store_true")
    shut_p.add_argument("--local", action="store_true")

    # ─── upgrade ─────────────────────────────────────────────────────────
    up_p = subparsers.add_parser("upgrade", help="Connect to cloud Brain")
    up_p.add_argument("--url", type=str, help="Cloud Brain URL")
    up_p.add_argument("--key", type=str, help="API key (prefer prompt or STARTQ_CLOUD_API_KEY)")

    # ─── status ──────────────────────────────────────────────────────────
    subparsers.add_parser("status", help="Show StartQ status")

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(1)

    banner()
    brain = BrainManager()

    # ─── INIT ────────────────────────────────────────────────────────────
    if args.command == "init":
        brain.init_brain()

    # ─── BOOT (StartQ) ──────────────────────────────────────────────────
    elif args.command == "boot":
        try:
            use_cloud = args.cloud and not args.local

            print(f"{DIM}  [BIOS] System Check ................ OK{RESET}")
            brain.check_health()
            print(f"{DIM}  [POST] Reading physical memory ..... OK{RESET}")

            config = brain.get_config()
            identity = config.get("identity")
            if identity and identity != "unknown-operator":
                print(f"{DIM}  [AUTH] Identity verified ........... [{identity}]{RESET}")
            else:
                print(f"{YELLOW}  [AUTH] Identity missing! ........... [run init]{RESET}")

            if brain.state_file.exists():
                print(f"{DIM}  [DISK] Session state block ......... attached{RESET}")

            cloud_cfg = config.get("cloud", {})
            if cloud_cfg.get("enabled") and not args.local:
                use_cloud = True
                print(f"{DIM}  [CLOUD] Brain endpoint ............ connected{RESET}")
            else:
                print(f"{DIM}  [CLOUD] Brain endpoint ............ local-only{RESET}")

            # Check recordings
            from .autoq import SessionRecorder
            recorder = SessionRecorder()
            summary = recorder.get_session_summary()
            if summary["total_records"] > 0:
                print(f"{DIM}  [AUTOQ] Recordings ................ {summary['total_records']} entries across {summary['total_sessions']} sessions{RESET}")

            daemons = config.get("daemons", {})
            if daemons:
                print(f"{DIM}  [MESH] Waking local agent daemons..{RESET}")
                for name, cmd in daemons.items():
                    print(f"{DIM}    \u251c\u2500\u2500> [ACTIVE] {name}{RESET}")
                    try:
                        subprocess.Popen(shlex.split(cmd),
                                         stdout=subprocess.DEVNULL,
                                         stderr=subprocess.DEVNULL)
                    except Exception as e:
                        print(f"{YELLOW}    \u2514\u2500\u2500> [FAILED] {name}: {e}{RESET}")

            print(f"{DIM}  [BOOT] Handing off to local kernel..{RESET}\n")

            boot_data = brain.boot_session(
                use_cloud=use_cloud,
                allow_legacy=args.allow_legacy,
            )
            sid = boot_data["session_id"]
            cloud_tag = f" | Cloud: \u2713" if boot_data.get("cloud_connected") else ""
            if boot_data.get("recent_context"):
                print(f"\n{BOLD}  Restored context:{RESET}")
                print(f"  {boot_data['recent_context']}")
            print(f"\n{GREEN}\u25b6 StartQ OS Loaded. System Active.{RESET} [Session: {sid[:8]}]{cloud_tag}\n")

        except FileNotFoundError as e:
            print(f"\n{RED}[!] FATAL: {e}{RESET}")
            sys.exit(1)
        except Exception as e:
            print(f"\n{RED}[!] FATAL KERNEL PANIC: {e}{RESET}")
            sys.exit(1)

    # ─── RECORD (AutoQ) ─────────────────────────────────────────────────
    elif args.command == "record":
        from .autoq import SessionRecorder
        recorder = SessionRecorder()
        entry = recorder.record(args.message, category=args.category)

        cat_colors = {
            "note": DIM, "decision": CYAN, "bug": YELLOW,
            "milestone": GREEN, "action": BOLD, "idea": CYAN,
        }
        color = cat_colors.get(args.category, DIM)
        print(f"  {GREEN}\u2713{RESET} Recorded [{color}{args.category.upper()}{RESET}] {args.message}")
        print(f"  {DIM}  ID: {entry['id']}  |  {entry['timestamp'][:19]}{RESET}\n")

    # ─── LOG (AutoQ) ────────────────────────────────────────────────────
    elif args.command == "log":
        from .autoq import SessionRecorder
        recorder = SessionRecorder()

        if args.summary:
            summary = recorder.get_session_summary()
            print(f"  Total records:  {summary['total_records']}")
            print(f"  Total sessions: {summary['total_sessions']}")
            print(f"  Storage:        {summary['recordings_dir']}")
            if summary['dates']:
                print(f"  Date range:     {summary['dates'][0]} to {summary['dates'][-1]}")
            print()
            sys.exit(0)

        if args.export:
            date = args.date
            output = recorder.export_session(date=date, format=args.export)
            print(output)
            sys.exit(0)

        records = recorder.read_records(
            limit=args.last,
            search=args.search,
            date=args.date,
        )

        if not records:
            print(f"  {DIM}No recordings found.{RESET}")
            print(f"  {DIM}Record something: startq record \"your note here\"{RESET}\n")
            sys.exit(0)

        cat_icons = {
            "note": "\u2502", "decision": "\u25c6", "bug": "\u2716",
            "milestone": "\u2605", "action": "\u25b6", "idea": "\u2737",
        }
        cat_colors = {
            "note": DIM, "decision": CYAN, "bug": YELLOW,
            "milestone": GREEN, "action": BOLD, "idea": CYAN,
        }

        print(f"  {BOLD}Session Log{RESET} {DIM}({len(records)} entries){RESET}\n")
        for r in records:
            ts = r.get("timestamp", "?")[:19].replace("T", " ")
            cat = r.get("category", "note")
            msg = r.get("message", "")
            icon = cat_icons.get(cat, "\u2502")
            color = cat_colors.get(cat, DIM)
            print(f"  {DIM}{ts}{RESET}  {color}{icon} [{cat.upper()}]{RESET} {msg}")
        print()

    # ─── END (quick close) ──────────────────────────────────────────────
    elif args.command == "end":
        try:
            use_cloud = args.cloud and not args.local
            brain.end_session(args.context, use_cloud=use_cloud)
        except Exception as e:
            print(f"\n{RED}[!] FATAL: {e}{RESET}")
            sys.exit(1)

    # ─── SHUTDOWN (EndQ - full graceful) ─────────────────────────────────
    elif args.command == "shutdown":
        from .endq import SessionShutdown
        shutdown = SessionShutdown()

        use_cloud = args.cloud and not args.local

        print(f"{DIM}  [TEARDOWN] Archiving session recordings...{RESET}")
        records_count = shutdown.archive_recordings()
        if records_count:
            print(f"{DIM}    \u2514\u2500\u2500> {records_count} records archived{RESET}")
        else:
            print(f"{DIM}    \u2514\u2500\u2500> no recordings today{RESET}")

        print(f"{DIM}  [TRANSCRIPT] Saving chat session...{RESET}")
        txt_path, conv_id, transcript_content = shutdown.save_transcript()
        if txt_path:
            print(f"{DIM}    \u2514\u2500\u2500> saved: {txt_path}{RESET}")
        elif conv_id:
            print(f"{DIM}    \u2514\u2500\u2500> session {conv_id[:12]}... has no content yet{RESET}")
        else:
            print(f"{DIM}    \u2514\u2500\u2500> no IDE session found{RESET}")

        print(f"{DIM}  [SNAPSHOT] Capturing git state...{RESET}")
        git = shutdown.capture_git_state()
        if git:
            branch = git.get("branch", "?")
            dirty = len(git.get("modified_files", []))
            print(f"{DIM}    \u2514\u2500\u2500> branch: {branch} | {dirty} uncommitted file(s){RESET}")
        else:
            print(f"{DIM}    \u2514\u2500\u2500> no git repo detected{RESET}")

        print(f"{DIM}  [RECEIPT] Writing signed session receipt...{RESET}")
        session_id = shutdown.shutdown(
            context=args.context,
            archive=args.archive,
            use_cloud=use_cloud,
            transcript=(txt_path, conv_id, transcript_content),
        )
        print(f"{DIM}    \u2514\u2500\u2500> {session_id}{RESET}")

        if use_cloud:
            print(f"{DIM}  [CLOUD] Syncing to cloud brain...{RESET}")

        print(f"\n{GREEN}\u25c8 EndQ complete.{RESET} Session closed cleanly.")
        print(f"  {DIM}Receipt: .startq/brain/{session_id}.json{RESET}")
        if txt_path:
            print(f"  {DIM}Transcript: {txt_path}{RESET}")
        if records_count:
            print(f"  {DIM}Records: {records_count} entries archived{RESET}")
        print()

    # ─── UPGRADE ─────────────────────────────────────────────────────────
    elif args.command == "upgrade":
        try:
            brain.check_health()
        except FileNotFoundError:
            print(f"  [!] Run 'startq init' first.")
            sys.exit(1)

        config = brain.get_config()

        brain_url = args.url
        if not brain_url:
            try:
                brain_url = input(f"  {CYAN}Cloud Brain URL:{RESET} ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\n  Cancelled.")
                sys.exit(0)

        if not brain_url:
            print("  [!] No URL provided.")
            sys.exit(1)

        api_key = args.key
        if not api_key:
            try:
                api_key = getpass.getpass(f"  {CYAN}API Key (Enter to skip):{RESET} ").strip()
            except (EOFError, KeyboardInterrupt):
                api_key = ""

        print(f"\n  Testing connection to {brain_url}...")
        try:
            from .cloud_brain import CloudBrainClient
            client = CloudBrainClient(brain_url=brain_url, api_key=api_key)
            if client.health():
                print(f"  {GREEN}\u2713 Cloud Brain is healthy.{RESET}")
            else:
                print(f"  {YELLOW}[!] Brain did not respond. Saving config anyway.{RESET}")
        except Exception as e:
            print(f"  {YELLOW}[!] Connection failed: {e}. Saving config anyway.{RESET}")

        from .credentials import write_cloud_api_key
        key_file = write_cloud_api_key(brain.root_dir, api_key)
        config["cloud"] = {
            "brain_url": brain_url,
            "api_key_storage": "user-config" if key_file else None,
            "enabled": True,
        }
        brain.save_config(config)

        print(f"\n  {GREEN}\u2713 Cloud Brain configured.{RESET}")
        print(f"  {DIM}  Sessions will auto-sync on boot and shutdown.{RESET}\n")

    # ─── STATUS ──────────────────────────────────────────────────────────
    elif args.command == "status":
        try:
            brain.check_health()
            config = brain.get_config()
            sessions = sorted(brain.brain_dir.glob("*.json"))

            print(f"  Identity:    {config.get('identity', 'unknown')}")
            print(f"  Brain:       {brain.brain_dir.absolute()}")
            print(f"  Sessions:    {len(sessions)}")

            # Recordings
            from .autoq import SessionRecorder
            recorder = SessionRecorder()
            rec_summary = recorder.get_session_summary()
            print(f"  Recordings:  {rec_summary['total_records']} entries across {rec_summary['total_sessions']} days")

            cloud_cfg = config.get("cloud", {})
            if cloud_cfg.get("enabled"):
                print(f"  Cloud:       {GREEN}\u2713 enabled{RESET} ({cloud_cfg.get('brain_url', '?')})")
            else:
                print(f"  Cloud:       local-only")

            if sessions:
                latest = sessions[-1]
                import os
                data = json.loads(latest.read_text())
                ctx = data.get("context", "")
                print(f"\n  Latest session:")
                print(f"    ID:        {data.get('session_id', '?')[:8]}")
                print(f"    Time:      {data.get('timestamp', '?')[:19]}")
                print(f"    Context:   {ctx[:80]}{'...' if len(ctx) > 80 else ''}")

            print()
        except FileNotFoundError:
            print(f"  StartQ not initialized. Run 'startq init' first.\n")
