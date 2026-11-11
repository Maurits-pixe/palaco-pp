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
