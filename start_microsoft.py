"""Start local PP with Microsoft mail, without changing the parent environment."""

import argparse
import os
from pathlib import Path
import re
import socket
import subprocess
import sys

from server import PPError, Store


ROOT = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--client-id", required=True)
    parser.add_argument("--sender", required=True)
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--login-only", action="store_true")
    parser.add_argument("--reauthenticate", action="store_true")
    args = parser.parse_args()
    if not re.fullmatch(
        r"[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}", args.client_id
    ):
        parser.error("--client-id moet de Application (client) ID van je eigen app zijn")
    try:
        sender = Store.validate_email(args.sender)
    except PPError:
        parser.error("--sender moet een geldig ASCII-mailadres zijn")
    if not sender or not 1 <= args.port <= 65535:
        parser.error("Afzender ontbreekt of poort ligt niet tussen 1 en 65535")
    if sys.platform != "win32":
        parser.error("De Microsoft-tokenopslag vereist Windows DPAPI")
    if not args.login_only:
        try:
            with socket.socket() as probe:
                probe.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
                probe.bind(("127.0.0.1", args.port))
        except OSError:
            print(
                f"Poort {args.port} is niet beschikbaar. Stop eerst de bestaande server, "
                "of gebruik --login-only voor alleen de aanmelding. Geen proces gestopt.",
                file=sys.stderr,
            )
            return 1

    environment = os.environ.copy()
    environment.update({
        "PP_SMTP_AUTH": "microsoft", "PP_SMTP_FROM": sender,
        "PP_MICROSOFT_CLIENT_ID": args.client_id,
        "PP_SMTP_HOST": "smtp-mail.outlook.com", "PP_SMTP_PORT": "587",
        "PP_SMTP_TLS": "starttls",
    })
    for name in ("PP_SMTP_USER", "PP_SMTP_PASSWORD"):
        environment.pop(name, None)
    server = str(ROOT / "server.py")
    cache = ROOT / "data" / f"microsoft-{args.client_id}.bin"
    try:
        dependencies = subprocess.run(
            [sys.executable, "-c",
             "import msal; from msal_extensions import "
             "FilePersistenceWithDataProtection, PersistedTokenCache"],
            env=environment, check=False,
        )
        if dependencies.returncode:
            print(
                "Installeer de mailpackages met: python -m pip install -r "
                f'"{ROOT / "requirements-mail.txt"}"', file=sys.stderr,
            )
            return 1
        if args.login_only or args.reauthenticate or not cache.is_file():
            print(
                "Meld zelf aan bij Microsoft. Deel de tijdelijke code, wachtwoorden "
                "of tokens niet in de chat.", flush=True,
            )
            result = subprocess.run(
                [sys.executable, server, "--microsoft-login"], env=environment, check=False,
            )
            if result.returncode:
                print("Microsoft-aanmelding niet voltooid. PP is niet gestart.", file=sys.stderr)
                return 1
        if args.login_only:
            print(
                "Aanmelding voltooid; de bestaande server is niet gewijzigd. "
                "Er is geen e-mail verstuurd.\nStop eerst de bestaande server. "
                "Start daarna dezelfde opdracht zonder --login-only."
            )
            return 0
        print(
            f"PP starten op http://127.0.0.1:{args.port}/ met Microsoft-mail. "
            "Stop met Ctrl+C.", flush=True,
        )
        result = subprocess.run(
            [sys.executable, server, "--port", str(args.port)], env=environment, check=False,
        )
        if result.returncode:
            print(
                "PP is met een fout gestopt. Controleer de melding; gebruik "
                "--reauthenticate wanneer Microsoft-toestemming is verlopen.",
                file=sys.stderr,
            )
            return 1
        return 0
    except OSError:
        print("Python-subproces kon niet worden gestart. PP is niet beschikbaar.", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nPP-starter gestopt.")
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
