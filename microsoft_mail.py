"""Local delegated Microsoft SMTP authentication; no account passwords."""

import os
from pathlib import Path
import re
import sys


SCOPES = ["https://outlook.office.com/SMTP.Send"]
AUTHORITY = "https://login.microsoftonline.com/consumers"


class MicrosoftMailError(Exception):
    pass


def build_application(client_id, cache_path):
    try:
        import msal
        from msal_extensions import FilePersistenceWithDataProtection, PersistedTokenCache
    except ImportError as error:
        raise MicrosoftMailError(
            "Installeer eerst: python -m pip install -r .\\requirements-mail.txt"
        ) from error
    if sys.platform != "win32":
        raise MicrosoftMailError("Deze lokale Microsoft-koppeling vereist Windows DPAPI.")
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    persistence = FilePersistenceWithDataProtection(str(cache_path))
    if not persistence.is_encrypted:
        raise MicrosoftMailError("Tokenopslag is niet versleuteld; aanmelding geblokkeerd.")
    return msal.PublicClientApplication(
        client_id, authority=AUTHORITY,
        token_cache=PersistedTokenCache(persistence), timeout=20,
    )


class MicrosoftMailer:
    def __init__(self, client_id, sender, cache_path):
        if not re.fullmatch(
            r"[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}", client_id
        ):
            raise MicrosoftMailError("Stel PP_MICROSOFT_CLIENT_ID in op je eigen Application (client) ID.")
        self.sender = sender
        try:
            self.app = build_application(client_id, cache_path)
        except MicrosoftMailError:
            raise
        except (OSError, ValueError, RuntimeError) as error:
            raise MicrosoftMailError("Microsoft-client of versleutelde cache kon niet worden geopend.") from error

    def access_token(self):
        try:
            accounts = self.app.get_accounts(username=self.sender)
            if len(accounts) != 1:
                raise MicrosoftMailError(
                    "Geen unieke Microsoft-aanmelding voor dit adres. Voer --microsoft-login uit."
                )
            result = self.app.acquire_token_silent(SCOPES, account=accounts[0])
        except MicrosoftMailError:
            raise
        except (OSError, ValueError, RuntimeError) as error:
            raise MicrosoftMailError("Microsoft-tokenvernieuwing mislukt; meld lokaal opnieuw aan.") from error
        if (not result or not isinstance(result.get("access_token"), str)
                or not result["access_token"]):
            raise MicrosoftMailError("Microsoft-toestemming ontbreekt of is verlopen; voer --microsoft-login uit.")
        return result["access_token"]

    def login(self):
        try:
            flow = self.app.initiate_device_flow(scopes=SCOPES)
            if "user_code" not in flow:
                raise MicrosoftMailError("Microsoft-aanmelding kon niet worden gestart.")
            print("Open https://microsoft.com/devicelogin in je eigen browser.")
            print("Voer deze tijdelijke code alleen daar in:", flow["user_code"])
            print("Meld aan met het ingestelde afzenderadres en beoordeel de toestemming.")
            result = self.app.acquire_token_by_device_flow(flow)
        except MicrosoftMailError:
            raise
        except (OSError, ValueError, RuntimeError) as error:
            raise MicrosoftMailError("Microsoft-aanmelding is mislukt; probeer opnieuw.") from error
        if not result or "access_token" not in result:
            raise MicrosoftMailError("Microsoft-aanmelding niet voltooid of toestemming geweigerd.")
        username = result.get("id_token_claims", {}).get("preferred_username", "")
        if username.casefold() != self.sender.casefold():
            # Remove only the newly acquired account, not other cached identities.
            account_id = result.get("id_token_claims", {}).get("oid")
            for account in self.app.get_accounts():
                if account.get("local_account_id") == account_id:
                    self.app.remove_account(account)
            raise MicrosoftMailError("Verkeerd Microsoft-account; gebruik exact het ingestelde afzenderadres.")
        self.access_token()
        print("Microsoft-aanmelding opgeslagen met Windows-versleuteling. Er is geen e-mail verstuurd.")


def configured_mailer(sender):
    client_id = os.environ.get("PP_MICROSOFT_CLIENT_ID", "").strip()
    cache_path = Path(__file__).resolve().parent / "data" / f"microsoft-{client_id}.bin"
    return MicrosoftMailer(client_id, sender, cache_path)
