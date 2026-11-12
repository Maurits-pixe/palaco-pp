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

### Technisch rapport en eigenaarswerkblad — strikt gescheiden (DRAFT)

Nieuwe pure modules:

- `review_044_inspection_owner_review.assess_inspection_technical_report(raw)`
  controleert **alle 24** scenario's, vaste volgorde, verwachte codes,
  uitsluitend toegestane technische resultaatcodes, `MATCH/MISMATCH`
  consistentie, exacte veldsets, UTF-8, grootte en dubbele JSON-sleutels.
  Een technisch rapport is altijd `IMPORTED / UNATTESTED`: zelfs 24
  geclaimde MATCH-resultaten betekenen `ALL_MATCH_CLAIMED`, nooit PASS.
- `review_044_inspection_owner_review.make_inspection_owner_worksheet(raw, marks)`
  maakt een uitsluitend lokaal, ongetekend 24-regelig eigenaarwerkblad.
  Alleen expliciet aangeboden markeringen worden `SELF_REPORTED`;
  ontbrekende blijven `NOT_REVIEWED / NO_OBSERVATION`. Er wordt geen
  tijdstip of menselijke waarneming verzonnen.
- `review_044_inspection_owner_binding.validate_inspection_owner_worksheet(
  raw_report, raw_worksheet)` controleert het werkblad opnieuw tegen
  de originele technische rapportbytes, de 24 scenarionamen en exacte
  markeringen/provenance. Verkeerde aantallen, extra velden, gewijzigde
  hashes of HOLD-escalaties geven één vaste weigering:
  `PP_REVIEW_044_INSPECTION_WORKSHEET_INVALID`. Een overeenkomst heet
  uitsluitend `TWO_FILE_HASH_MATCH_UNTRUSTED`.

Het rapport is maximaal 64 KiB; een werkblad maximaal 48 KiB.
Deze modules hebben geen database-, netwerk-, test-runner-, tijd- of
bestandsschrijfacties. Ze worden **niet** aangeroepen door de
backoffice of een automatisch proces. De eigenaar bepaalt later of,
wanneer en hoe de eigen tests en waarnemingen plaatsvinden.

**Huidige status: DRAFT / NOT EXECUTED / NOT_VERIFIED / HOLD / DENY /
NOT_AUTHORIZED.** Ook een consistente tweebestandenbinding geeft geen
PALACO ONE-inlogrecht, identiteit, uitgifte of productiebevoegdheid.

### Backoffice — eigenaarwerkblad voor 24 inspectiescenario's

De bestaande lokale beheerpagina heeft nu het afzonderlijke paneel
**Review 044 / eigenaarwerkblad inspectieregressies (24 scenario's)**.
De eigenaar kiest een reeds bestaand, synthetisch technisch runner-JSON
(maximaal 64 KiB), laadt dit expliciet in de browser en ziet de
24 scenario's met hun geclaimde technische MATCH/MISMATCH-uitkomst.

Iedere regel kan afzonderlijk worden gemarkeerd als:

- niet ingevoerd: `NOT_REVIEWED / NO_OBSERVATION`;
- expliciet niet beoordeeld: `NOT_REVIEWED / SELF_REPORTED`;
- waargenomen zoals gerapporteerd: `OBSERVED_AS_REPORTED / SELF_REPORTED`;
- afwijking gerapporteerd: `DISCREPANCY_REPORTED / SELF_REPORTED`.

Een klik op **Download mijn 24-scenario-eigenaarwerkblad (.json)**
maakt uitsluitend lokaal het contract
`palaco.pp.review-044-inspection-owner-worksheet.v0` aan, met de
SHA-256-vingerafdruk van het originele technische rapport.
De browseruitvoer houdt dezelfde veldnamen, volgorde en vaste
HOLD/DENY-grenzen aan als de pure Python-werkbladbouwer.
Een bestandswissel of afmelding wist de tijdelijke markeringen.

**Geen onafhankelijke controle:** de browserparser kan dubbele
JSON-sleutels niet betrouwbaar afwijzen en bewijst de uitvoering van
een runner niet. De strikte controle blijft bij
`assess_inspection_technical_report()` en
`validate_inspection_owner_worksheet()` in Python. Er wordt geen
serverupload, databasewijziging, PALACO ONE-koppeling of automatische
autorisatie uitgevoerd. De server biedt de beide Review 044-scripts
uitsluitend aan via twee expliciete statische allowlist-paden.

**Status: DRAFT / NOT EXECUTED / NOT_VERIFIED / HOLD / DENY.**

### Backoffice — twee-bestandenbinding van het inspectiewerkblad

Het afzonderlijke paneel **Review 044 / technische rapportbinding met
eigenaarwerkblad** leest twee originele lokale JSON-bestanden: het
synthetische technische inspectierapport (maximaal 64 KiB) en het
eigenaarwerkblad (maximaal 48 KiB). Het vergelijkt de vaste
rapportcontracten, 24 scenario's, gemelde markeringen, interne aantallen
en SHA-256 van beide oorspronkelijke bytestromen.

Een consistente browserindicatie toont de volledige hashes, de
technisch *geclaimde* vergelijking en de eigenaarsmarkeringen.
Een optionele expliciete download schrijft alleen een nieuwe, ongetekende
`palaco.pp.review-044-inspection-owner-browser-binding.v0` met
`CLIENT_TWO_FILE_HASH_MATCH_UNTRUSTED` en vaste
`NOT_VERIFIED / HOLD / DENY / NOT_AUTHORIZED`-velden. Een nieuwe
bestandskeuze of afmelding wist eerdere resultaten en blokkeert export.

**Bewijsgrens:** `JSON.parse` kan dubbele JSON-sleutels niet
betrouwbaar detecteren. De browser voert dus *geen* strikte Python-validatie
uit. Gebruik voor de normatieve controle later de pure functie
`review_044_inspection_owner_binding.validate_inspection_owner_worksheet(
technical_report_bytes, worksheet_bytes)` op beide originele bestanden.
Die functie kan alleen interne consistentie vaststellen, geen
onafhankelijke authenticiteit, tijd, daadwerkelijke testuitvoering,
persoonlijke identiteit of bevoegdheid.

De server serveert het nieuwe script alleen via een expliciete lokale
allowlist-route. Geen algemene bestandsserver, uploadendpoint of
autorisatieroute is toegevoegd. **DRAFT / NOT EXECUTED / HOLD / DENY.**

### Offline vastleggen van de strikte Python-beoordeling (DRAFT)

`review_044_inspection_evidence.compile_inspection_owner_evidence(
technical_report, owner_worksheet)` leest geen bestanden en voert geen
tests uit. Hij roept uitsluitend de twee strikte, bestaande in-memory
contractbeoordelaars aan voor de **originele bytebestanden**. Onjuiste
rapportstructuur, dubbele JSON-sleutels, afwijkende scenariorijen,
vervalste eigenaarsmarkeringen of gebroken SHA-256-binding leiden tot
`PP_REVIEW_044_INSPECTION_EVIDENCE_INVALID`.

De uitvoer bevat onder andere de SHA-256 van beide bronnen, het aantal
technisch *geclaimde* afwijkingen, expliciet door de eigenaar gemarkeerde
scenario's, en de vaste bewijsstatus. De uitkomst
`STRICT_PYTHON_TWO_FILE_HASH_MATCH_UNTRUSTED` duidt **alleen op strikte
interne consistentie**, niet op een bewezen uitgevoerde runner, tijd,
bronidentiteit, eigenaarshandtekening of autorisatie.

De opt-in opdrachtregel `review_044_inspection_evidence_cli.py` gebruikt
dezelfde functie. **Tot de latere eigenaarstestsessie niet uitvoeren.**
Zonder `--run` worden geen bestanden geopend. Tijdens een expliciet
geautoriseerde lokale testsessie kan de eigenaar kiezen voor een
consoleweergave:

```powershell
python .\review_044_inspection_evidence_cli.py --run --technical "PAD_NAAR_TECHNISCH.json" --worksheet "PAD_NAAR_WERKBLAD.json"
```

Of een expliciet nieuw JSON-bestand (niet overschrijven):

```powershell
python .\review_044_inspection_evidence_cli.py --run --technical "PAD_NAAR_TECHNISCH.json" --worksheet "PAD_NAAR_WERKBLAD.json" --export "review-044-evidence-hold.json"
```

De CLI leest maximaal 64 KiB technische rapportbytes en 48 KiB
werkbladbytes, geeft geen broninhoud terug bij een fout en weigert een
bestaand exportpad. Zonder `--export` schrijft hij niets naar schijf.
Er is geen webserver, database of PALACO ONE-runtimekoppeling.
Een technisch consistente uitkomst blijft
`UNSIGNED_LOCAL_PYTHON_VALIDATION_RESULT / NOT_VERIFIED / HOLD / DENY /
NOT_AUTHORIZED`, zonder zelfstandige bevoegdheid of PASS-claim.

**Status: DRAFT / NOT EXECUTED / NOT_VERIFIED / HOLD / DENY.**

### Read-only backofficeweergave van een geëxporteerd Python-bewijsrapport

Het lokale backofficepaneel **Review 044 / Python-bewijsrapport —
alleen-lezen overzicht** kan een reeds door de eigenaar opgeslagen
`palaco.pp.review-044-inspection-owner-evidence.v0`-JSON van maximaal
16 KiB lezen. Er worden geen bestanden geüpload, opgeslagen, gewijzigd
of verzonden en er wordt geen Python gestart.

Het paneel splitst de inhoud in drie uitdrukkelijk verschillende
categorieën:

1. **Technisch geclaimd:** schema, twee volledige SHA-256-hashes,
   aantallen en het label `STRICT_PYTHON_TWO_FILE_HASH_MATCH_UNTRUSTED`
   zoals *in het gekozen bestand vermeld*.
2. **Eigenaarswaarnemingen:** alleen aantallen van gerapporteerde
   markeringen en afwijkingen; de uitvoeringsherkomst blijft
   `NOT_INDEPENDENTLY_ESTABLISHED`.
3. **Onafhankelijke verificatie:** uitsluitend
   `NOT_VERIFIED / HOLD / DENY / NOT_AUTHORIZED`, zonder identiteit,
   ondertekening, onveranderlijke historie of productiebevoegdheid.

De browser weigert onbekende velden, verkeerde vaste statuswaarden,
ongeldige SHA-256-vormen, onmogelijke aantallen of tegenstrijdige
technische vergelijkingslabels. De ingelezen JSON blijft echter
**onvertrouwde gebruikersinput**: een bestand kan nagemaakt zijn en
`JSON.parse` detecteert geen dubbele sleutels. De browser voert daarom
geen strikte broncontrole of echte herverificatie uit. Een strikt oordeel
vereist later opnieuw de twee originele bronbestanden via
`review_044_inspection_evidence_cli.py --run`.

Bij nieuwe bestandskeuze of afmelden wordt de tijdelijke weergave
gewist. Het extra JavaScriptbestand staat alleen op de expliciete
lokale allowlist van de server.

**Status: DRAFT / NOT EXECUTED / HOLD / DENY.**

### PP-RECOVERY-002 — alleen-lezen herstelcoördinatie

De module `review_044_recovery_coordination.py` biedt
`compile_recovery_coordination(handoff_bytes, technical_report_bytes,
owner_worksheet_bytes)` aan. De functie herbeoordeelt drie originele
lokale bytebestanden via de strikte bestaande contracten:
`parse_review_handoff`, `assess_inspection_technical_report` en
`validate_inspection_owner_worksheet` (via de bewijscompiler).
Ongeldige invoer wordt geweigerd met
`PP_RECOVERY_002_COORDINATION_INVALID`. De uitvoer bevat uitsluitend
drie SHA-256-verwijzingen, niet-persoonsgebonden status- en telvelden,
en verplichte blokkades. Er komen geen P.P.-nummers, consumer-ID's,
gebruikersnamen, sessies of geheimen in het overzicht.

**Zeer belangrijk:** de bronnen kunnen elk intern consistent zijn
zonder dat de identiteit of bevoegdheid van hun maker, of een
gemeenschappelijke subjectbinding, is vastgesteld. Daarom blijft
`crossSourceSubjectBinding=NOT_ESTABLISHED`,
`ownerAuthority=NOT_ESTABLISHED` en
`palacoOneSession=NOT_CREATED`. Er wordt geen PALACO ONE-account
aangemaakt, geen bestaande registratie aangepast en geen uitgifte toegestaan.
De volgende stap is alleen
`MANUAL_SOURCE_AND_IDENTITY_REVIEW_ONLY`.

De opt-in CLI `review_044_recovery_coordination_cli.py` opent geen
bronbestanden zonder expliciet `--run`. Tijdens de latere eigenaartestsessie:

```powershell
python .\review_044_recovery_coordination_cli.py --run --handoff "PP_HANDOFF.json" --technical "TECHNISCH.json" --worksheet "EIGENAAR.json"
```

Met optioneel `--export "PP_RECOVERY_002_HOLD.json"` wordt alleen een
nieuw bestand aangemaakt; bestaande bestanden worden nooit overschreven.
Zonder `--export` wordt alleen JSON naar de terminal geschreven.
Er is geen netwerk-, database-, runtime- of authenticatieactie.

De backoffice bevat nu het paneel **PP-RECOVERY-002 /
herstelcoördinatie — alleen lezen**. Het leest een bestaand JSON-rapport
(maximaal 16 KiB) via de lokale File API en toont drie afzonderlijke
rubrieken: P.P.-status, Review 044-bewijsclaim en de identiteitsblokkades.
Dit is uitsluitend een browserindicatie van **onvertrouwde** JSON:
`JSON.parse` is geen bewijs van een uitgevoerde Python-validator en
detecteert geen dubbele sleutels. Bij bestandswissel of afmelding wordt
de weergave gewist. De serverroute voor dit script is expliciet
geallowlist; geen API voor uploads, accountbinding of autorisatie is toegevoegd.

**Status: DRAFT / NOT EXECUTED / NOT_VERIFIED / HOLD / DENY /
NOT_AUTHORIZED.**

### PP-RECOVERY-002 — beslisdossier met vijf geblokkeerde bewijsvereisten

`review_044_recovery_decision.prepare_decision_dossier(handoff_bytes,
technical_report_bytes, owner_worksheet_bytes, review_marks=None)`
bereidt vanuit **de drie originele bytestromen** een nieuw, alleen-lezen
beslisdossier voor. Het gebruikt de bestaande strikte herstelcoördinator
en doet geen runtime-, test-, database-, netwerk- of PALACO ONE-operaties.

Vijf vereisten staan **onvoorwaardelijk op `NOT_ESTABLISHED / BLOCKED`**:

1. `SOURCE_ATTESTATION` — onafhankelijk bewijs van bronherkomst;
2. `CROSS_SOURCE_SUBJECT` — onafhankelijk bewijs dat bronnen hetzelfde
   subject betreffen;
3. `OWNER_AUTHORITY` — geauthenticeerde eigenaarsbevoegdheid;
4. `RUNTIME_EXECUTION` — onafhankelijke vaststelling van uitvoering;
5. `HUMAN_REVIEW` — vastgelegde beoordeling door een bevoegde reviewer.

Een optioneel, afzonderlijk bestand met maximaal vijf expliciete
eigenaarsmarkeringen kan uitsluitend `NOT_REVIEWED`,
`REVIEW_REQUESTED` of `BLOCKER_REPORTED` bevatten. Dit zijn
**zelfgerapporteerde planningsmarkeringen**, geen afgeronde bewijscontroles.
Niet ingevulde markeringen blijven `NO_OBSERVATION`. Geen enkele
markering kan een bewijsstatus of autorisatiepoorten veranderen.

`review_044_recovery_decision_cli.py` is uitsluitend opt-in; zonder
`--run` leest hij geen bronbestanden. Een latere eigenaartestsessie kan
de volgende opdracht gebruiken:

```powershell
python .\review_044_recovery_decision_cli.py --run --handoff "PP_HANDOFF.json" --technical "TECHNISCH.json" --worksheet "EIGENAAR.json" --export "PP_RECOVERY_DECISION_HOLD.json"
```

`--marks "MARKERINGEN.json"` is optioneel. Zonder `--export`
schrijft de CLI uitsluitend naar de terminal; met `--export` wordt
uitsluitend een **nieuw** bestand gemaakt. Een bestaand bestand
wordt nooit overschreven.

De backoffice heeft een aanvullend, alleen-lezen paneel
**PP-RECOVERY-002 / beslisdossier — vijf bewijsvereisten**. Het leest
een door de eigenaar gekozen dossier van maximaal 16 KiB lokaal en
toont de vijf poorten, bronhashes en de geblokkeerde PALACO ONE-overdracht.
Een browsercontrole op ingelezen JSON bewijst geen Python-uitvoering
en detecteert geen dubbele sleutels. De server serveert uitsluitend het
specifiek toegestane script. Geen upload, accountkoppeling of uitgifte.

**Onvoorwaardelijke uitkomst:** `crossSourceSubjectBinding=NOT_ESTABLISHED`,
`ownerAuthority=NOT_ESTABLISHED`, `humanReview=NOT_COMPLETED`,
`palacoOneHandoff=BLOCKED`, `palacoOneSession=NOT_CREATED`,
`NOT_VERIFIED / HOLD / DENY / NOT_AUTHORIZED`.

**Status: DRAFT / NOT EXECUTED.**

### Human-review queue — ongetekende verzoeken, geen beslissingsbevoegdheid

`review_044_human_review_queue.append_review_request(
dossier_bytes, previous_queue_bytes, requirement_id, action)` bereidt
een **nieuw lokaal snapshot** voor van een aan een specifiek beslisdossier
gebonden rij verzoeken. De Python-parser weigert onbekende velden,
dubbele JSON-sleutels, een onjuist beslisdossier, gewijzigde voorganger-
of entry-hashes, volgordefouten en autorisatie-escalaties.
Maximaal 128 gebeurtenissen / 128 KiB per snapshot.
Een hashketen zonder externe verankering is **geen** bewijs van een
onveranderlijke geschiedenis.

Alleen deze verzoektypen bestaan:
`REVIEW_REQUESTED`, `EVIDENCE_REQUESTED`,
`BLOCKER_REPORTED`. Ze kunnen worden gekoppeld aan precies vijf
vaste bewijsvereisten: `SOURCE_ATTESTATION`,
`CROSS_SOURCE_SUBJECT`, `OWNER_AUTHORITY`,
`RUNTIME_EXECUTION` en `HUMAN_REVIEW`.
Er is opzettelijk **geen** `APPROVED`, `PASS`,
`IDENTITY_VERIFIED` of `ISSUANCE`-actie.
Geen authenticatie of bevoegdheid van een reviewer is in dit
prototype vastgesteld: `UNSIGNED_LOCAL_REVIEW_REQUEST` is
een beperkte provenanceclaim, geen menselijke ondertekening.

`review_044_human_review_queue_cli.py` is opt-in. Zonder
`--run` worden geen bestanden geopend. Later, tijdens de
eigenaartestsessie, kan een nieuw snapshot worden voorbereid met:

```powershell
python .\review_044_human_review_queue_cli.py --run --dossier "PP_RECOVERY_DECISION_HOLD.json" --requirement "SOURCE_ATTESTATION" --action "EVIDENCE_REQUESTED" --export "PP_REVIEW_QUEUE_001.json"
```

Gebruik bij een volgende gebeurtenis ook
`--previous "PP_REVIEW_QUEUE_001.json"` en een **nieuw**
`--export`-pad. De CLI schrijft uitsluitend bij deze expliciete actie,
weigert overschrijven en wijzigt de bronbestanden niet.

De backoffice bevat het alleen-lezen paneel
**PP-RECOVERY-002 / human-review queue** voor een bestaand
beslisdossier en queue-snapshot. Het geeft uitsluitend een
browservergelijking op herkenbare velden; het kan geen dubbele
JSON-sleutels of de volledige cryptografische keten normatief
beoordelen. De Python-module blijft leidend. De server heeft
alleen een expliciete route voor het extra JavaScriptbestand.
Geen accountmutatie, externe toegang, testen, merge of uitrol.

**Alle vijf poorten blijven BLOCKED. Status:
DRAFT / NOT EXECUTED / NOT_VERIFIED / HOLD / DENY /
NOT_AUTHORIZED.**

### Human-review intake — bewijsstukken en reviewerclaims, niet geverifieerd

`review_044_review_intake.append_review_intake(
decision_dossier_bytes, review_queue_bytes, previous_intake_bytes,
request_sequence, evidence_bytes, evidence_kind, submitter_role_claim)`
bereidt offline een nieuw, beperkt `palaco.pp.recovery-002-review-intake.v0`
JSON-snapshot voor. Het verlangt het **originele beslisdossier**, een
volledig strikte queue-snapshot en het door de eigenaar bewust gekozen
bewijsbestand (max. 64 KiB). Het koppelt dat bewijsbestand uitsluitend
via SHA-256 aan een bestaand reviewverzoek. De uitvoer bevat geen
bewijsinhoud, reviewernaam, P.P.-nummer, consumer-ID of sessietoken.

`submitterRoleClaim` is beperkt tot `OWNER_CLAIMED`,
`REVIEWER_CLAIMED` of `SOURCE_CLAIMED`. **Geen daarvan bewijst
identiteit of bevoegdheid**. Bewijstypen zijn `DOCUMENT`,
`SCREENSHOT`, `LOG_EXCERPT`, `OTHER_UNTRUSTED`.
De intake weigert onbekende velden, dubbele JSON-sleutels, gemanipuleerde
hashketens, ontbrekende reviewverzoeken, een verkeerde dossier- of
queue-binding, dubbele bewijsverwijzingen binnen hetzelfde verzoek en
pogingen tot autorisatieverhoging. Maximaal 64 intake-items en 16 KiB
per JSON-snapshot. Ook een geldige keten bewijst zonder externe
ondertekening geen onveranderlijke historie.

`review_044_review_intake_cli.py` voert **niets** uit zonder `--run`.
Later kan de eigenaar een nieuwe intake voorbereiden met:

```powershell
python .\review_044_review_intake_cli.py --run --dossier "PP_RECOVERY_DECISION_HOLD.json" --queue "PP_REVIEW_QUEUE_001.json" --request-sequence 1 --evidence "BEWIJSSTUK.json" --kind DOCUMENT --role-claim REVIEWER_CLAIMED --export "PP_REVIEW_INTAKE_001.json"
```

Bij een volgend item is `--previous "PP_REVIEW_INTAKE_001.json"`
vereist. De bijbehorende **zelfde queue-snapshot** moet behouden blijven;
nieuwe queueversies vergen een nieuwe intakeketen. Export is create-only,
zonder overschrijven. De CLI start geen tests, upload, databasewijziging
of PALACO ONE-inlog. De status is zonder uitzondering:
`sourceAuthenticity=NOT_ESTABLISHED`,
`reviewerAuthentication=NOT_ESTABLISHED`,
`reviewerAuthority=NOT_ESTABLISHED`, `subjectBinding=NOT_ESTABLISHED`,
`NOT_VERIFIED / HOLD / DENY / NOT_AUTHORIZED`.

**Status: DRAFT / NOT EXECUTED.**

### Backoffice — read-only intakeoverzicht bewijsstukken en reviewerclaims

De bestaande lokale beheerpagina heeft nu het paneel
**PP-RECOVERY-002 / bewijs-intake en reviewerclaims — alleen lezen**.
De eigenaar kan drie bestaande lokale bestanden kiezen: het
beslisdossier (maximaal 16 KiB), de bijbehorende human-review queue
(maximaal 128 KiB) en het review-intake-snapshot (maximaal 16 KiB).
Het paneel leest de bestanden alleen na een expliciete klik, uitsluitend
via de browser-File API.

De presentatie scheidt:
- **Bewijsverwijzingen**: volgnummer, reviewverzoek, bewijsvereiste,
  bewijstype en verkorte SHA-256 van het oorspronkelijke bewijsbestand;
- **Reviewer-/indienersrolclaims**: `OWNER_CLAIMED`,
  `REVIEWER_CLAIMED` of `SOURCE_CLAIMED`, expliciet onbevestigd;
- **Alle vijf beslisvereisten**: altijd `NOT_ESTABLISHED / BLOCKED`;
- **Statusoverzicht**: `reviewerAuthority=NOT_ESTABLISHED`,
  `sourceAuthenticity=NOT_ESTABLISHED`, PALACO ONE-overdracht
  `BLOCKED`, `NOT_VERIFIED / HOLD / DENY / NOT_AUTHORIZED`.

De browser controleert herkenbare vaste velden, grenzen, rijvolgorde,
het verband met de opgegeven queue-verzoeken en tegenstrijdige
autorisatieclaims. Dit is **geen normatieve SHA-256-ketenvalidatie**:
de browser herberekent de canonieke dossier- en queuehashes niet,
controleert de volledige historische keten niet en kan dubbele JSON-sleutels
niet betrouwbaar detecteren. De bestaande Python-module
`review_044_review_intake.py` blijft het strikte in-memory contract.
Zelfs een strikt consistente intake is een ongetekende, niet-onafhankelijk
geverifieerde claim.

Bij bestandswissel of afmelding wordt de vorige intakeweergave gewist.
Het script is toegevoegd aan de beperkte lokale server-allowlist.
Er is geen nieuw uploadendpoint, databasewijziging, aanmeldroute,
achtergrondtaak, testuitvoering, merge of publicatie.

**Status: DRAFT / NOT EXECUTED / NOT_VERIFIED / HOLD / DENY /
NOT_AUTHORIZED.**

### Intakebeoordeling — per bewijsstuk ontbrekende controles (DRAFT)

De pure functie `review_044_intake_assessment.assess_review_intake(
decision_dossier_bytes, review_queue_bytes, intake_bytes)`
controleert opnieuw de oorspronkelijke dossier-, queue- en intakecontracten.
Een fout in structuur, volgorde, digestketen, queuebinding, rolclaim
of duplicaatverwijzing wordt geweigerd met
`PP_RECOVERY_002_INTAKE_ASSESSMENT_INVALID`.
Ze leest geen bewijsinhoud van schijf, voert geen tests uit en stelt
nimmer bron- of revieweridentiteit vast.

Ieder intake-item krijgt zes expliciet openstaande controles:

1. `ORIGINAL_EVIDENCE_BYTES_NOT_RECHECKED`;
2. `SOURCE_PROVENANCE_NOT_ATTESTED`;
3. `SUBMITTER_IDENTITY_NOT_AUTHENTICATED`;
4. `REVIEWER_AUTHORITY_NOT_ESTABLISHED`;
5. `SUBJECT_BINDING_NOT_ESTABLISHED`;
6. `INDEPENDENT_REVIEW_NOT_COMPLETED`.

Het rapport bevat tevens de SHA-256 van de originele intakebytes,
de canonieke dossier- en queuedigests, aantallen en vijf open
bewijsvereisten, die allemaal `NOT_ESTABLISHED / BLOCKED` blijven.
Het originele bewijsbestand wordt niet meegeleverd en zijn hash
wordt daarom **niet opnieuw vergeleken** met originele bewijsbytes.
Interne consistentie is geen attestatie of bewijs van de uitvoerder.

De opt-in `review_044_intake_assessment_cli.py` leest niets zonder
`--run`. Tijdens een latere door de eigenaar uitgevoerde testsessie:

```powershell
python .\review_044_intake_assessment_cli.py --run --dossier "PP_RECOVERY_DECISION_HOLD.json" --queue "PP_REVIEW_QUEUE_001.json" --intake "PP_REVIEW_INTAKE_001.json" --export "PP_INTAKE_ASSESSMENT_HOLD.json"
```

Zonder `--export` geeft de CLI JSON op de terminal; met `--export`
maakt hij alleen een nieuw bestand aan. Overschrijven wordt geweigerd.
Geen PALACO ONE-accountactie, netwerkverzoek, databasewijziging,
testuitvoering of stilzwijgende bevoegdheidsverlening.

Het backofficepaneel **PP-RECOVERY-002 / intakebeoordeling —
ontbrekende controles** kan een eerder opgeslagen rapport van maximaal
64 KiB uitsluitend lokaal tonen. De browser controleert het herkenbare
schema, vaste HOLD-velden, aantallen en vereisten, maar verifieert
niet onafhankelijk dat Python is uitgevoerd. `JSON.parse` is geen
normatieve strikte bronparser; de originele drie bestanden blijven
nodig voor de Python-contractcontrole.

**DRAFT / NOT EXECUTED / NOT_VERIFIED / HOLD / DENY / NOT_AUTHORIZED.**

### Verificatieplan — zes afhankelijke stappen per bewijsstuk

`review_044_verification_plan.prepare_verification_plan(
decision_dossier_bytes, review_queue_bytes, intake_bytes)` valideert
eerst de **originele drie bestanden** via het bestaande strikte
intakebeoordelingscontract. Daarna wordt voor ieder intake-item
een workflow met precies zes handmatige controles voorbereid:
originele bewijsbytes vergelijken (1); onafhankelijke bronherkomst
verkrijgen (2, na 1); indiener onafhankelijk authenticeren (3);
reviewer onafhankelijk authenticeren en bevoegdheid vaststellen (4);
subjectbinding aantonen (5, na 2 en 3); gedocumenteerde onafhankelijke
review afronden (6, na 1 t/m 5).

De vijf bestaande beslispoorten hebben ieder expliciete afhankelijkheden
en blijven zonder uitzondering `NOT_ESTABLISHED / BLOCKED`.
Elke geplande controle heeft `status=NOT_STARTED`,
`verification=NOT_VERIFIED` en
`reviewerAuthority=NOT_ESTABLISHED`. Geen automatisch bewijsresultaat,
voltooiingsmarkering, PASS, identiteitsbinding of PALACO ONE-sessie.
Bron- en beoordelingsdossier, queue en intake worden verbonden met
SHA-256-verwijzingen. Een digest is geen onafhankelijke attestatie.

De CLI `review_044_verification_plan_cli.py` is bewust opt-in:
zonder `--run` worden geen bronbestanden geopend. Pas tijdens de
latere eigenaartestsessie mag de gebruiker expliciet kiezen voor:

```powershell
python .\review_044_verification_plan_cli.py --run --dossier "PP_RECOVERY_DECISION_HOLD.json" --queue "PP_REVIEW_QUEUE_001.json" --intake "PP_REVIEW_INTAKE_001.json" --export "PP_VERIFICATION_PLAN_HOLD.json"
```

Zonder `--export` wordt alleen naar stdout geschreven; met
`--export` uitsluitend naar een nieuw bestand. Geen overschrijving,
netwerk, database, tests, reviewerautorisatie of productieactie.

**DRAFT / NOT EXECUTED / NOT_VERIFIED / HOLD / DENY / NOT_AUTHORIZED.**

### Backoffice — alleen-lezen verificatieplan met afhankelijkheden

Het aanvullende paneel **PP-RECOVERY-002 / verificatieplan —
zes afhankelijke stappen** leest een reeds opgeslagen
`palaco.pp.recovery-002-verification-plan.v0`-JSON van maximaal
128 KiB volledig lokaal. De eigenaar ziet per intake-item de zes
voorbereide controles, de expliciete voorwaarden voor elke stap en
de vijf beslispoorten met hun afhankelijke controlevolgordes.

De browser weigert een afwijkend schema, onbekende velden, onjuiste
hashvormen, onmogelijke aantallen, ontbrekende controles, afwijkende
volgorde, gewijzigde afhankelijkheden, of enige claim van uitvoering
of vrijgave. `NOT_STARTED / NOT_VERIFIED / NOT_ESTABLISHED / BLOCKED`
zijn vaste contractwaarden. Geen check wordt uitgevoerd of afgevinkt.

**Strikte scheiding:** de ingelezen JSON kan nagemaakt zijn en
`JSON.parse` herkent dubbele sleutels niet als fout. Het paneel
controleert niet opnieuw de oorspronkelijke dossier-, queue- en
intakebytes. De bestaande offline Python-module
`review_044_verification_plan.py` blijft het normatieve contract voor
interne consistentie; ook die module verstrekt geen externe attestatie
of identiteitsautorisatie.

Het afzonderlijke JavaScriptbestand is toegevoegd aan de expliciete
lokale server-allowlist. Bij bestandswissel, verborgen beheerderssessie
of afmelding wordt de tijdelijke weergave gewist. Er is geen nieuwe
API, upload, databasewijziging, netwerkverzoek, runner, merge of uitrol.

**Status: DRAFT / NOT EXECUTED / NOT_VERIFIED / HOLD / DENY /
NOT_AUTHORIZED.**

### PP-RECOVERY-002 — observatieregister voor verificatiestappen (DRAFT)

De pure module `review_044_observation_register.py` biedt
`append_observation(dossier_bytes, queue_bytes, intake_bytes,
verification_plan_bytes, previous_register_bytes,
intake_sequence, check_order, mark)`. Hij valideert opnieuw alle
oorspronkelijke dossier-/queue-/intakecontracten, bouwt het
verificatieplan in geheugen opnieuw op en vergelijkt de volledige
planstructuur type-exact met het aangeleverde planbestand.
Daarna controleert hij elk event uit het vorige register,
inclusief volgnummer, verwijzingen en de SHA-256-hashketen.

Er zijn uitsluitend drie **zelfgerapporteerde** markeringen:

- `OBSERVATION_REPORTED` — een eigen waarneming gemeld;
- `BLOCKER_REPORTED` — een blokkade gemeld;
- `RECHECK_REQUESTED` — een nieuwe controle gevraagd.

Iedere gebeurtenis bindt aan één `intakeSequence` en één
`checkOrder` (1 t/m 6) met de onveranderlijke
`checkId` uit het verificatieplan. Het nieuwe snapshot bevat
maximaal 128 gebeurtenissen en 128 KiB JSON. De gehele
historie is uitsluitend een **lokale hashketenclaim**; zonder
onafhankelijke verankering of handtekening levert dit geen
bewijs van ongewijzigde historie, tijd of revieweridentiteit.

Alle events behouden `checkStatus=NOT_STARTED`,
`verification=NOT_VERIFIED` en `gate=BLOCKED`.
De registerkop houdt `humanReview=NOT_COMPLETED`,
`reviewerAuthority=NOT_ESTABLISHED` en
`HOLD / DENY / NOT_AUTHORIZED` vast. Er is geen actie
voor PASS, COMPLETED, identiteitsactivatie of uitgifte.

De lokale CLI `review_044_observation_register_cli.py` is
uitdrukkelijk opt-in. Zonder `--run` wordt geen bestand
geopend. Tijdens een latere eigenaartestsessie kan bijvoorbeeld
een eerste snapshot worden aangemaakt:

```powershell
python .\review_044_observation_register_cli.py --run --dossier "PP_RECOVERY_DECISION_HOLD.json" --queue "PP_REVIEW_QUEUE_001.json" --intake "PP_REVIEW_INTAKE_001.json" --plan "PP_VERIFICATION_PLAN_HOLD.json" --intake-sequence 1 --check-order 1 --mark OBSERVATION_REPORTED --export "PP_OBSERVATION_001.json"
```

Voor opvolgende waarnemingen wordt ook het vorige bestand
opgegeven met `--previous "PP_OBSERVATION_001.json"`,
gecombineerd met een **nieuwe** `--export`-bestandsnaam.
De CLI maakt uitsluitend een nieuw bestand aan, weigert
overschrijven en verandert de oorspronkelijke bronnen niet.
Zonder `--run` geen uitvoering; ook met `--run` worden
geen technische of identiteitscontroles uitgevoerd — alleen
bestaande JSON-contracten beoordeeld voor een self-report.

**DRAFT / NOT EXECUTED / NOT_VERIFIED / HOLD / DENY /
NOT_AUTHORIZED.**

### Backoffice — alleen-lezen observatiegeschiedenis per verificatiestap

De PALACO PHONE-backoffice heeft nu het paneel
**PP-RECOVERY-002 / voortgangsregister — ongetekende waarnemingen**.
Het leest een eerder opgeslagen verificatieplan (maximaal 128 KiB)
en een observatiesnapshot (maximaal 128 KiB) via de lokale browser-File API.
Geen automatische runner, netwerkoverdracht, database-opslag of
PALACO ONE-identiteitshandeling wordt aangeroepen.

De browser controleert een beperkte herkenbare structuur en berekent
SHA-256 van de **originele planbytes**, die gelijk moet zijn aan
`verificationPlanSha256` in het observatiesnapshot. Per
gebeurtenis toont het paneel volgnummer, intake, checknummer, check-ID,
zelfrapportagemarkering en een verkorte eventhash. Het telt afzonderlijk
`OBSERVATION_REPORTED`, `BLOCKER_REPORTED` en
`RECHECK_REQUESTED`.

**Verificatiegrens:** de browser herberekent niet de hele eventhashketen,
kan dubbele JSON-sleutels niet betrouwbaar weigeren en controleert niet
de originele onderliggende dossier-, queue- en intakecontracten.
Het paneel is uitsluitend een **lokale indicatie** van ongetekende
gebruikersbestanden. De pure Python-module
`review_044_observation_register.py` blijft het strikte contract
voor hashketen- en dossierconsistentie. Ook strikte consistentie
bewijst geen externe historie, persoonlijke identiteit, menselijke
review of bronauthenticiteit.

Bij bestandwijziging, sessieverlies of afmelding wordt de weergave
gewist. Het script is afzonderlijk toegevoegd aan de beperkte
lokale server-allowlist, zonder nieuw uploadendpoint.
**Alle controles blijven `NOT_STARTED`, de vijf beslispoorten
`BLOCKED`, en PALACO ONE-overdracht blijft geblokkeerd.**

**Status: DRAFT / NOT EXECUTED / NOT_VERIFIED / HOLD / DENY /
NOT_AUTHORIZED.**

### Overkoepelende herstelcockpit — vijf bewijsstromen, één read-only status

`review_044_recovery_cockpit.prepare_recovery_cockpit(
dossier_bytes, queue_bytes, intake_bytes, plan_bytes, register_bytes)`
bouwt een **beperkte samenhangsrapportage** uit de oorspronkelijke
vijf lokale bestanden: beslisdossier, human-review queue,
review-intake, verificatieplan en observatieregister. De Pythonmodule
gebruikt de bestaande strikte parsers en eist onderlinge binding.
Het plan wordt uit de originele bronnen opnieuw samengesteld en
type-exact gecontroleerd; het observatieregister wordt opnieuw
beoordeeld inclusief zijn lokale eventhashketen.
Een ongeldig bestand, mismatch of rechtenescalatie wordt geweigerd
met `PP_RECOVERY_002_COCKPIT_INVALID`.

Het JSON-rapport scheidt vijf **ruwe bestands-SHA-256** van
verzoek-, intake-, controle- en waarnemingsaantallen. Alle vijf
beslispoorten blijven `BLOCKED / NOT_VERIFIED`; geen teller of
technische consistentie kan dit wijzigen.
`independentSourceAttestation=ABSENT`,
`reviewerAuthority=NOT_ESTABLISHED`,
`subjectBinding=NOT_ESTABLISHED`,
`historicalImmutability=NOT_ESTABLISHED`,
`palacoOneHandoff=BLOCKED`, `NOT_VERIFIED / HOLD / DENY /
NOT_AUTHORIZED` blijven verplicht.

De CLI `review_044_recovery_cockpit_cli.py` leest geen bestanden
zonder `--run`. Tijdens de latere eigenaartestsessie kan de
eigenaar expliciet een nieuw rapport voorbereiden:

```powershell
python .\review_044_recovery_cockpit_cli.py --run --dossier "PP_RECOVERY_DECISION_HOLD.json" --queue "PP_REVIEW_QUEUE_001.json" --intake "PP_REVIEW_INTAKE_001.json" --plan "PP_VERIFICATION_PLAN_HOLD.json" --observations "PP_OBSERVATION_001.json" --export "PP_RECOVERY_COCKPIT_HOLD.json"
```

`--export` is create-only, nooit een overschrijving. Zonder
`--export` wordt uitsluitend JSON naar stdout geschreven.
Dit is een opt-in lokale samenhangsbeoordeling, geen uitvoering van
tests, bewijscontroles of identiteitsactivatie.

Het lokale backofficepaneel **PP-RECOVERY-002 / herstelcockpit —
alle vijf bewijsstromen** leest de vijf originele JSON-bestanden
plus het eerder geëxporteerde cockpitrapport. De browser herberekent
SHA-256 voor de **originele byteinhoud** van de vijf geselecteerde
bestanden en vergelijkt die met de SHA-256 in het ongetekende
cockpitrapport. De rapportclaims en vaste HOLD-staten zijn apart
zichtbaar. Het paneel voert **niet** alle Python-validaties opnieuw
uit, detecteert geen dubbele JSON-sleutels en bewijst niet wie het
rapport heeft vervaardigd. Er is geen netwerkverkeer, upload,
database-mutatie of account-API toegevoegd.

Bij bestandswijziging, een verborgen beheerderssessie of afmelden
wordt de tijdelijke weergave gewist. Het extra JavaScriptbestand
is enkel via de expliciete lokale server-allowlist bereikbaar.

**DRAFT / NOT EXECUTED / NOT_VERIFIED / HOLD / DENY /
NOT_AUTHORIZED.**

### Centraal PP-RECOVERY-002 herstelstatusrapport — blokkades en vervolgstappen

De pure functie `review_044_recovery_status.build_recovery_status_report(
dossier_bytes, queue_bytes, intake_bytes, plan_bytes, observations_bytes)`
valideert vijf oorspronkelijke lokale JSON-bestanden via de bestaande
strikte herstelcockpit. Ongeldige broncontracten, inconsistente
verwijzingen, afwijkende eventketens en vrijgaveclaims worden geweigerd.
Het resultaat bevat SHA-256-verwijzingen, aantallen, een vaste set van
**vijf geblokkeerde beslispoorten** en zes onveranderlijk
`NOT_STARTED / NOT_VERIFIED` controlefasen.

De acht voorgestelde **toekomstige handmatige acties** zijn geordend:
oorspronkelijke bestanden behouden, bewijsbytes hervergelijken,
bronherkomst onafhankelijk onderbouwen, indiener authenticeren,
reviewerbevoegdheid vaststellen, subjectbinding aantonen,
bevoegde menselijke review vastleggen en pas daarna een afzonderlijk
bevoegd HOLD-besluit laten herbeoordelen. De acties worden in dit
rapport **niet uitgevoerd** en hebben
`authorizationEffect=NONE`. De herbeoordeling is een
voorstel voor een externe bevoegde workflow, nooit een automatische
opheffing van HOLD.

De opt-in CLI `review_044_recovery_status_cli.py` leest geen
bronbestanden zonder `--run`. Tijdens een latere testsessie kan
de eigenaar een statusrapport opstellen met:

```powershell
python .\review_044_recovery_status_cli.py --run --dossier "PP_RECOVERY_DECISION_HOLD.json" --queue "PP_REVIEW_QUEUE_001.json" --intake "PP_REVIEW_INTAKE_001.json" --plan "PP_VERIFICATION_PLAN_HOLD.json" --observations "PP_OBSERVATION_001.json" --export "PP_RECOVERY_STATUS_HOLD.json"
```

Met `--export` wordt uitsluitend een **nieuw** bestand gemaakt;
bestaande bestanden worden nooit overschreven. Zonder
`--export` schrijft de CLI alleen JSON naar stdout. Er worden
geen tests, proof checks, accountsessies of autorisatiehandelingen
gestart.

Het nieuwe backofficepaneel **PP-RECOVERY-002 / centraal
herstelstatusrapport — alleen lezen** leest het geëxporteerde JSON
van maximaal 32 KiB. Het toont brongetallen, de vijf poorten,
de zes controlefasen en acht handmatige vervolgstappen. De browser
weigert tegenstrijdige vaste HOLD-statussen, maar valideert niet
opnieuw de vijf originele broncontracten, de volledige SHA-256-ketens
of de herkomst van het statusbestand. Het blijft een **ongetekende
browserindicatie**, geen onafhankelijk Python-attest.

Het JavaScriptbestand staat op de expliciete lokale server-allowlist.
Er is geen nieuwe upload/API-route, testuitvoering, merge of
productie-uitrol. Bij bestandswijziging of afmelden wordt de tijdelijke
weergave gewist.

**DRAFT / NOT EXECUTED / NOT_VERIFIED / HOLD / DENY /
NOT_AUTHORIZED.**

### PP-RECOVERY-002 — vrijgavegereedheidsanalyse: alleen ontbrekende voorwaarden

`review_044_release_readiness.analyze_release_readiness(
dossier_bytes, queue_bytes, intake_bytes, plan_bytes, observations_bytes)`
hergebruikt de strikte vijfbron-controle via
`build_recovery_status_report`. De functie retourneert een
niet-autorisatieverlenend rapport van **zes globale blokkades**,
**vijf afzonderlijke beslispoorten** en voor elke poort precies
de ontbrekende handmatige verificatiestappen uit het eerder
vastgelegde zesstappenplan. De geblokkeerde poorten krijgen
één voorgestelde externe handmatige vervolgrichting.

Het schema `palaco.pp.recovery-002-release-readiness.v0` heeft
onvoorwaardelijk `overallReadiness=NOT_READY`,
`blockedGateCount=5`, `gate=BLOCKED`,
`readiness=NOT_READY`, `manualDecision=REQUIRED_OUTSIDE_THIS_MODULE`,
`independentVerification=NOT_VERIFIED`,
`reviewerAuthority=NOT_ESTABLISHED`,
`authorization=HOLD`, `accessDecision=DENY`,
`issuance=NOT_AUTHORIZED` en `palacoOneHandoff=BLOCKED`.
Interne consistentie of het bestaan van veel zelfrapportages
is geen toestemming, revieweridentiteit of onafhankelijke attestatie.

De opt-in `review_044_release_readiness_cli.py` leest niets zonder
`--run`. Tijdens een latere gebruikerssessie kan een nieuw rapport
als volgt worden voorbereid:

```powershell
python .\review_044_release_readiness_cli.py --run --dossier "PP_RECOVERY_DECISION_HOLD.json" --queue "PP_REVIEW_QUEUE_001.json" --intake "PP_REVIEW_INTAKE_001.json" --plan "PP_VERIFICATION_PLAN_HOLD.json" --observations "PP_OBSERVATION_001.json" --export "PP_READINESS_GAPS_HOLD.json"
```

`--export` maakt een nieuw bestand; overschrijven is verboden.
Zonder `--export` wordt het JSON-rapport uitsluitend naar stdout
geschreven. Er worden geen tests, identiteitscontroles, merge, deploy
of autorisatiehandelingen gestart.

Het backofficepaneel **PP-RECOVERY-002 / vrijgavegereedheid —
ontbrekende voorwaarden** leest een bestaand rapport tot 32 KiB
via de browser-File API. Het controleert op herkenbare schema-,
teller- en blokkadevelden, maar voert geen volledige strikte Python-
validatie uit en verifieert niet de oorspronkelijke vijf bronbestanden.
Ook het geraadpleegde rapport is een **ongetekende claim**.
Het nieuwe JavaScriptbestand is alleen aan de expliciete
lokale server-allowlist toegevoegd.

**Status: DRAFT / NOT EXECUTED / NOT_VERIFIED / NOT_READY /
HOLD / DENY / NOT_AUTHORIZED.**

### PP-RECOVERY-002 — ongetekend human-review handoffmanifest

De nieuwe pure module `review_044_human_review_handoff.py` bereidt
een overdrachts**manifest** voor op basis van de vijf oorspronkelijke
bronbestanden. De module hergebruikt de strikte
`analyze_release_readiness` en `build_recovery_status_report`
en laat alle vijf poorten `BLOCKED`. De output bevat vijf ruwe
bronbestand-SHA-256-referenties, de zes globale ontbrekende
voorwaarden, alle per-poort ontbrekende checks en canonieke digests
van de voorafgaande analyse- en statusobjecten. Er wordt geen
oorspronkelijke bewijsinhoud, PP-nummer, persoon of account-ID
in het manifest opgenomen.

Het schema `palaco.pp.recovery-002-human-review-handoff.v0`
verklaart expliciet `intendedRecipient=
INDEPENDENT_AUTHORIZED_HUMAN_REVIEWER_UNASSIGNED`,
`recipientAuthentication=NOT_ESTABLISHED`,
`recipientAuthorization=NOT_ESTABLISHED`,
`deliveryStatus=NOT_DELIVERED`,
`receiptStatus=NOT_ACKNOWLEDGED`,
`manifestProvenance=UNSIGNED_LOCAL_DRAFT`,
`originalEvidenceIncluded=false`,
`originalEvidenceRetention=REQUIRED_SEPARATELY`,
`releaseReadiness=NOT_READY` en
`HOLD / DENY / NOT_AUTHORIZED`.
Een dergelijke manifestclaim is geen bewijs van verzending,
ontvangst, onafhankelijke bronherkomst of bevoegde reviewer.

De opt-in `review_044_human_review_handoff_cli.py` opent zonder
`--run` geen bronbestanden. Later kan de eigenaar, tijdens de
eigen testsessie, expliciet een **nieuw** manifest voorbereiden:

```powershell
python .\review_044_human_review_handoff_cli.py --run --dossier "PP_RECOVERY_DECISION_HOLD.json" --queue "PP_REVIEW_QUEUE_001.json" --intake "PP_REVIEW_INTAKE_001.json" --plan "PP_VERIFICATION_PLAN_HOLD.json" --observations "PP_OBSERVATION_001.json" --export "PP_HUMAN_REVIEW_HANDOFF_HOLD.json"
```

De export schrijft alleen een nieuw bestand (`xb`), nooit een
bestaand bestand over; zonder `--export` alleen naar stdout.
Er wordt niets verstuurd of geauthenticeerd.

De backoffice heeft een afzonderlijk paneel
**PP-RECOVERY-002 / overdrachtsmanifest menselijke review — alleen
lezen**. De browser leest maximaal 32 KiB lokale JSON, toont
vijf bronreferenties, globale blokkades en vijf open poorten,
en weigert tegenstrijdige autorisatieclaims. De weergave is
uitsluitend **indicatief**: er is geen onafhankelijke herberekening
van de vijf originele bronhashes, geen strikte Python-validatie en
geen cryptografische attestatie van de manifestmaker.
Het nieuwe script staat uitsluitend op de expliciete lokale
server-allowlist. Geen API, upload, merge, tests of uitrol.

**DRAFT / NOT EXECUTED / NOT_DELIVERED / NOT_ACKNOWLEDGED /
NOT_VERIFIED / NOT_READY / HOLD / DENY / NOT_AUTHORIZED.**

### Ontvangst- en reviewerprotocol — uitsluitend onbevestigde claims

De pure module `review_044_review_protocol.py` biedt
`append_review_protocol_claim(dossier_bytes, queue_bytes, intake_bytes,
plan_bytes, observations_bytes, manifest_bytes,
previous_protocol_bytes, mark, role_claim, requirement_id)`.
Hij reconstrueert het bestaande, ongetekende handoffmanifest uit de vijf
originele bronnen, eist een **type-exacte** overeenkomst met het
aangeleverde manifest, bindt het protocol aan de SHA-256 van de
originele manifestbytes en valideert de hashketen van een eerder
protocol-snapshot. Onjuiste, te grote en tegenstrijdige gegevens worden
afgewezen met `PP_RECOVERY_002_REVIEW_PROTOCOL_INVALID`.

Het protocol accepteert uitsluitend **zelfgerapporteerde** categorieën:
`RECEIPT_CLAIMED`, `REVIEW_REQUESTED`,
`IDENTITY_CHECK_REQUESTED`, `AUTHORITY_CHECK_REQUESTED`,
`AUTHENTICATION_BLOCKER_REPORTED`, `EVIDENCE_GAP_REPORTED`
en `RECHECK_REQUESTED`. Een opgegeven rol is uitsluitend
`OWNER_CLAIMED`, `RECIPIENT_CLAIMED` of
`REVIEWER_CLAIMED`. Iedere claim is verbonden met één van de vijf
bewijspoorten en krijgt een volgnummer en lokale SHA-256-hashverwijzing.
Er is geen markering `RECEIVED_VERIFIED`, `REVIEW_APPROVED`,
`PASS` of `AUTHORIZED`.

Het register is maximaal 64 KiB, 64 events, en houdt
`receiptVerification=NOT_VERIFIED`,
`reviewerAuthentication=NOT_ESTABLISHED`,
`reviewerAuthority=NOT_ESTABLISHED`,
`humanReview=NOT_COMPLETED`, `gate=BLOCKED`,
`palacoOneHandoff=BLOCKED` en `HOLD / DENY /
NOT_AUTHORIZED` vast. De lokale hashketen heeft geen onafhankelijke
handtekening, timestamp of externe onveranderlijke verankering.

De CLI `review_044_review_protocol_cli.py` opent geen bestanden
zonder expliciet `--run`; `--export` is create-only en verplicht
voor een registratie. Tijdens een latere eigenaartestsessie:

```powershell
python .\review_044_review_protocol_cli.py --run --dossier "PP_RECOVERY_DECISION_HOLD.json" --queue "PP_REVIEW_QUEUE_001.json" --intake "PP_REVIEW_INTAKE_001.json" --plan "PP_VERIFICATION_PLAN_HOLD.json" --observations "PP_OBSERVATION_001.json" --manifest "PP_HUMAN_REVIEW_HANDOFF_HOLD.json" --mark IDENTITY_CHECK_REQUESTED --role-claim REVIEWER_CLAIMED --requirement HUMAN_REVIEW --export "PP_REVIEW_PROTOCOL_001.json"
```

Bij de volgende registratie is `--previous` met het vorige
protocol-snapshot nodig, terwijl `--export` naar een **nieuwe**
bestandsnaam verwijst. Een `RECEIPT_CLAIMED` is geen bewezen
ontvangst: voor een werkelijke beoordeling moet de reviewer via een
afzonderlijk onafhankelijk authenticatie- en autorisatieproces
worden vastgesteld, met een separaat besluitrecord buiten dit
claims-only protocol.

De backoffice heeft nu het nieuwe paneel
**PP-RECOVERY-002 / ontvangst- en beoordelingsprotocol — alleen lezen**.
De browser leest lokaal een manifest van maximaal 32 KiB en een
protocolsnapshot van maximaal 64 KiB, vergelijkt de
SHA-256 van de ongewijzigde manifestbytes en presenteert de
onbevestigde claims. De browser herberekent niet de complete
eventketen of de vijf oorspronkelijke broncontracten en kan dubbele
JSON-sleutels niet normatief uitsluiten. Het paneel is daarom
uitdrukkelijk niet geschikt als bewijs van ontvangst,
reviewerbevoegdheid, onafhankelijke beoordeling of vrijgave.
Geen API, upload, tests, merge of uitrol.

**DRAFT / NOT EXECUTED / NOT_DELIVERED /
RECEIPT_NOT_VERIFIED / REVIEWER_AUTHORITY_NOT_ESTABLISHED /
NOT_READY / HOLD / DENY / NOT_AUTHORIZED.**

### Onafhankelijke reviewer-authenticatie — beveiligingscontract, geen authenticator

De pure module `review_044_reviewer_auth_contract.py` levert het
contract `palaco.pp.recovery-002-reviewer-auth-contract.v0`.
Hij herbouwt het ongetekende handoffmanifest uit de oorspronkelijke
vijf bronnen en eist een type-exacte match; vervolgens valideert
hij het bijbehorende claims-only ontvangstprotocol en de volledige
lokale SHA-256-eventketen. Het resultaat koppelt de byte-SHA-256
van manifest en protocol aan de lijst van onvervulde externe eisen.
Een correcte keten geeft **geen** identiteit, bevoegdheid of onafhankelijk
bewijs van aflevering/ontvangst.

De acht noodzakelijke externe controles zijn:
1. betrouwbare, onafhankelijke identity provider;
2. verse, doelgroepgebonden challenge met phishingbestendige authenticatie;
3. onafhankelijk ondertekende reviewer-rolattestatie;
4. scope- en doelbinding aan PP-RECOVERY-002;
5. replaypreventie, geldigheid en intrekking met vertrouwde tijd en opslag;
6. onafhankelijke functiescheiding en belangenconflictcontrole;
7. ondertekend ontvangstbewijs over **exacte** manifestbytes;
8. extern verankerde, manipulatiebestendige auditregistratie.

De nieuwe contractmodule **implementeert geen enkele externe controle**:
`identityProviderIntegration=NOT_CONFIGURED`,
`credentialValidation=NOT_PERFORMED`,
`reviewerAuthentication=NOT_ESTABLISHED`,
`recipientAuthentication=NOT_ESTABLISHED`,
`reviewerAuthority=NOT_ESTABLISHED`,
`humanReview=NOT_COMPLETED` en alle vijf poorten blijven
`NOT_VERIFIED / BLOCKED`. PALACO ONE krijgt geen sessie of token.
Er bestaan geen PASS-, SIGN-, LOGIN- of GRANT-acties in dit contract.

`review_044_reviewer_auth_contract_cli.py` leest niets zonder
expliciet `--run`, en maakt uitsluitend een nieuw bestand
via `--export`. Een mogelijke *latere* offline eigenaarshandeling:

```powershell
python .\review_044_reviewer_auth_contract_cli.py --run --dossier "PP_RECOVERY_DECISION_HOLD.json" --queue "PP_REVIEW_QUEUE_001.json" --intake "PP_REVIEW_INTAKE_001.json" --plan "PP_VERIFICATION_PLAN_HOLD.json" --observations "PP_OBSERVATION_001.json" --manifest "PP_HUMAN_REVIEW_HANDOFF_HOLD.json" --protocol "PP_REVIEW_PROTOCOL_001.json" --export "PP_REVIEWER_AUTH_REQUIREMENTS_HOLD.json"
```

Het lokale backofficepaneel **PP-RECOVERY-002 / onafhankelijke
reviewer-authenticatie — eisencontract** leest uitsluitend een eerder
opgeslagen JSON-bestand van maximaal 32 KiB. Het paneel controleert
herkenbare vorm, acht vaste controle-ID's, vijf geblokkeerde poorten
en afwezigheid van autorisatieclaims, maar controleert niet opnieuw
de oorspronkelijke zeven documenten. Het is geen identiteitsprovider
en geen bewijs dat Python, externe crypto-validatie of reviewercontrole
heeft plaatsgevonden. Bij bestandwijziging of afmelden wordt de
weergave gewist; de statische module is op de expliciete
server-allowlist aangesloten. Geen tests, merge, deploy,
identiteitsuitgifte of wijziging van HOLD.

**DRAFT / NOT EXECUTED / NOT_VERIFIED / NOT_READY /
REVIEWER_AUTHORITY_NOT_ESTABLISHED / HOLD / DENY / NOT_AUTHORIZED.**

### Reviewer-identiteitsdienst — gescheiden architectuurcontract (niet actief)

`review_044_reviewer_service_blueprint.py` definieert drie strikt
gescheiden trust boundaries: **AUTHENTICATION**, **AUTHORIZATION** en
**AUDIT**. De module valideert eerst de vijf originele bronbestanden,
het ongetekende human-review handoffmanifest, het ontvangstprotocol
en het eerdere reviewer-authenticatiecontract. De oorspronkelijke
contractbytes worden gebonden via SHA-256. Het authenticatiecontract
moet exact overeenkomen met de opnieuw berekende structuur; een
afwijking wordt geweigerd met
`PP_RECOVERY_002_REVIEWER_SERVICE_BLUEPRINT_INVALID`.

De drie grenzen bevatten alleen **nog te implementeren eisen**:

- **Authenticatie**: vertrouwde issuer, doelgroepgebonden challenge,
  algoritme-/handtekeningcontrole, vertrouwde tijd, replaypreventie,
  sleutelintrekking. Toekomstige output: `IDENTITY_ASSERTION`.
- **Autorisatie**: onafhankelijke rolattestatie, PP-RECOVERY-002-scope,
  least privilege, functiescheiding, conflict-/intrekkingscontrole,
  deny-by-default. Toekomstige output: `REVIEWER_SCOPE_DECISION`.
- **Audit**: exact-manifestgebonden ondertekende ontvangst, onafhankelijke
  auditverankering, vertrouwde timestamp en externe verificatie.
  Toekomstige output: `SIGNED_RECEIPT_AND_IMMUTABLE_AUDIT_REFERENCE`.

De module **verifieert geen tokens, sleutels of handtekeningen**,
raadpleegt geen identity provider en schrijft geen auditrecord. De
drie services hebben `implementation=NOT_IMPLEMENTED`,
`trustEvaluation=NOT_PERFORMED` en `outboundAuthority=NONE`.
Alle acht reviewer-eisen blijven `NOT_ESTABLISHED` en alle vijf
beslispoorten `BLOCKED`. De vaste systeemstatus blijft
`NOT_VERIFIED / NOT_READY / HOLD / DENY / NOT_AUTHORIZED`.
Een claims-only ontvangst- of reviewerregistratie kan deze
trust boundary nooit oversteken.

De opt-in CLI `review_044_reviewer_service_blueprint_cli.py` opent
geen bestanden zonder `--run`. `--export` is verplicht en maakt
uitsluitend een nieuw bestand aan; er is geen overwrite, test-runner,
netwerkactie of autorisatieroute. Voor een latere eigenaartestsessie:

```powershell
python .\review_044_reviewer_service_blueprint_cli.py --run --dossier "PP_RECOVERY_DECISION_HOLD.json" --queue "PP_REVIEW_QUEUE_001.json" --intake "PP_REVIEW_INTAKE_001.json" --plan "PP_VERIFICATION_PLAN_HOLD.json" --observations "PP_OBSERVATION_001.json" --manifest "PP_HUMAN_REVIEW_HANDOFF_HOLD.json" --protocol "PP_REVIEW_PROTOCOL_001.json" --contract "PP_REVIEWER_AUTH_REQUIREMENTS_HOLD.json" --export "PP_REVIEWER_SERVICE_BLUEPRINT_HOLD.json"
```

Het nieuwe backofficepaneel **PP-RECOVERY-002 / reviewer-identiteitsdienst —
drie gescheiden beveiligingslagen** kan een bestaand lokaal JSON-rapport
van maximaal 32 KiB indicatief tonen. Browserimport valideert niet de
originele acht documenten, echte authenticatie of externe audit.
Het script staat op de beperkte server-allowlist; bij afmelding
of bestandwijziging wordt de lokale weergave gewist. Geen API, login,
merge, deploy, issuance of functionele tests.

**DRAFT / NOT EXECUTED / NOT_IMPLEMENTED / NOT_VERIFIED /
NOT_READY / HOLD / DENY / NOT_AUTHORIZED.**
