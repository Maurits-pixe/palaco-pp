# PALACO Phone — Offline browseracceptatie v0.1

Status: IMPLEMENTED TEST HARNESS · NOT EXECUTED
Last Updated: 2026-11-02

## Doel en grenzen

Controleert uitsluitend lokale **conceptnotities** in het Offline Atelier. De harness doet **geen** accountaanmaak, P.P.-nummerselectie, intrekking, Supabase-aanroep of officiële uitgifte.

De bestaande server moet lokaal draaien op http://127.0.0.1:8765. Gebruik een afzonderlijk test-browserprofiel: testconcepten blijven bewust staan als inspecteerbaar bewijs. De test mag niet op een persoonlijk profiel met vertrouwelijke notities worden uitgevoerd.

## Uitvoering

Open in Playwright één bestaande pagina van dezelfde browsercontext op de lokale PALACO-origin. Roep vervolgens aan:

```js
const { runOfflineAtelierAcceptance } = require("./offline_browser_acceptance");
const report = await runOfflineAtelierAcceptance(page);
console.log(report);
```

Voorwaarden:

1. De testpagina staat reeds op een URL onder http://127.0.0.1:8765.
2. Playwright ondersteunt downloads, `download.path()`, `setInputFiles` en `context.setOffline`.
3. De browser ondersteunt IndexedDB, Web Crypto en service workers.
4. De offline shell wordt eerst online geladen; op de offline reload moet deze uit de service-worker-cache komen.
5. Er wordt geen tweede context geopend of browser-storage gewist.

## Controles

1. Lokale opslagindicator wordt actief.
2. Concept wordt geschreven, bevestigd en na reload teruggevonden.
3. Exportbestand bevat schema v2, SHA-256-veld en het concept.
4. Gewijzigde export met oude checksum wordt geweigerd; het ingespoten concept verschijnt niet.
5. Browser wordt offline gezet, pagina wordt herladen en concept blijft leesbaar.
6. Nieuw concept kan offline worden opgeslagen.
7. `finally` herstelt online stand van de testcontext, ook na fout.

## Bewijsgrens

Een geslaagde code- of syntaxcontrole is niet gelijk aan browseracceptatie. Tot een echte run met datum, browser, commit, log en resultaat is vastgelegd: **BROWSER ACCEPTANCE: NOT EXECUTED**. Een SHA-256-controlesom detecteert toevallige of niet-gecompenseerde bestandswijzigingen, maar bewijst **geen identiteit, herkomst of authenticiteit**.

**TRIAS:** testconcepten, geen officiële identiteit. Productie: HOLD.
**ORACLE:** registreer de run en falende stappen; claim geen PASS zonder uitvoering.
**MENTOR:** voer deze kleine same-context regressie eerst lokaal uit, daarna pas mobiele en langdurige offlineproeven.
