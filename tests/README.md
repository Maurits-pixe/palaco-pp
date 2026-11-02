# PP same-context acceptance — operator guide (DRAFT)

Status: **LOCAL ACCEPTANCE HOLD / PRODUCTION HOLD**. This test changes the selected number
and then permanently revokes it; **never run it on a real user or existing registration**.

## Requirements

- Python 3.11+ local PP server running on `http://127.0.0.1:8765/`
- Node.js 20+ and a separately installed `@playwright/test` (not a PP runtime dependency)
- A *new, explicitly approved, disposable* local PP account with ten offered options and **no prior selection**
- A Playwright storageState JSON file containing that account's local session cookie, stored outside Git

## Run (PowerShell)

```powershell
python .\server.py --check
python .\server.py
# In a second terminal, install the test runner in an isolated disposable Node environment.
# Make @playwright/test available to this repository's test runner.
$env:PP_BASE_URL = "http://127.0.0.1:8765/"
$env:PP_TEST_STORAGE_STATE = "C:\secure-test-only\pp-demo-storage-state.json"
$env:PP_DESTRUCTIVE_BROWSER_ACCEPTANCE = "YES"
npx playwright test --config=playwright.config.cjs
```

Ensure the local server is actually running, and that the storageState cookie belongs
to the disposable, unselected account **before** enabling the last environment variable.
The test refuses non-loopback URLs, doesn't create a new context, and uses the existing
`browser_acceptance.js` end-to-end assertions for persistent selection and revocation.
The case is skipped unless explicit opt-in and storageState are present.

**Security:** storageState files contain session credentials. Do not attach them to PRs,
traces, screenshots or CI artifacts. Do not commit them. Delete after the test, revoke
the session, and avoid copying production data.

## Evidence required

Capture commit SHA, run ID, PASS/FAIL, screenshot or sanitized trace on failure,
and human review. Keep production, telecom, WhatsApp/SMS and definitive P.P. identity
registration **HOLD**. No test execution or Playwright PASS is claimed merely by
adding this code.
