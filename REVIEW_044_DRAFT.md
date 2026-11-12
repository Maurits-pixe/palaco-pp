# P.P. Review 044 — offline vier-bestandenketen (DRAFT)

**Object:** `PP-RECOVERY-002` · **Scope:** uitsluitend synthetische lokale bestanden.

**Uitvoering:** NOT EXECUTED. Dit dossier bereidt controles voor; het voert ze
niet uit en bevat geen waarneming van een echte reviewer. De eigenaar voert
de tests op een later moment zelf uit. Geen merge, accountkoppeling of uitgifte.

## Contract

De controlefunctie `review_chain.link_hold_chain` ontvangt de oorspronkelijke
bytes van de handoff, het HOLD-rapport, de bewijsindex en de client-observatie.
Alle vier blijven onvertrouwd. Bij geldige bestandsconsistentie is de
uitkomst `FOUR_FILE_HASH_MATCH_UNTRUSTED` met HOLD/DENY. Iedere ongeldige
invoer moet `PP_CHAIN_INVALID` opleveren, zonder persoonsgegevens in de fout.

## Voorbereide scenario's

De pure fixturefunctie `review_fixtures.build_review_fixtures()` levert
in-memory byte-tuples zonder bestanden te schrijven of validators aan te roepen.
UUID's en P.P.-suffixen zijn expliciet synthetisch.

## Bewust starten tijdens de testsessie

De voorbereide, offline runner `review_044_runner.py` start **niet** bij
importeren en voert pas controles uit met een expliciete `--run`-optie.
Vanaf de projectmap kan de eigenaar later kiezen:

```sh
python review_044_runner.py --run
```

Voor een kopieerbaar technisch rapport naar de terminal:

```sh
python review_044_runner.py --run --json
```

Zonder `--run` worden geen scenario's gestart. De runner schrijft geen
bestanden en legt geen externe verbindingen. Een technisch overeenkomende
uitkomst is uitsluitend `SYNTHETIC_AUTOMATED_LOCAL_EXECUTION`, **niet**
`SELF_REPORTED` en geen onafhankelijke identiteitstoets. De gebruiker kan
de eigen schermwaarneming later apart als `SELF_REPORTED` registreren.

## Eigen waarnemingen als afzonderlijk contract

`review_044_observations.make_self_report(observations, recorded_at)` maakt
uitsluitend op expliciete invoer van de eigenaar een in-memory
`palaco.pp.review-044-self-report.v0`-object. Een invoerregel bevat exact
`scenario_id`, `observed_result` en `observed_at`; het rapport bevat geen
vrij tekstveld, nummers of consumer-ID's. Niet ingevulde scenario's blijven
`NOT_OBSERVED` met `NO_OBSERVATION`. Een zelfgerapporteerde overeenkomst heet
`MATCH_CLAIMED` en nooit `PASS` of `VERIFIED`.

De functie vergelijkt alleen de ingevoerde waarden met de vooraf vastgelegde
verwachting. Zij voert geen fixture, validator of test uit, schrijft geen
bestanden, en kent geen autorisatie-uitkomst anders dan `HOLD`/`DENY`.

## Voorbereid formulier in de lokale beheerpagina

Onder **Review 044 / mijn eigen waarneming** kunnen later per scenario
uitkomsten worden vastgelegd via een expliciete knop. De selectie heeft
geen test- of validatorfunctie. Het JSON-bestand wordt uitsluitend na een
aparte downloadactie lokaal aangeboden. Het formulier bewaart de invoer
alleen in paginageheugen: herladen of afmelden wist de observaties.
De export gebruikt hetzelfde `palaco.pp.review-044-self-report.v0`-contract
als de pure Python-functie; ontbrekende scenario's blijven `NOT_OBSERVED`,
de opgegeven resultaten zijn `SELF_REPORTED`, en de uitkomst blijft
`NOT_VERIFIED` / `HOLD` / `DENY`. Er is geen serverupload of externe opslag.

## PALACO ONE overdrachtsvoorbereiding (alleen-lezen)

`review_044_identity_preview.preview_identity_handoff(raw_report)` accepteert
uitsluitend een begrensd JSON-zelfrapport met de negen vaste scenario's,
verwachtingen, bewijslabels en HOLD/DENY-velden. Dubbele JSON-sleutels,
onbekende velden, afwijkende vergelijkingslabels en autorisatieverhoging
worden geweigerd met `PP_REVIEW_044_PREVIEW_INVALID`. De functie produceert
alleen een geminimaliseerde preview: geen persoonsgegevens, geen P.P.-nummer,
geen login, geen accountbinding en geen bewijs van identiteit. Een lokale
zelfrapportage kan deze grens niet zelfstandig opheffen.
Tijdstempels moeten exacte UTC ISO-8601-milliseconden met `Z` zijn en geen
waarneming mag na het rapporttijdstip liggen. Ook syntactisch geldige maar
semantisch afwijkende datums worden geweigerd. Een timestamp is uitsluitend
een door de client opgegeven tijd, geen onafhankelijke tijdsattestatie.

Deze adapter is **DRAFT / NOT EXECUTED**. Er is nog geen echte PALACO ONE
runtimekoppeling en geen toestemming voor activatie.

### Voorbereide negatieve regressies (nog niet uitgevoerd)

`review_044_preview_fixtures.build_preview_fixtures()` maakt uitsluitend
synthetische byte-invoer en benoemde verwachtingen in geheugen. De functie
roept de adapter **niet** aan. Twee positieve vormscenario's mogen hooguit
een `HOLD_DENY_PREVIEW` opleveren; ongeldige invoer moet steeds
`PP_REVIEW_044_PREVIEW_INVALID` geven. Voorbereid zijn:

- geldig rapport zonder waarneming; geldig zelfrapport met één claim;
- ontbrekende `Z`, andere tijdzone, onmogelijke kalenderdatum,
  ontbrekende milliseconden, waarneming na rapporttijd;
- autorisatie- of verificatie-escalatie, vervalst `PASS`-vergelijkingslabel;
- ontbrekende provenance, dubbele JSON-sleutel en te grote invoer.

Verwachte foutcodes zijn **SPECIFICATION**, geen geobserveerde uitslagen.
De uitvoering blijft voorbehouden aan de latere expliciete testsessie.

### Afzonderlijke opt-in previewrunner

`review_044_preview_runner.py` is voorbereid voor deze **13** synthetische
scenario's. Zonder expliciet `--run` voert hij geen controles uit. Later kan
de eigenaar vanuit de projectmap kiezen voor:

```sh
python review_044_preview_runner.py --run --json
```

De uitvoer gaat uitsluitend naar de terminal, niet naar een bestand of
netwerk. Ook een technisch overeenkomend resultaat blijft
`SYNTHETIC_AUTOMATED_LOCAL_EXECUTION` met `HOLD`/`DENY`, zonder
PALACO ONE-sessie, accountbinding of uitgifte. **Tot uitvoering door de
eigenaar: NOT EXECUTED; geen PASS-claims.**

### Beoordelingsvoorbereiding voor een later rapport

`review_044_preview_assessment.assess_preview_report(raw)` accepteert
uitsluitend het vaste technische rapportcontract met 13 scenario's in
de voorgeschreven volgorde. De parser weigert dubbele sleutels,
onbekende velden, ongeldige codes, inconsistenties tussen geclaimde
resultaten en vergelijkingslabels en pogingen tot autorisatie-escalatie.
Hij geeft alleen een minimale **claimed**-samenvatting terug; het importeren
van een JSON-rapport bewijst niet dat een lokale runner werkelijk is uitgevoerd.
De eigenaarreview blijft `PENDING` en identiteit/uitgifte blijven geblokkeerd.
Deze functie is eveneens **DRAFT / NOT EXECUTED**.

### Werkblad voor de latere eigenaarreview

`review_044_owner_review.make_owner_review_draft(technical_report, owner_marks)`
maakt een niet-ondertekend werkblad bij de oorspronkelijke rapportbytes.
De SHA-256-waarde bindt het werkblad aan die bytes maar bewijst **niet**
wie ze heeft gemaakt of of de runner daadwerkelijk heeft gedraaid.
Per scenario accepteert het werkblad alleen `NOT_REVIEWED`,
`OBSERVED_AS_REPORTED` of `DISCREPANCY_REPORTED`. Niet ingevulde scenario's
blijven `NOT_REVIEWED` en `NO_OBSERVATION`; expliciete eigenaarinvoer is
uitsluitend `SELF_REPORTED`. Het werkblad verwerkt geen namen,
P.P.-nummers, vrije tekst of inloggegevens. De uitvoer blijft altijd
`NOT_VERIFIED`/`HOLD`/`DENY` en start geen test of PALACO ONE-sessie.

De bestaande lokale backoffice biedt hiervoor een aanvullend
**Review 044 / eigenaarwerkblad technische preview**-paneel. Het leest
een door de eigenaar gekozen technisch JSON-bestand (maximaal 32 KB),
toont alleen een voorlopige structuurindicatie, verzamelt de drie
toegelaten markeringen per scenario en biedt het werkblad als lokale
JSON-download aan. De browser-JSON-parser detecteert dubbele sleutels
niet; de striktere Python-parser is daarom normatief. Geen serverupload,
runner-uitvoering, automatische goedkeuring of duurzame browseropslag.
Status van deze interface: **DRAFT / NIET GETEST / HOLD / DENY**.

### Bewijsindex voor technisch rapport en eigenaarwerkblad

`review_044_owner_index.make_owner_evidence_index(technical_report, worksheet)`
maakt uitsluitend na strikte inhoudelijke controle een lokale bewijsindex.
Beide argumenten zijn de **originele bytes** van respectievelijk het
synthetische technische rapport en het eigenaarwerkblad. De parser weigert
onder andere dubbele JSON-sleutels, onbekende velden, gewijzigde hashes,
verkeerde scenario-volgorde, verzonnen eigenaarprovenance en aangepaste
HOLD/DENY-velden. Hij reconstrueert het eigenaarwerkblad volgens het
bestaande contract, inclusief het onderscheid tussen ontbrekende en
expliciet onbeoordeelde markeringen.

De index vermeldt beide SHA-256-hashes en hoogstens
`TWO_FILE_HASH_MATCH_UNTRUSTED`: de binding is een consistentieclaim,
**geen herkomstbewijs**. Geen lokaal testprogramma wordt aangeroepen, geen
server benaderd, geen identiteit vastgesteld en geen autorisatie verleend.
Status: **DRAFT / NOT EXECUTED / HOLD / DENY**.

De backoffice bevat nu eveneens een afzonderlijk paneel om die twee
bestanden lokaal te kiezen en een bewijsindex als JSON te downloaden.
Deze browservergelijking kan dubbele JSON-sleutels niet afwijzen en is dus
**geen vervanging** van `make_owner_evidence_index` in Python. Een
browseruitkomst `TWO_FILE_HASH_MATCH_UNTRUSTED` is uitsluitend indicatief;
het bestand wordt niet verzonden of automatisch geregistreerd.

### Lokaal drie-bestandendossier

De pure functie `review_044_owner_dossier.assess_owner_dossier(
technical_report, owner_worksheet, evidence_index)` accepteert uitsluitend
de **drie originele bytebestanden**. De technische rapportcontrole en de
eigenaarsmarkeringen worden opnieuw vanuit de bronnen beoordeeld; vervolgens
wordt de verwachte bewijsindex opnieuw berekend en strikt vergeleken met
het ingevoerde derde bestand. Dubbele JSON-sleutels, onbekende velden,
afwijkende hashes en autorisatie-escalatie worden geweigerd.

Een consistente dossierketen levert alleen
`THREE_FILE_HASH_MATCH_UNTRUSTED` op. Dit bewijst geen bron, uitvoerende
persoon, echte runtime-uitvoering of identiteit. Het dossier heeft geen
databaseverbinding, testuitvoering, bestandsschrijfacties of bevoegdheid.
**Status: DRAFT / NOT EXECUTED / HOLD / DENY.**

Voor latere eigenaarbediening is daarnaast het backofficepaneel
**Review 044 / lokaal drie-bestandendossier** toegevoegd. De drie bestanden
worden niet verzonden of opgeslagen door PALACO; de browser biedt uitsluitend
een indicatieve vergelijking en een downloadbare beoordeling. Bij een nieuwe
bestandskeuze vervalt de vorige indicatie. Duplicaten van JSON-sleutels
vallen buiten de browsergarantie; de Python-beoordelaar blijft normatief.

### Lokaal Review 044-bewijsregister (concept)

`review_044_owner_registry.append_owner_dossier(existing_registry,
technical_report, owner_worksheet, evidence_index)` geeft een **nieuw
JSON-registersnapshot als bytes** terug. De functie schrijft niets weg,
roept geen runner aan en verandert geen account. `existing_registry` is
uitsluitend `None` voor een nieuw register of de originele bytes van het
vorige snapshot. Elk toegevoegd dossier moet eerst de strikte drie-
bestandencontrole doorstaan. Herhaalde identieke dossierverwijzingen worden
geweigerd; iedere nieuwe rij heeft een oplopend volgnummer, drie hashes,
een eigen entry-hash en de hash van de voorgaande rij.

Het register verzint geen tijdstempels en bewaart geen bronbestanden.
Een hashketen controleert interne consistentie maar biedt **zonder externe
ondertekening of onveranderlijke opslag geen bescherming tegen het volledig
herschrijven van de geschiedenis**. Ook een geldig snapshot bewijst niet
dat eerdere bronbestanden destijds echt of onafhankelijk geverifieerd waren.
Maximaal 256 verwijzingen en 256 KB per snapshot. Alle rijen blijven
`NOT_VERIFIED / HOLD / DENY / NOT_AUTHORIZED`.

Het lokale backofficepaneel **Review 044 / lokaal bewijsregister** maakt
hiervan een downloadbare, browsermatig voorbereide versie. Na een indicatieve
beoordeling van drie dossierbestanden kan een bestaand register worden
geselecteerd; leeg betekent een nieuw register. Het paneel controleert de
volgorde, vaste HOLD/DENY-velden, interne hashketen en dubbele
dossierverwijzingen alvorens één rij toe te voegen. Het schrijft niets op de
server en vervangt het vorige bestand niet. De browser kan dubbele sleutels
in JSON niet betrouwbaar afwijzen en verifieert geen externe historie:
`review_044_owner_registry.py` blijft het normatieve validatiecontract.
Het voorbereide snapshot wordt in een scrollbare tabel samengevat met
volgnummer, verkorte entry-hash, voorgangerhash en de vaste HOLD/DENY-status.
Bij bestandswissel wordt het oude overzicht gewist. De term
`INTERN CONSISTENT` is geen externe authenticiteitsverklaring.
Een geselecteerde rij krijgt daarnaast een uitsluitend lokaal inspectiepaneel:
alle drie bronhashes, de eigen entry-hash, de voorgangerhash en het nummer
zijn volledig leesbaar. De laatst toegevoegde rij wordt aanvankelijk
geselecteerd; een ander volgnummer is aanklikbaar. De onafhankelijke
verificatiestatus blijft uitdrukkelijk `NOT_VERIFIED`.
Het paneel biedt een downloadbaar `palaco.pp.review-044-registry-row-inspection.v0`
JSON-inspectierapport voor precies de geselecteerde regel. Het bevat geen
automatisch ingevuld tijdstip, handtekening, zelfstandig authenticiteitsbewijs
of productieautoriteit. Bij register- of dossierwijziging wordt een eerdere
selectie en de bijbehorende exportmogelijkheid onmiddellijk ingetrokken.

De pure offline functie
`review_044_owner_inspection.validate_owner_inspection(registry_bytes,
inspection_bytes)` koppelt een gedownload inspectierapport strikt aan het
oorspronkelijke registersnapshot. De bestaande registervalidator beoordeelt
eerst de volledige keten, waarna exact schema, veldset, vaste bewijsgrenzen,
volgnummer en alle bron-/entry-/voorgangerhashes moeten overeenkomen.
Dubbele JSON-sleutels en ambiguë of gemanipuleerde claims worden geweigerd
met `PP_REVIEW_044_OWNER_INSPECTION_INVALID`. De geretourneerde beoordeling
blijft `REGISTER_ROW_HASH_BINDING_CONSISTENT_UNTRUSTED / NOT_VERIFIED /
HOLD / DENY / NOT_AUTHORIZED`. **Status: DRAFT / NOT EXECUTED.**

Status: **DRAFT / NOT EXECUTED / HOLD / DENY**.

| Fixture | Verwacht bij latere uitvoering | Risico dat wordt onderzocht |
| --- | --- | --- |
| `baseline_untrusted_hold` | `FOUR_FILE_HASH_MATCH_UNTRUSTED` | Correcte binding ≠ verificatie |
| `handoff_changed_without_rebinding` | `PP_CHAIN_INVALID` | Gewijzigde oorspronkelijke overdracht |
| `report_authority_escalation` | `PP_CHAIN_INVALID` | Onterechte autorisatieclaim in rapport |
| `index_wrong_report_digest` | `PP_CHAIN_INVALID` | Verbroken tweede hashbinding |
| `observation_wrong_index_digest` | `PP_CHAIN_INVALID` | Verbroken derde hashbinding |
| `observation_authority_escalation` | `PP_CHAIN_INVALID` | Onterechte autorisatieclaim in observatie |
| `observation_duplicate_key` | `PP_CHAIN_INVALID` | Ambigue JSON / dubbele sleutel |
| `observation_truncated_json` | `PP_CHAIN_INVALID` | Ongeldige JSON-invoer |
| `observation_oversized` | `PP_CHAIN_INVALID` | Overschreden invoerlimiet |

## Registratieformat voor eigen waarnemingen

Vul na uitvoering per scenario apart in:

- `scenario_id`: exacte fixturenaam
- `observed_result`: letterlijke foutcode of teruggegeven status
- `expected_result`: waarde uit de tabel
- `evidence_kind`: `SELF_REPORTED`, tenzij onafhankelijk bewijs bestaat
- `executed_at`: werkelijk tijdstip van uitvoering, niet vooraf invullen
- `notes`: geen P.P.-nummer of andere persoonsgegevens
- `decision`: `HOLD` tot de bevoegde review expliciet anders beslist

## AI-review aan de hand van drie lenzen

- **TRIAS:** geen testfixture kan een productie- of identiteitsgate openen.
- **ORACLE:** verwachte waarden zijn specificatie, niet geobserveerde PASS.
- **MENTOR:** negen compacte scenario's geven de eigenaar een duidelijke
  volgorde voor de latere testsessie; afwijkingen worden afzonderlijk hersteld.

**Status:** PREPARED / NOT EXECUTED / HOLD / DENY.

### Inspectierapporten lokaal importeren — alleen voorbereiding

De backoffice heeft een apart importpaneel voor het oorspronkelijke
Review 044-registersnapshot (maximaal 256 KiB) en een gedownload
regelinspectierapport (maximaal 16 KiB). De knop **Vergelijk geselecteerde
regel lokaal (indicatief)** leest beide bestanden uitsluitend via de
browser-File API. Er is geen upload en geen databasehandeling.

**Bewijsgrens:** de browser controleert alleen de herkenbare velden van
de geselecteerde regel. Hij controleert *niet* de volledige hashketen en
weigert niet betrouwbaar dubbele JSON-sleutels. Zelfs bij overeenkomst
is dit **geen** strikte Python-verificatie.

Een afzonderlijke opt-in CLI gebruikt de bestaande normatieve validator:
`review_044_inspection_cli.py`. Pas tijdens de eigenaartestsessie:

```powershell
python .\review_044_inspection_cli.py --run --registry "PAD_NAAR_REGISTER.json" --inspection "PAD_NAAR_INSPECTIE.json" --json
```

Zonder `--run` worden geen bestanden gelezen. Een weigering geeft
`PP_REVIEW_044_OWNER_INSPECTION_INVALID` en exitcode 1; een technisch
consistente binding geeft exitcode 0, maar uitsluitend het label
`REGISTER_ROW_HASH_BINDING_CONSISTENT_UNTRUSTED`. Bevoegdheden blijven
`NOT_VERIFIED / HOLD / DENY / NOT_AUTHORIZED`. De CLI leest uitsluitend
expliciet genoemde lokale bestanden, schrijft niets, toont geen
bestandsinhoud of persoonsgegevens, en maakt geen netwerkverbinding.
Deze nieuwe functie is **NOT EXECUTED**; pas jouw testwaarnemingen later
als `SELF_REPORTED` vast.

### Negatieve importregressies — voorbereid, NIET uitgevoerd

`review_044_inspection_fixtures.build_inspection_fixtures()` levert
**24 deterministische, volledig synthetische** scenario's als vier-tuples
`(scenario_id, registry_bytes, inspection_bytes, expected_result)`.
De fixturebouwer schrijft niets weg, gebruikt geen echte eigenaargegevens
en roept de validator niet aan. De scenario's omvatten een uitsluitend
technisch consistente basisbinding en afwijzingen voor:

- onjuist of boolean volgnummer en mismatches in de vijf hashverwijzingen;
- vervalste autorisatie-, verificatie- en historievermeldingen;
- ontbrekende/onbekende velden en dubbele JSON-sleutels;
- afgebroken, lege, ongeldige UTF-8 en te grote inspectiebestanden;
- gemanipuleerde registerhash, volgorde, autorisatie, lege keten,
  dubbele registersleutel en overschrijding van de registerlimiet.

`review_044_inspection_runner.py` is een afzonderlijke opt-in runner.
Hij roept de validator **alleen na expliciet `--run`** aan. Tijdens een
latere, door de eigenaar gestarte testsessie:

```powershell
python .\review_044_inspection_runner.py --run --json
```

De JSON-uitvoer bevat technische waarnemingen onder
`SYNTHETIC_AUTOMATED_LOCAL_EXECUTION`, nooit menselijke
`SELF_REPORTED`-verklaringen of een onafhankelijk PASS-certificaat.
Zonder `--run` blijft de uitvoering op NOT EXECUTED. Deze build heeft
**geen fixtures uitgevoerd** en claimt geen testuitslagen. De code
wijzigt geen PP-account, register, database of productieautorisatie.
Alle bevoegdheidsvelden blijven `HOLD / DENY / NOT_AUTHORIZED`.
