# PALACO Phone — Offline-first capability v0.1

**Status:** IMPLEMENTED IN DRAFT PR ONLY · STATIC VALIDATION PASS · RUNTIME/BROWSER NOT EXECUTED · PRODUCTION HOLD

## Implemented

- `static/sw.js`: versioned app-shell cache, background update and offline navigation fallback. **Never intercepts `/api/`**, cross-origin or POST requests. Consequently no cached auth/session/number selection.
- `static/offline.html`, `static/offline.css`, `static/offline.js`: standalone private-device concept atelier; IndexedDB stores up to 100 small local, non-sensitive drafts; manual JSON import/export; no cloud calls, no P.P. number issuance.
- `static/app.js`: registers service worker on secure contexts (loopback localhost/127.0.0.1 for development, HTTPS for future).
- `static/index.html`: Offline Atelier link.
- `server.py`: serves the four new same-origin static assets. The Python/SQLite backend still works completely offline on the same machine while its process is running.

## Initial caching requirement

First visit must happen while the local server/site is available so the service worker can install and cache the shell. Then, after a reload / service worker control, `/offline.html` can be used with no internet or with the local server stopped (assuming the browser retained its cache). A fresh browser/device with no cache cannot download the offline app out of thin air.

## Non-negotiable identity boundary

P.P. selected-number uniqueness, withdrawal, authenticated cross-device identity and admission must be verified by the server. The offline atelier never claims to perform these operations. A ten-digit P.P. number is an **identifier**, not a secret, local encryption key, password or proof of authority.

## Security and resilience limitations

- IndexedDB is local browser storage; user/browser can clear it. It is **not encrypted**. Do not store passwords, recovery keys or sensitive personal records.
- JSON export is plaintext and should be stored safely. Import validates schema, size, field lengths and maximum count, but is not a provenance receipt or signature.
- Offline work cannot know whether an account has been revoked or rights changed. Fail closed for any operation involving authority.
- Browser-cache eviction, private mode, browser upgrades, storage quotas, power loss and device failure can remove drafts. Export manually and test restore.
- Online account login, recovery, sync, real-number registration, mobile installation and durable encrypted backups are not implemented here.

## Verification actually done

- JavaScript syntactic parsing: `sw.js`, `offline.js`, `app.js` — PASS.
- HTML-to-JS referenced IDs in offline view — PASS.
- Server static route wiring, UI link, worker registration, and API exclusion — static inspection PASS.
- Python unit tests, browser install/cache/offline/reload/restore, device loss and negative auth tests — NOT EXECUTED.
- No live Supabase SQL, Site deployment, issuance, external migration or telecom change.

## Browser acceptance when environment available

1. Run on a new synthetic test browser profile with local P.P. server running.
2. Load `/`, open `/offline.html`, save a harmless concept, export it.
3. Turn the machine's network off, and stop the local Python server only in a disposable QA environment. Reload the offline page: it should remain available from the worker; verify draft remains.
4. Import the file in a separate *synthetic* browser profile after first caching the app; verify content and caps. Do not use private data.
5. Confirm `/api/pp/me` and `/api/pp/select` never return cached success offline. The browser must not claim ACTIVE or official issuance.
6. Restore service; verify offline page remains accessible and no automatic cloud mutation occurred.
7. Test browser storage cleared and service worker unregistered: expected loss/unavailability warning, no fake recovery.

**TRIAS:** offline capability is not authority.  
**ORACLE:** source checks only; browser evidence pending.  
**MENTOR:** next implement local export integrity and browser regression harness; then optional encrypted device-bound private drafts, without deriving any key from P.P. digits.
