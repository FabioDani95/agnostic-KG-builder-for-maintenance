"""Campaign annotation sheet: what the annotator writes becomes gold claims, mistakes are reported."""

from __future__ import annotations

from scripts.campaign import BRANCH, pages_from, parse_sheet

SHEET = """# Annotazione
Annotatore: Fabio Daniele
Data: 2026-09-28
Tempo impiegato (minuti): 40
Pagine annotate (tutte le pagine diagnostiche, per esempio 45-52, 60): 11, 12–13

## Istruzioni

## Rami

### Ramo R1
- problema: Pump fails to operate | ID: p11.t1.r2
- codice:
- causa: Restricted air supply | ID: p11.t1.r2
- azione: Clear the air line | tipo: riparazione | ID: p11.t1.r2
- azione: Check the regulator | tipo: controllo | ID: p11.t1.r2, p11.b6
- componente:  | ID:
- condizioni:
- nota:

### Ramo R2
- problema: Alarm 7, low oil | ID: p12.b3
- codice: 7
- causa: non indicata nel manuale | ID:
- azione: Call service | ID: p12.x
- componente:  | ID:
- condizioni:
- nota:
"""


def test_page_ranges_accept_dashes_and_lists():
    assert pages_from("11, 12–13") == [11, 12, 13]


def test_the_sheet_becomes_one_claim_per_action():
    gold, problems = parse_sheet(SHEET)
    assert gold["annotator"] == "Fabio Daniele" and gold["pages"] == [11, 12, 13] and gold["branches"] == 2
    first = [claim for claim in gold["claims"] if claim["branch_id"] == "R1"]
    assert [(claim["claim_id"], claim["action_kind"]) for claim in first] == [("R1.1", "repair"), ("R1.2", "inspection")]
    unnamed = next(claim for claim in gold["claims"] if claim["branch_id"] == "R2")
    assert unnamed["failure"] == "" and not unnamed["failure_stated"] and unnamed["code"] == "7"
    assert any("p12.x" in item for item in problems) and any("needs tipo" in item for item in problems)


def test_an_empty_template_is_not_a_branch():
    gold, problems = parse_sheet("Pagine annotate: \n## Istruzioni\n## Rami\n" + BRANCH)
    assert gold["claims"] == [] and problems == ["write the annotated pages at the top"]
