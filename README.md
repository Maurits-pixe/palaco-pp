# PALACO Phone / lokaal prototype v0.7

## PP-RECOVERY-002 / hersteldossier (bouwfase)

Na aanmelden toont de consumentenpagina een afzonderlijk, alleen-lezen
registratiedossier. De gebruiker kan zelf een JSON-overzicht downloaden met
accountreferentie, lokale registratiestatus en bestaande keuze/tijdstippen.
Er worden geen wachtwoorden, cookies, e-mailadressen, geheugenbanknotities of
sessietokens geëxporteerd. Het overzicht is geen onafhankelijke verificatie:
`identityVerification=NOT_VERIFIED`, `authorization=HOLD`,
`accessDecision=DENY` en `issuance=NOT_AUTHORIZED` zijn vaste grenzen.
De download schrijft niets naar de database en verbindt niets met PALACO ONE.
Deze wijziging is nog niet getest; acceptatie blijft voor de eigenaar.

Een lokale JSON-inspectie kan een eerder geëxporteerd bestand (max. 64 KiB)
vergelijken met de actieve accountreferenties en de actuele P.P.-registratie.
Ongeldige contracten, andere accounts en afwijkende/historische registraties
krijgen afzonderlijke meldingen. De inspector gebruikt uitsluitend de File API
in de browser en schrijft of uploadt geen data. Zelfs een volledige match
betekent **geen** handtekeningcontrole, onafhankelijke identiteitsverificatie,
herstel, autorisatie of PALACO ONE-aanmelding. HOLD/DENY blijven behouden.

## PALACO ONE / handmatige overdracht v0 (DRAFT)

Bij een bestaande `ACTIVE` of `REVOKED` registratie kan de gebruiker een
afzonderlijk `palaco.pp.one.review-handoff.v0`-pakket downloaden. Het bevat
de lokale consumer-/optie-ID, de laatste vier P.P.-cijfers en tijdstippen;
het bevat uitdrukkelijk geen volledig nummer, gebruikersnaam, wachtwoord,
sessie, geheugenbank of e-mailadres. Het bestand wordt niet verstuurd.
De ontvanger moet het als **ongetekende, door gebruiker beheerste input**
behandelen. Status `PENDING_HUMAN_REVIEW`, `NOT_VERIFIED`, `HOLD`, `DENY`,
`NOT_AUTHORIZED` verbiedt automatische accountkoppeling, authenticatie en
uitgifte. Een toekomstig PALACO ONE-importcontract dient eigen server-side
authenticatie, bronbewijs en onafhankelijke beslisregels toe te voegen.

### Ontvangende contractgrens (alleen-lezen, DRAFT)

`review_handoff.py` biedt `parse_review_handoff(raw: bytes)` voor een toekomstige
handmatige beoordelingsroute. De parser weigert onbekende velden, onjuiste
statusovergangen, tijdstempels zonder tijdzone, ongeldige ID's en pakketten
groter dan 16 KiB. Een structurele controle levert uitsluitend
`STRUCTURE_ACCEPTED_UNTRUSTED` met onveranderlijk `HOLD`/`DENY` terug.
De validator heeft geen database-, netwerk-, login-, import- of schrijfrechten.
Er is geen API-route die inkomende gegevens toepast. Deze bouwfase is ongetest.

De consumentenpagina heeft daarnaast een lokale handoff-inspectie voor de
eigenaar. Deze vergelijkt een gekozen bestand met de actuele registratie, zonder
netwerk of opslag. Een overeenkomst is alleen een gebruikersinterface-waarneming;
de striktere Python-parser blijft een afzonderlijke contractgrens. Geen van
beide inspecties bewijst authenticiteit of verleent rechten. Tests zijn aan de
eigenaar voorbehouden.

### Backoffice / lokaal HOLD-beoordelingsrapport (DRAFT)

Het bestaande `/admin`-scherm bevat nu een alleen-lezen werkruimte voor een
door de beheerder gekozen handoff-JSON (max. 16 KiB). De browser beoordeelt
uitsluitend de contractstructuur en berekent lokaal een SHA-256-vingerafdruk.
Er is geen upload, persistente opslag, accountkoppeling of databasewijziging.
De beheerder kan een JSON-rapport downloaden met bestandsvingerafdruk,
structuuruitkomst, optionele niet-persoonsgebonden notitie en onvoorwaardelijk
`NOT_VERIFIED` / `HOLD` / `DENY` / `NOT_AUTHORIZED`. Een hash bewijst geen
herkomst en dit rapport is geen onafhankelijke menselijke verificatie.

### Offline bewijsbinding (DRAFT)

`review_bundle.py` voegt `link_hold_evidence(handoff, report)` toe. Deze
puur lokale, alleen-lezen functie accepteert een strikt P.P.-handoffcontract
en een lokaal HOLD-beoordelingsrapport uitsluitend als de SHA-256-hash van de
exacte handoff-bytes overeenkomt met de rapportreferentie. Beide JSON-parsers
weigeren nu ook dubbele sleutels. Er worden geen namen, nummers of consumer-ID's
in de uitkomst opgenomen. Een geslaagde binding heet
`HASH_MATCH_UNTRUSTED`, met uitsluitend `NOT_VERIFIED`, `HOLD` en `DENY`.
Er bestaat nog geen automatische invoerroute in PALACO ONE. Geen tests of
uitrol uitgevoerd in deze bouwfase.

Het backoffice-scherm kan daarnaast twee lokale bestanden (handoff + HOLD-rapport)
in de browser vergelijken en een beperkte `palaco.pp.evidence-index.v0`
downloaden met uitsluitend de twee bestandsvingerafdrukken en HOLD/DENY.
Dit is een gebruikersinterface-waarneming, geen vervanging van de strengere
Python-bundelcontrole of bewijs van authenticiteit. De bestanden worden
niet geïmporteerd, geüpload of persistent opgeslagen.

`review_index.py` sluit de derde lokale schakel af met
`link_hold_index(handoff, report, index)`. De functie controleert eerst de
strikte handoff/rapport-binding en vervolgens het vaste indexschema, dubbele
JSON-sleutels, tijdstempel, HOLD/DENY-velden en de SHA-256-hashes van **beide**
oorspronkelijke bytebestanden. Bij afwijkingen volgt `PP_INDEX_INVALID`;
bij overeenstemming uitsluitend `THREE_FILE_HASH_MATCH_UNTRUSTED`. Ook deze
controle is geen digitale handtekening, identiteitscontrole, inlogrecht of
uitgifteautoriteit. De nieuwe code is DRAFT; tests en runtimeverificatie
zijn uitgesteld op verzoek van de eigenaar.

De backoffice heeft nu ook een afzonderlijk **drie-bestanden-reviewpaneel**.
Daarin kan de eigenaar de handoff, het HOLD-rapport en de eerder geëxporteerde
bewijsindex lokaal selecteren en hun onderlinge SHA-256-verwijzingen vergelijken.
Na iedere nieuwe bestandskeuze vervalt de eerdere waarneming; de controle is
uitsluitend indicatief en geeft geen bevoegdheid. De browserparser kan (anders
dan de Python-validator) dubbele JSON-sleutels niet zelfstandig uitsluiten.
Daarom vervangt dit paneel de onafhankelijke, strengere validatie niet.
Na een positieve lokale indicatie kan het paneel nu een afzonderlijk
`palaco.pp.chain-observation.v0`-rapport downloaden. Dat bevat alleen de
SHA-256-hashes van de drie exacte bestanden, een waarnemingstijd, een expliciet
`UNSIGNED_LOCAL_BROWSER_OBSERVATION`-herkomstlabel en uitsluitend HOLD/DENY.
Er worden geen identifiers, P.P.-nummers of authenticatiegegevens geëxporteerd.
Bij een nieuwe bestandskeuze vervalt het rapport in het geheugen en wordt de
downloadknop opnieuw geblokkeerd. De uitvoer is niet ondertekend en vormt
geen bewijs van een uitgevoerde menselijke identiteitscontrole.

`review_chain.py` biedt de strengere, lokale controle
`link_hold_chain(handoff, report, index, observation)` voor alle **vier**
oorspronkelijke bytebestanden. Eerst moet de bestaande drie-bestandenketen
strikt geldig zijn. Vervolgens controleert de functie het vaste
`palaco.pp.chain-observation.v0`-contract, de UTC-tijd, dubbele sleutels,
de HOLD/DENY-velden en drie SHA-256-vingerafdrukken. Bij enige afwijking:
`PP_CHAIN_INVALID`; anders uitsluitend
`FOUR_FILE_HASH_MATCH_UNTRUSTED` met onveranderlijke HOLD/DENY-uitkomst.
Dit is geen bewijs van authenticiteit of bevoegdheid. Er is geen automatische
koppeling naar PALACO ONE of uitgifte. Tests blijven NOT EXECUTED op verzoek.

Voor een latere, door de eigenaar uitgevoerde controle is
`REVIEW_044_DRAFT.md` voorbereid, samen met `review_fixtures.py`: negen
synthetische, deterministische vier-bestandenscenario's inclusief
verwachte negatieve weigeringen. De fixtures schrijven niets naar schijf
en voeren geen validators uit. Er worden geen PASS-resultaten geclaimd.
De bijbehorende `review_044_runner.py` is een afzonderlijk, opt-in lokaal
uitvoerscript: zonder expliciete `--run` start geen review. Met `--run --json`
kan de eigenaar later technische waarnemingen naar de terminal laten schrijven.
Het script verandert geen autorisatie en schrijft geen bestanden.
Voor aparte eigenaarwaarnemingen is bovendien de pure functie
`review_044_observations.make_self_report()` voorbereid. Zij markeert elke
ingevoerde waarneming uitsluitend als `SELF_REPORTED` en laat ontbrekende
scenario's `NOT_OBSERVED`; ook deze uitvoer blijft `NOT_VERIFIED` en HOLD/DENY.
De bestaande lokale beheerpagina heeft nu ook het formulier **Review 044 /
mijn eigen waarneming**: selecteer een van de negen scenario's, registreer
expliciet de eigen waarneming en download desgewenst een JSON-zelfrapport.
Het formulier voert geen tests uit, uploadt niets en bewaart invoer alleen
in het geheugen van de open pagina (niet na afmelden of herladen).
Een gelijke uitkomst is `MATCH_CLAIMED`, nooit `PASS` of toestemming;
alle autorisatievelden blijven HOLD/DENY.
Een aparte pure adapter `review_044_identity_preview.py` bereidt een
alleen-lezen PALACO ONE-overdrachtspreview voor. Hij weigert afwijkende
zelfrapportstructuren en geeft nooit identity binding, sessietoegang of
uitgifte vrij. De adapter is DRAFT en niet uitgevoerd of aangesloten.
`review_044_preview_fixtures.py` levert daarbij synthetische positieve en
negatieve bytevoorbeelden met verwachtingen, zonder de adapter aan te roepen.
Ook deze regressies zijn nog niet uitgevoerd.
De afzonderlijke `review_044_preview_runner.py` voert ze alleen uit na
expliciet `--run` (optioneel `--json`); hij schrijft geen bestanden en
maakt geen verbinding met een PALACO ONE-runtime.
Voor de latere handmatige rapportbeoordeling is tevens de pure parser
`review_044_preview_assessment.py` voorbereid. Die vat uitsluitend
geclaimde technische resultaten samen en kan geen onafhankelijke
uitvoering, identiteit of autorisatie bevestigen.
`review_044_owner_review.py` kan later een lokaal, niet-ondertekend
eigenaarwerkblad opstellen dat de ingevoerde technische rapportbytes met
SHA-256 identificeert. Dit is geen authenticiteitsbewijs en geeft nooit
autorisatie vrij.
De lokale backoffice bevat nu tevens een Review 044-eigenaarwerkbladpaneel:
selecteer een bestaand synthetisch technisch JSON-rapport, leg per 13 scenario's
een eigenaarsmarkering vast en download een niet-ondertekend HOLD-werkblad.
De browser voert geen tests of uploads uit. De ingebouwde structuurindicatie
kan dubbele JSON-sleutels niet betrouwbaar afwijzen; de Python-parser hierboven
blijft het striktere controlecontract. De markeringen zijn alleen tijdelijk
in het browsergeheugen; bewaren vereist een expliciete lokale download.
De pure module `review_044_owner_index.py` kan de originele bytes van een
technisch rapport en een eigenaarwerkblad vervolgens fail-closed koppelen tot
een niet-ondertekende bewijsindex met twee SHA-256-vingerafdrukken. Die
index bewijst geen herkomst, identiteit of bevoegdheid en blijft HOLD / DENY.
Ook deze twee-bestandenbinding heeft nu een afzonderlijk paneel in de lokale
backoffice. De gebruiker kiest beide oorspronkelijke JSON-bestanden, laat
uitsluitend een indicatieve browservergelijking maken en kan de bewijsindex
downloaden. De browser weigert structurele mismatches, maar kan dubbele
JSON-sleutels niet strikt detecteren; de Python-module blijft normatief.
Er zijn geen uploads of automatische autorisatieacties.
`review_044_owner_dossier.py` voegt een strikte offline drie-bestandencontrole
toe: het oorspronkelijke technische rapport, het eigenaarwerkblad en de
bewijsindex moeten inhoudelijk en via hun vingerafdrukken overeenkomen.
De uitkomst is uitsluitend `THREE_FILE_HASH_MATCH_UNTRUSTED` en blijft
NOT_VERIFIED / HOLD / DENY; er worden geen tests of runtimeacties gestart.

Zelfstandig prototype met een Nederlandstalige, responsive interface. De lokale
PP-engine gebruikt de Python-standaardbibliotheek; geen externe lettertypen of
analytics. Python 3.11+ vereist. Optionele e-mail gebruikt een externe SMTP-provider;
Microsoft OAuth vereist de packages uit `requirements-mail.txt`.

## Starten

Open PowerShell in deze map:

```powershell
python .\server.py
```

Open **http://127.0.0.1:8765**. Gebruik exact dit adres, niet `localhost`.
Stop met Ctrl+C. Alternatieve poort: `python .\server.py --port 8766`.

```powershell
python -m pip install -r .\requirements-mail.txt
python -m unittest -v
```

De aanvullende Microsoft-tests gebruiken mocks en een echte tijdelijke
Windows-DPAPI-cache, geen echte Microsoft-aanmelding of e-mailbezorging.

Controleer de persistente P.P.-database zonder een webserver te starten:

```powershell
python .\server.py --check
```

De controle rapporteert alleen checks en recordaantallen, nooit P.P.-nummers,
gebruikersnamen, sessies of wachtwoorden. De bestaande database moet aanwezig
zijn. Startupmigraties, zoals het aanvullen van legacy-auditregels, worden eerst
idempotent toegepast; er wordt geen database aangemaakt als het pad ontbreekt.
Een fout resulteert in exitcode 1; een geldige database resulteert in exitcode 0.

## Browseracceptatie op dezelfde pagina

`browser_acceptance.js` exporteert `runPPBrowserAcceptance(page)` voor een bestaande
Playwright-pagina. Meld op die pagina eerst aan op een expliciet goedgekeurd account
met tien aangeboden opties. Er wordt geen nieuwe browsercontext geopend en de test
wisselt, wist of vervangt geen cookies. De test selecteert definitief de derde optie
en trekt het nummer daarna onomkeerbaar in.

De regressie controleert tien unieke nummers, vier werkelijk gerenderde kleuren,
behoud van kleur/volgorde bij herladen, selectie via `data-testid="pp-option-3"`,
bevestiging, behoud van hetzelfde consumer-ID en nummer na herladen, intrekking
en behoud daarvan na herladen. Zowel een tweede selectie als een nieuwe batch
moeten HTTP 409 met `PP_ALREADY_SELECTED` opleveren, zonder de registratie te wijzigen.
Een mislukte controle gooit een fout; een geslaagde test retourneert het bewijsrapport.
De helper gebruikt de Playwright-pagina van de browserharness; hiervoor zijn geen
nieuwe runtime-afhankelijkheden aan de applicatie toegevoegd.

De helper vereist een aangemeld testaccount met `OFFERED` status. Voer hem niet uit
op een account met een bestaande keuze: selectie en intrekking zijn onomkeerbaar.

### Gecontroleerde status

- De 67 Python-tests controleren selectie, database-invarianten, enginehistorie,
  accountisolatie, sessies, wachtwoordvalidatie, login/logout, loginrem,
  geheugenbank-CRUD, validatie, auditprivacy en gescheiden beheerdersrechten.
- Zes aanvullende startertests controleren Microsoft-configuratie, hergebruik
  van tokens, poortconflicten en foutafhandeling zonder netwerk of proceswijzigingen.
- De volledige selectie-/intrekkingsacceptatietest in de browser is nog niet
  uitgevoerd op een ongekozen, aangemeld testaccount.
- **Lokale accountdemo: werkt volgens geautomatiseerde API- en Store-tests.
  Browseracceptatie: nog te controleren. Productie: HOLD.**

## Werking en vormgeving

- Warm gebroken wit, donkergroen en zachte lime-accenten; een digitale P.P.-kaart.
- Tien toegankelijke radiokaarten, toetsenbordbediening, zichtbare focus,
  bevestigingsdialoog, foutmeldingen en een mobiele layout.
- Tien willekeurig gegenereerde nummers, niet numeriek gesorteerd. Kaartkleuren
  blauw, rood, groen en geel worden willekeurig verdeeld. Elke kleur komt minstens
  eenmaal voor; de overige zes kaarten krijgen onafhankelijk een willekeurige
  kleur. Kleurnamen staan ook als tekst op de kaarten. Volgorde en kleuren
  worden samen met de opties opgeslagen en blijven bij herladen gelijk.
- Nummerweergave in groepen van 3 / 3 / 4; de API bewaart exact tien cijfers.
- Een batch per consumer, tien wereldwijd unieke nummers **binnen deze database**.
- Herhaald aanvragen en herladen leveren dezelfde batch op.
- Eén definitieve selectie, ook na intrekking. De andere negen opties vervallen.
- Geen nummerhergebruik, ook niet van vervallen of ingetrokken opties.
- Nummerbereik: 1000000000 t/m 9999999999, zonder PALACO-prefix.
- SQLite `BEGIN IMMEDIATE` serialiseert schrijvers, ook bij gelijktijdige verzoeken.
  Unieke constraints bewaken batch, nummer en selectie. Registratie, vervallen
  opties en audit-event worden samen gecommit of samen teruggedraaid.
- Database-triggers blokkeren verwijderen van batch, optie en selectie,
  verhinderen wijzigingen aan de nummer-/batch-/kleuridentiteit en accepteren
  alleen de statusovergangen `OFFERED -> ACTIVE/EXPIRED` en `ACTIVE -> REVOKED`.
  Een selectierecord moet bij een actieve optie van dezelfde consumer horen;
  intrekking is een eenmalige overgang gekoppeld aan een ingetrokken optie.
- `python .\server.py --check` valideert SQLite- en foreign-key-integriteit,
  exact tien opties en alle vier kleuren per batch, status/selection-invarianten
  en exacte auditdekking (geen ontbrekende, dubbele of verkeerd gekoppelde events)
  van aanbiedingen, selectie en intrekking. Ook controleert het dat geheugenbank-
  auditregels alleen het geheugen-ID bevatten en geen notitie-inhoud. Ongeldige
  audit-JSON blokkeert de historie en laat de controle falen zonder een exception
  weg te moffelen.
- `ACTIVE` is de opgeslagen selectiestatus; geen losse tussenstatus `SELECTED`.
  Dit betekent actieve **lokale identificatie**, geen telecomactivatie.
- Onbekende/inconsistente status blokkeert verdere stappen en wordt niet als succes getoond.

## Identiteit en grenzen

Bij het eerste bezoek wordt een anonieme lokale consumer gemaakt. Bij accountcreatie
wordt diezelfde consumer aan de gebruikersnaam gekoppeld, zodat de huidige batch
of selectie behouden blijft. Bestaande accounts kunnen met hun wachtwoord op een
andere browser aanmelden en zien dan dezelfde server-side registratie.
Maak het eerste account aan in dezelfde browser waarin je de eerdere demo gebruikte
om die bestaande demo-consumer eraan te koppelen.

Accounts gebruiken een unieke gebruikersnaam (3–32 ASCII-letters/cijfers, punt,
koppelteken of underscore) en een wachtwoord van 12–128 tekens. Wachtwoorden worden
met PBKDF2-HMAC-SHA256 (600.000 iteraties en willekeurige salt) gehasht; alleen de
hash wordt opgeslagen. Sessie-ID's zijn willekeurig, server-side opgeslagen als
hash en verlopen na 30 dagen. Login roteert de sessie; logout trekt de huidige
sessie in. P.P.-routes vereisen een account. Een oude, onbekende sessiecookie wordt
gewist; aanmelden kan daarna bestaande accountgegevens terugvinden.

Na vijf onjuiste aanmeldpogingen voor dezelfde gebruikersnaam (ook als die niet
bestaat) wordt verdere aanmelding gedurende 15 minuten afgewezen met HTTP 429.
Deze blokkade wordt opgeslagen, overleeft een serverherstart en wordt na een
succesvolle login verwijderd. Pogingen ouder dan het venster worden opgeschoond.
De rem helpt tegen toevallig raden, maar is geen volwaardige abusepreventie:
een andere lokale gebruiker kan een account tijdelijk blokkeren.

**Dit blijft een lokale prototype-account, geen geverifieerde persoon of officieel
PALACO-ID.** Er is geen e-mail, wachtwoordherstel of MFA.
Bewaar je wachtwoord niet als je het elders gebruikt. Kies een uniek testwachtwoord.
Cookies verwijderen wist alleen de sessie, niet de accountgegevens in de database;
je kunt met je gebruikersnaam en wachtwoord weer aanmelden. Een anonieme demo die
nog niet aan een account gekoppeld was, kan alleen via het oorspronkelijke cookie
worden teruggevonden. Gebruik geen echte persoonsgegevens.

Het lokale HTTP-cookie heeft geen `Secure`-vlag. Dit prototype bindt uitsluitend
op `127.0.0.1`; het is niet ontworpen voor toegang via LAN of internet. Productie
vereist HTTPS, sterke sessie- en accountbeveiliging, abusebeperking, herstelbeleid,
privacybeheer, back-ups en onafhankelijk securityonderzoek.

De server luistert uitsluitend op loopback, controleert Host en Origin en laadt
alleen lokale assets met een strikte Content Security Policy. Alleen POST-verzoeken
vanaf de eigen origin worden geaccepteerd. Geen CORS of externe API-koppelingen.

Data staat in `data\palaco.sqlite3`, inclusief sessies, historie en audit.
Behoud deze database **en** het browsercookie om dezelfde registratie na een
herstart te gebruiken. De database is niet versleuteld; bescherm de lokale map.
Bewaar bij een back-up ook de SQLite WAL-bestanden, of stop eerst de server.
Database verwijderen is geen ondersteunde reset-/herstelprocedure.

De audit is append-only via SQLite-triggers; dit is geen manipulatiebestendig
extern auditlog. Een lokale databasebeheerder kan de triggers verwijderen.
HTTP-fouten worden geaudit waar opslag beschikbaar is; bij opslagfouten wordt
expliciet gelogd en een 503-status teruggegeven.

## API

Alle POST-verzoeken hebben JSON en `Origin: http://127.0.0.1:8765` nodig
(of de gekozen poort). Het sessiecookie moet worden meegestuurd.

| Methode | Pad | Functie |
|---|---|---|
| POST | `/api/session` | Anonieme consumer aanmaken of huidige sessie teruggeven; body `{}` |
| GET | `/api/auth/me` | Aanmeldstatus en gebruikersnaam ophalen |
| POST | `/api/auth/register` | Account koppelen aan huidige consumer; body `{"username":"...","password":"..."}` |
| POST | `/api/auth/login` | Account aanmelden; zelfde bodyvorm als registratie |
| POST | `/api/auth/logout` | Huidige sessie intrekken; body `{}` |
| POST | `/api/pp/options` | Dezelfde tien opties teruggeven; vereist account |
| POST | `/api/pp/select` | Definitief selecteren; body `{"optionId":"..."}` |
| GET | `/api/pp/me` | Status `NEW`, `OFFERED`, `ACTIVE` of `REVOKED`; vereist account |
| GET | `/api/pp/mail` | Eigen bevestigingsstatus en SMTP-beschikbaarheid; vereist account |
| GET | `/api/pp/history` | Persoonsgebonden P.P.-enginehistorie; vereist account |
| POST | `/api/pp/revoke` | Definitief intrekken; vereist account; body `{}` |

Selectie geeft `consumerId`, `ppNumberId`, `ppNumber`, `status`, `selectedAt`.
`POST /api/pp/select` accepteert daarnaast optioneel `email` als tekenreeks.
Fouten geven `{"error":"PP_..."}` met een niet-2xx HTTP-status.
Een vreemde of onbekende optie geeft dezelfde `PP_OPTION_INVALID`-fout, zodat
de API geen informatie over andermans opties prijsgeeft.

De append-only historie registreert iedere aangeboden optie, de definitieve
selectie en intrekking binnen dezelfde SQLite-transactie als de bijbehorende
statuswijziging. `GET /api/pp/history` geeft alleen de eigen P.P.-levenscyclus
terug: sequentie, eventtype, tijdstip, batch-/optie-ID, nummer en kleur. Login-,
logout- en generieke foutgebeurtenissen worden niet via dit endpoint getoond.
Oudere selectie-events worden bij het lezen verrijkt met nummer en kleur uit de
eigen optie-record; de bestaande auditrecords zelf worden niet gewijzigd.
Bij het opstarten worden ontbrekende offer-events voor bestaande databases
eenmalig aangevuld met de oorspronkelijke `offered_at`-tijd. Herhaald herstarten
voegt geen duplicaten toe. De geschiedenis blijft chronologisch.
De P.P.-tijdlijn in het scherm is inklapbaar en gebruikt tekstlabels naast kleur.

## Automatische keuzebevestiging per e-mail

Het definitieve keuzedialoog heeft een optioneel e-mailadres. Zonder adres
blijft de selectie hetzelfde werken. Met adres worden selectie, wachtrijrecord
en audit atomisch opgeslagen. Er wordt per consumer maximaal één bevestiging
aangevraagd; opnieuw laden of opnieuw selecteren maakt geen nieuwe mail.
Dit geldt alleen voor nieuwe keuzes, niet met terugwerkende kracht.

Kies voor persoonlijke Hotmail-/Outlook.com-adressen de OAuth-instructies
hieronder. Een gewoon Microsoft-wachtwoord of app-wachtwoord is voor deze
koppeling niet de ondersteunde route.

Voor een andere provider die wachtwoordauthenticatie ondersteunt, configureer
SMTP in de omgeving van het serverproces, bijvoorbeeld in PowerShell:

```powershell
$env:PP_SMTP_AUTH = "password"
$env:PP_SMTP_HOST = "smtp.jouw-provider.nl"
$env:PP_SMTP_PORT = "587"
$env:PP_SMTP_TLS = "starttls"
$env:PP_SMTP_FROM = "bevestiging@jouw-domein.nl"
$env:PP_SMTP_USER = "jouw-smtp-gebruikersnaam"
$smtpSecret = Read-Host "SMTP-wachtwoord of app-wachtwoord" -AsSecureString
$smtpCredential = New-Object System.Management.Automation.PSCredential("smtp", $smtpSecret)
$env:PP_SMTP_PASSWORD = $smtpCredential.GetNetworkCredential().Password
try { python .\server.py } finally { Remove-Item Env:PP_SMTP_PASSWORD }
```

Gebruik de echte instellingen van je mailprovider en een toegestaan afzenderadres.
De waarden hierboven zijn voorbeelden. Deel het SMTP-wachtwoord niet in de chat
en zet het niet in broncode. Stop de bestaande server voordat je hem vanuit deze
terminal opnieuw start: omgevingswijzigingen bereiken een al draaiend proces niet.
Voor impliciete TLS: `PP_SMTP_TLS=ssl` en meestal poort `465`. Alleen TLS met
certificaatcontrole wordt ondersteund; geen onbeveiligde SMTP. Gebruikersnaam
en wachtwoord mogen beide leeg blijven voor een expliciet vertrouwde TLS-relay.
Een gedeeltelijke of ongeldige configuratie stopt de server met een foutmelding.
Zonder SMTP-configuratie blijft de app bruikbaar, maar is het e-mailveld
uitgeschakeld; de API weigert een e-mailaanvraag met `PP_EMAIL_UNAVAILABLE`
zonder de PP-keuze vast te leggen. Ongeldige adressen geven `PP_EMAIL_INVALID`.
De huidige adresvalidatie ondersteunt uitsluitend ASCII-mailadressen, geen
internationale mailboxnamen; domeinen kunnen in punycode worden ingevuld.

Een achtergrondworker leest de blijvende SQLite-wachtrij om de twee seconden.
De netwerkoproep gebeurt buiten de selectietransactie. Expliciete SMTP-fouten
worden maximaal drie keer geprobeerd, met vijf minuten tussen pogingen;
daarna volgt `FAILED`. Bij verbindingsverlies is ontvangst onzeker: `UNKNOWN`
blokkeert automatische herverzending. Na een onderbroken serverrun worden
`SENDING`-records eveneens `UNKNOWN`. Een vaste Message-ID helpt herkenning,
maar garandeert geen exactly-once-bezorging. Er is nog geen handmatige retry
of correctie van een verkeerd ingevuld adres. Draai slechts één server/worker
per database; meerdere afzonderlijke serverprocessen zijn niet ondersteund.

Eigen status is zichtbaar na herladen of via **E-mailstatus vernieuwen**:
`NOT_REQUESTED`, `QUEUED`, `SENDING`, `SENT`, `FAILED`, `UNKNOWN`.
`SENT` betekent uitsluitend dat de SMTP-server het bericht heeft aangenomen,
niet dat het in de inbox is bezorgd. Een latere intrekking annuleert geen reeds
aangevraagde bevestiging: de tekst beschrijft de oorspronkelijke keuze en
claimt niet dat het nummer nog actief is. Mailstoringen draaien een vastgelegde
PP-keuze nooit terug. Bij opslagfouten stopt de worker met een expliciete
serverlog; de wachtrij blijft bewaard.

De e-mail bevat alleen nummer, keuzetijdstip en prototypegrenzen. Geen
privé-notities, wachtwoorden of sessies. Het adres staat onversleuteld in de
lokale wachtrij en gaat naar de ingestelde mailprovider; er is nog geen
automatische bewaartermijn/opschoning. Het adres wordt niet in de audit of
backoffice getoond en wordt niet gebruikt voor marketing, accountverificatie
of wachtwoordherstel. Bescherm de database en gebruik alleen testgegevens.

Tests controleren onder meer atomaire opslag, herstart, gelijktijdige workers,
adresvalidatie, optioneel gebruik, TLS-/SMTP-aanroepen met mocks, retrylimieten,
onzekere ontvangst en accountisolatie. Browserformulierlogica is gecontroleerd
met een tijdelijke database en gesimuleerde mailverzending: kiezen met adres,
status vernieuwen en hetzelfde nummer plus mailstatus na reload. De browserharness
vereiste DOM-change/submit in plaats van fysieke clicks. Er is nog geen echte
SMTP-server of ontvangst in een externe inbox gevalideerd.

### Hotmail / Outlook.com aansluiten met Microsoft OAuth2

**Snelle lokale starter.** Wanneer je eigen Microsoft-appregistratie klaarstaat,
kun je de omgevingsinstellingen en opdrachten hieronder ook laten uitvoeren door
`start_microsoft.py`. Deze starter vraagt geen wachtwoord, wijzigt de omgeving
van je terminal niet en gebruikt dezelfde Python-interpreter voor de mailkoppeling
en server. Gebruik je eigen openbare client-ID en afzenderadres:

```powershell
python .\start_microsoft.py --client-id "JE-APPLICATION-CLIENT-ID" --sender "jij@hotmail.com" --login-only
```

`--login-only` werkt terwijl de gewone demo draait. De tijdelijke Microsoft-code
verschijnt uitsluitend in je terminal; beoordeel en voltooi de aanmelding zelf.
Er wordt geen e-mail verstuurd en de draaiende server krijgt niet automatisch
nieuwe mailinstellingen. Stop daarna de bestaande server en start dezelfde
opdracht **zonder** `--login-only` om PP met Microsoft-mail te draaien:

```powershell
python .\start_microsoft.py --client-id "JE-APPLICATION-CLIENT-ID" --sender "jij@hotmail.com"
```

De starter stopt nooit andere processen en weigert vooraf een bezette poort.
Hij hergebruikt een bestaande versleutelde cache; bij verlopen toestemming
gebruik je `--reauthenticate`. Met `--port` kun je bewust een andere poort kiezen;
gebruik niet meerdere serverprocessen tegelijk op dezelfde database.
Ontbrekende mailpackages, mislukte aanmelding of serverstart geven een foutstatus
en geen succesmelding. Start de opdracht in een eigen interactieve terminal,
niet via een gedeelde chatlog. Er is geen wijziging van PowerShell-executionpolicy
nodig. De uitgebreide handmatige configuratie blijft hieronder beschikbaar.

Deze route is voor persoonlijke Microsoft-accounts, niet voor Microsoft 365
werk-/schoolaccounts. De vaste autoriteit is `consumers`, de SMTP-server is
`smtp-mail.outlook.com:587` met STARTTLS en certificaatcontrole. De app vraagt
gedelegeerde toestemming `https://outlook.office.com/SMTP.Send`; MSAL voegt
de scopes voor aanmelden en tokenvernieuwing toe. Er is geen client secret nodig.
PP vraagt geen toegang tot inbox of privé-notities.

**1. Maak je eigen appregistratie.** Open
[Microsoft Entra](https://entra.microsoft.com), ga naar **App registrations >
New registration** en geef de app bijvoorbeeld de naam **PALACO PP lokaal**.
Kies **Personal Microsoft accounts only**, of de variant die zowel organisaties
als persoonlijke Microsoft-accounts toestaat. Een organisatie-only registratie
werkt hier niet. Een Hotmail-mailbox op zichzelf garandeert geen rechten om
apps te registreren: als de portal geen directory/toegang geeft, is een eigen
geschikte Entra-directory en bevoegdheid nodig. Omzeil dit niet met een geleende
client-ID of een Microsoft-wachtwoord.

Kopieer op **Overview** de **Application (client) ID**. Dit is een openbare UUID,
geen wachtwoord. Zet bij **Authentication > Advanced settings > Allow public
client flows** de optie op **Yes** en sla op. Device-codeaanmelding heeft geen
redirect-URI nodig. Als je vooraf API-permissions configureert, kies de
gedelegeerde Exchange Online-permission **SMTP.Send**, niet Microsoft Graph
`Mail.Send`; de aanmeldflow vraagt de SMTP-scope in ieder geval expliciet.
Maak geen client secret aan.

**2. Installeer en configureer lokaal.** Open een eigen PowerShell-terminal
in de projectmap en voer uit:

```powershell
python -m pip install -r .\requirements-mail.txt
$env:PP_SMTP_AUTH = "microsoft"
$env:PP_SMTP_FROM = Read-Host "Je volledige Hotmail/Outlook-afzenderadres"
$env:PP_MICROSOFT_CLIENT_ID = Read-Host "Application (client) ID van je eigen app"
$env:PP_SMTP_HOST = "smtp-mail.outlook.com"
$env:PP_SMTP_PORT = "587"
$env:PP_SMTP_TLS = "starttls"
Remove-Item Env:PP_SMTP_PASSWORD -ErrorAction SilentlyContinue
Remove-Item Env:PP_SMTP_USER -ErrorAction SilentlyContinue
python .\server.py --microsoft-login
```

Open uitsluitend zelf **https://microsoft.com/devicelogin**, vul de tijdelijke
code uit je eigen terminal in, meld aan met exact het ingestelde afzenderadres
en beoordeel de toestemming voor je eigen app. Deel code, wachtwoord of token
niet in de chat. Verkeerd account, geweigerde toestemming, ontbrekende client-ID
of onversleutelbare opslag geeft een expliciete fout. Een Microsoft-alias die
afwijkt van de gerapporteerde aanmeldnaam wordt hier eveneens geweigerd; gebruik
het primaire, aangemelde mailboxadres. Er wordt tijdens deze opdracht geen
e-mail verzonden en geen PP-account of selectie aangemaakt.

**3. Start de server vanuit dezelfde terminal.** Stop eerst de bestaande demo
op poort 8765 en voer vervolgens uit:

```powershell
python .\server.py
```

De server controleert bij het starten of voor dit afzenderadres een geldig token
kan worden verkregen. De SMTP-verbinding zelf wordt pas bij mailverzending gemaakt.
Zonder voltooide aanmelding stopt een Microsoft-geconfigureerde server expliciet;
hij doet niet alsof mail beschikbaar is. Bij een volgende terminalsessie moet je
de niet-geheime omgevingsvariabelen opnieuw instellen. Herhaal de aanmelding
alleen wanneer de opgeslagen toestemming niet meer bruikbaar is.

**Opslag en grenzen.** MSAL en MSAL Extensions bewaren tokens in
`data\microsoft-<client-id>.bin` met Windows DPAPI, gekoppeld aan de lokale
Windows-gebruiker. Geen plaintext-fallback. Die map is uitgesloten van Git.
De cache kan meerdere accounts bevatten, maar alleen exact het geconfigureerde
afzenderaccount wordt gebruikt. Bescherm ook deze map: processen onder dezelfde
Windows-gebruiker vallen niet buiten de DPAPI-vertrouwensgrens. De code vernieuwt
tokens stil waar mogelijk; verlopen/ingetrokken toestemming vraagt een nieuwe
interactieve login. Bij tokenverlies wordt een mail `FAILED`, zonder verzending
of terugdraaien van de PP-keuze. Er is nog geen herverzendknop voor die mail.
Een eventuele Microsoft-fout tijdens SMTP-authenticatie volgt de bestaande
begrensde SMTP-retrylogica.

Test eerst een nieuwe synthetische PP-keuze met een eigen toegestaan
ontvangstadres. Een SMTP-acceptatie is geen bewijs van inboxbezorging; controleer
ook de inbox/spammap. SPF/DKIM/DMARC en Microsoft-verzendlimieten blijven bij
de mailprovider. Een eigen appregistratie, echte toestemming en echte
Hotmail-bezorging zijn nog niet uitgevoerd of geverifieerd in deze demo.

Officiële bronnen:
- [Outlook.com serverinstellingen en OAuth2](https://support.microsoft.com/en-us/outlook/pop-imap-and-smtp-settings-for-outlook-com)
- [SMTP OAuth-scope en XOAUTH2](https://learn.microsoft.com/en-us/exchange/client-developer/legacy-protocols/how-to-authenticate-an-imap-pop-smtp-application-by-using-oauth)
- [Eigen app registreren](https://learn.microsoft.com/en-us/entra/identity-platform/quickstart-register-app)
- [Public-client flow inschakelen](https://learn.microsoft.com/en-us/entra/identity-platform/scenario-desktop-app-configuration)

## Privé-geheugenbank

Elke aangemelde account heeft een eigen notitiebank: maximaal 100 notities,
elk met een titel van maximaal 120 tekens, inhoud van maximaal 5000 tekens en
maximaal 8 tags van 24 tekens. Notities kunnen worden aangemaakt, aangepast en
verwijderd. De API koppelt iedere bewerking server-side aan de aangemelde
consumer; een account kan geen notities van een andere consumer lezen of wijzigen.
De database begrenst het maximum ook op insertniveau. Audit-events bevatten
alleen het notitie-ID en gebeurtenistype, nooit titel, inhoud of tags.

Routes (alleen voor aangemelde accounts):

| Methode | Pad | Functie |
|---|---|---|
| GET | `/api/memory` | Eigen notities ophalen |
| POST | `/api/memory/save` | Notitie maken of bijwerken; body `{"id":"optioneel","title":"...","content":"...","tags":["..."]}` |
| POST | `/api/memory/delete` | Eigen notitie verwijderen; body `{"id":"..."}` |

**Privacygrens:** notities staan lokaal onversleuteld in SQLite. Ze worden niet
door AI verwerkt, veranderen geen P.P.-status of rechten en zijn geen veilige
opslag voor wachtwoorden, herstelcodes of andere geheimen. Bescherm de database
en maak alleen een back-up als je de onversleutelde inhoud bewust wilt bewaren.

## Beheerderskant / backoffice

Open **http://127.0.0.1:8765/admin**. Beheerders zijn afzonderlijke identiteiten;
een consumentenaccount krijgt nooit automatisch beheerrechten. Maak de eerste
beheerder vanuit een lokale, interactieve PowerShell-terminal:

```powershell
python .\server.py --create-admin
```

Voer een beheerdersnaam en tweemaal een uniek wachtwoord van 12-128 tekens in.
Wachtwoordinvoer is verborgen; als dat niet mogelijk is, wordt afgebroken.
Er is geen standaardwachtwoord, openbare beheerdersregistratie of wachtwoord
via commandoregelargumenten. Bestaande beheerders worden niet overschreven.
Dezelfde opdracht kan extra beheerders aanmaken; lokale database-/terminaltoegang
moet daarom vertrouwd zijn. Gebruik `--db` om expliciet een andere database te kiezen.

De backoffice toont aantallen, accounts inclusief anonieme consumenten,
consumer-ID, gekozen nummer en PP-status. Overzicht en audit zijn gepagineerd
met 50 regels per pagina. Je kunt registraties zoeken op een deel van de
gebruikersnaam, consumer-ID of het gekozen PP-nummer, gecombineerd met een
PP-statusfilter. Zoeken is hoofdletterongevoelig voor gebruikersnamen en IDs;
voer het nummer zonder spaties in. `%` en `_` zijn gewone zoektekens, geen wildcards.
De zoekterm is maximaal 120 tekens. Zoeken of filters wissen begint op pagina 1;
de volgende pagina behoudt de toegepaste filters. Een lege resultatenlijst wordt
expliciet gemeld. De vier statistieken blijven globale totalen; de teller bij de
tabel vermeldt het gefilterde totaal. Filters worden niet bewaard bij herladen
of afmelden.

Er is geen toegang tot privé-notities, geheugenevents,
wachtwoordhashes of sessietokens. De audit geeft uitsluitend de hieronder
beschreven velden terug, nooit de onbewerkte audit-JSON.

Alle beheerders mogen actieve nummers intrekken. Dit vereist een expliciete
bevestiging en een reden van 5-240 tekens. Intrekking en het audit-event met
beheerder-ID en reden worden atomisch opgeslagen; bij een fout wordt alles
teruggedraaid. De gewone PP-levenscyclus blijft gelden: geen herselectie of
heruitgifte na intrekking. Geen accounts verwijderen, nummers toewijzen of
privé-notities wijzigen via het beheer.

Beheerders gebruiken dezelfde PBKDF2-wachtwoordhashing en loginrem als accounts,
maar aparte databasetabellen en een apart `HttpOnly; SameSite=Strict` cookie met
pad `/api/admin`. Sessies verlopen na acht uur, roteren bij login en worden
ingetrokken bij logout. De loginrem voor beheer is gescheiden van consumenten.
Beheerderslogin verandert de consumentensessie niet.

| Methode | Pad | Functie |
|---|---|---|
| POST | `/api/admin/login` | Beheerder aanmelden met `username` en `password` |
| GET | `/api/admin/me` | Huidige beheerder; vereist beheerderssessie |
| POST | `/api/admin/logout` | Beheerderssessie intrekken |
| GET | `/api/admin/overview?offset=0&q=&status=` | Overzicht; optionele zoekterm en statusfilter |
| GET | `/api/admin/audit?offset=0&q=&event=&status=` | Audit met beheerder, intrekkingsreden en optionele filters |
| POST | `/api/admin/revoke` | Intrekken met `consumerId`, `reason` en `confirm: true` |

Ook deze beheerinterface is uitsluitend voor de loopback-demo. Geen MFA,
wachtwoordherstel, beheerdersrollen, internettoegang of productieclaim.

Het overzicht geeft `entries`, `total` (gefilterd), `counts` (globaal), `offset`
en `limit` terug. Geldige statusfilters: leeg, `NEW`, `OFFERED`, `ACTIVE`,
`REVOKED` en `UNKNOWN`. Querywaarden moeten URL-gecodeerd zijn; ongeldige
statussen, dubbele/onbekende parameters en ongeldige offsets geven HTTP 400.
Filtering en telling gebeuren samen in dezelfde SQLite-leestransactie.

### Auditdetails en filters

De audit toont sequentie, tijdstip, gebeurtenis, account/consumer-ID en, waar
expliciet geregistreerd, beheerder-ID en beheerdersnaam. Alleen het event
`ADMIN_NUMBER_REVOKED` toont de vastgelegde intrekkingsreden. Andere detailvelden
(zoals wachtwoorden, sessies, notitiegegevens of willekeurige extra JSON-velden)
worden niet uitgegeven en zijn niet doorzoekbaar. Account- en beheerdersnamen
komen uit de huidige registratie; een onbekende beheerder blijft herkenbaar
aan het oorspronkelijke ID, zonder een naam te verzinnen.

Vrij zoeken (maximaal 120 tekens) doorzoekt gebeurtenis, sequentie, consumer-ID,
accountnaam, beheerder-ID, beheerdersnaam en intrekkingsreden. `%` en `_` worden
letterlijk gezocht, niet als wildcards. ASCII-letters zijn hoofdletterongevoelig;
SQLite normaliseert niet alle internationale hoofd-/kleine letters.
De gebeurtenisfilter accepteert de aangeboden engine-, account- en beheerevents,
maar nooit privé-geheugenevents.

De auditstatus is de **PP-status bij de gebeurtenis**, niet de huidige status:
`OPTION_OFFERED` en `OPTIONS_OFFERED` horen bij `OFFERED`, `NUMBER_SELECTED` bij
`ACTIVE`, `NUMBER_REVOKED` en `ADMIN_NUMBER_REVOKED` bij `REVOKED`. Overige events
hebben een lege status. Het filter accepteert leeg, `OFFERED`, `ACTIVE`, `REVOKED`.
Een beheerintrekking schrijft twee gekoppelde gebeurtenissen: de gewone
levenscyclusovergang en de beheerhandeling met actor en reden.

Zoekterm, gebeurtenis en status werken samen (AND). De 50-regelpaginering behoudt
alle toegepaste filters en telt alleen passende events, in aflopende sequentie.
Auditfilters staan los van accountfilters; toepassen of wissen begint op auditpagina
1. Een lege match wordt expliciet getoond. Na herladen of afmelden zijn filters
gewist. Ongeldige queryparameters geven HTTP 400; ongeldige beheeraudit-JSON,
actor of reden blokkeert de audit met HTTP 503 `PP_AUDIT_UNKNOWN`, ook wanneer
de foutieve regel niet bij de zoekterm past. De UI toont dan geen oude auditregels.
De opgeslagen append-only records worden niet gewijzigd door zoeken of bekijken.

Browsercontrole van de backoffice is uitgevoerd met een tijdelijke, synthetische
database op een aparte poort: login, sessiebehoud bij reload, annuleren van
intrekking, definitief intrekken, audit-event, behoud van intrekking na reload,
logout en afgeschermde dashboardtoegang na reload. De mobiele viewport van
390 pixels had geen pagina-brede horizontale overflow. Bestaande accounts,
consumentensessies en privé-notities in de gewone demo zijn hiervoor niet gebruikt.
Zoekacceptatie is aanvullend gecontroleerd op 52 synthetische consumenten:
pagina 2, zoeken terug naar pagina 1, hoofdletterongevoelige gebruikersnaam,
nummer plus status, geen resultaten en filters wissen. De formulierhandelingen
zijn via DOM-submit uitgevoerd wegens instabiele Playwright-clicks in de browserharness;
dit bewijst de aangesloten formulierlogica, niet alle fysieke muisinteracties.
Auditacceptatie is aanvullend uitgevoerd op een tijdelijke database met 72
zichtbare gebeurtenissen: gefilterde paginering, zoeken op beheerder, gebeurtenis
plus status, actor/reden, een lege match en filters wissen. HTML-achtige tekst in
een reden bleef gewone tekst en werd niet als HTML uitgevoerd. De mobiele
viewport van 390 pixels had geen pagina-brede horizontale overflow. Ook deze
formulierhandelingen gebruikten DOM-submit en niet uitsluitend fysieke muisklikken.
Een bewust ongeldig beheer-event in uitsluitend die tijdelijke database gaf
HTTP 503, een expliciete foutmelding en nul oude auditregels in de browser.

## Niet inbegrepen

Geen bellen, SMS, WhatsApp, officieel PALACO-register,
heruitgifte, productiehosting of aanspraak op geverifieerde PALACO-canon.
De visuele richting is een prototypevoorstel, niet een bevestigde huisstijl.
Deze implementatie is gebaseerd op het aangeleverde ontwerp; de genoemde
Notion-bronnen zijn hiervoor niet onafhankelijk gevalideerd.
