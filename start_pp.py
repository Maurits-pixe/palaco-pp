"""Start PALACO P.P. from its extracted folder, using the current Python."""

import sys
import argparse
import json
import os
from pathlib import Path
import socket


def diagnose(arguments):
    parser = argparse.ArgumentParser(description="Controleer de lokale P.P.-startvoorwaarden zonder data te wijzigen.")
    parser.add_argument("--diagnose", action="store_true")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--db", type=Path, default=Path(__file__).resolve().parent / "data" / "palaco.sqlite3")
    args = parser.parse_args(arguments)
    if not 1 <= args.port <= 65535:
        parser.error("poort moet tussen 1 en 65535 liggen")
    checks = {"python": "PASS" if sys.version_info >= (3, 11) else "FAIL"}
    try:
        with socket.socket() as probe:
            if sys.platform == "win32":
                probe.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
            probe.bind(("127.0.0.1", args.port))
        checks["port"] = "PASS"
    except OSError:
        checks["port"] = "BLOCKED"
    ancestor = args.db.resolve().parent
    while not ancestor.exists() and ancestor != ancestor.parent:
        ancestor = ancestor.parent
    checks["directory_access"] = "PASS" if ancestor.is_dir() and os.access(ancestor, os.W_OK | os.X_OK) else "BLOCKED"
    try:
        if args.db.exists():
            with args.db.open("rb") as source:
                header = source.read(16)
            checks["database_header"] = "PASS" if header == b"SQLite format 3\x00" else "FAIL"
            checks["database_access"] = "PASS" if os.access(args.db, os.R_OK | os.W_OK) else "BLOCKED"
        else:
            checks["database_header"] = "NEW_DATABASE"
    except OSError:
        checks["database_header"] = "BLOCKED"
    ready = all(value not in {"FAIL", "BLOCKED"} for value in checks.values())
    print(json.dumps({"ready": ready, "checks": checks,
                      "note": "Momentopname; poort en toegang kunnen veranderen. Geen database-inhoud gecontroleerd. Gebruik --check voor de bestaande database-integriteitscontrole."}, ensure_ascii=False, indent=2))
    return 0 if ready else 1


def main():
    if "--diagnose" in sys.argv[1:]:
        return diagnose(sys.argv[1:])
    if sys.version_info < (3, 11):
        print("P.P. heeft Python 3.11 of hoger nodig. Installeer Python en probeer opnieuw.",
              file=sys.stderr)
        return 1
    try:
        from server import main as run_server
        print("PALACO P.P. — lokaal prototype", flush=True)
        print("Open na de start http://127.0.0.1:8765/ in je browser.", flush=True)
        print("Gebruik je --port, open dan dat poortnummer. Stop met Ctrl+C.", flush=True)
        return run_server()
    except KeyboardInterrupt:
        return 0
    except OSError as error:
        print("P.P. kon niet starten: %s" % error, file=sys.stderr)
        print("Controleer of de poort vrij is en de projectmap schrijfbaar is. "
              "Er is geen ander proces gestopt.", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
