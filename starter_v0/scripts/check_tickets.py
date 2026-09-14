import argparse
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]
TICKET_DIR = ROOT / "tickets"


def list_tickets() -> list[Path]:
    if not TICKET_DIR.exists():
        return []
    return sorted(TICKET_DIR.glob("*.json"))


def clean_tickets() -> int:
    tickets = list_tickets()
    count = 0
    for ticket in tickets:
        try:
            ticket.unlink()
            count += 1
            print(f"Deleted junk ticket: {ticket.name}")
        except Exception as exc:
            print(f"Failed to delete {ticket.name}: {exc}", file=sys.stderr)
    return count


def verify_gitignore() -> bool:
    gitignore_path = ROOT / ".gitignore"
    if not gitignore_path.exists():
        print("WARNING: starter_v0/.gitignore does not exist!", file=sys.stderr)
        return False
    content = gitignore_path.read_text(encoding="utf-8")
    is_ignored = "/tickets/" in content or "tickets/" in content
    if is_ignored:
        print("PASS: /tickets/ is properly configured in .gitignore.")
    else:
        print("FAIL: /tickets/ is MISSING from .gitignore!", file=sys.stderr)
    return is_ignored


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit and clean generated tickets to prevent junk tickets in git repo.")
    parser.add_argument("--clean", action="store_true", help="Remove all generated ticket JSON files.")
    args = parser.parse_args()

    print("=== TICKET AUDIT & CLEANUP INSPECTION ===")
    verify_gitignore()

    tickets = list_tickets()
    print(f"Total tickets found in {TICKET_DIR}: {len(tickets)}")
    for t in tickets:
        print(f"  - {t.name}")

    if args.clean:
        deleted = clean_tickets()
        print(f"Successfully cleaned {deleted} ticket files.")
    elif tickets:
        print("\nNotice: If you are preparing to submit, run with --clean to remove all local generated tickets:")
        print("  python scripts/check_tickets.py --clean")


if __name__ == "__main__":
    main()
