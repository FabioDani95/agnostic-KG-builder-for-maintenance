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


def test_run_ledger_label_is_explicit_and_status_surrounds_each_run(tmp_path, monkeypatch):
    from types import SimpleNamespace

    from scripts import campaign

    manual = tmp_path / "manual"
    (manual / "gold").mkdir(parents=True)
    (manual / "gold/gold.json").write_text('{}')
    events = []
    monkeypatch.setattr(campaign, 'folder', lambda _: manual)
    monkeypatch.setattr(campaign, 'info', lambda _: {})
    monkeypatch.setattr(campaign, 'cmd_status', lambda _: events.append('status'))
    monkeypatch.setattr(campaign.subprocess, 'run', lambda args, **kwargs: events.append(args))
    campaign.cmd_run(SimpleNamespace(id='manual', without_gold=False, reps=1, budget='10',
                                    spend_ceiling='6.317599975', run_prefix='campaign_E'))
    assert events[0] == events[2] == 'status'
    assert events[1][events[1].index('--run-id')+1] == 'campaign_E_manual_v3_r1'
    assert events[1][-2:] == ['--spend-ceiling', '6.317599975']


def test_header_fields_may_be_list_items():
    from scripts.campaign import parse_sheet

    sheet = ("# Annotazione\n\n- Annotatore: Fabio\n- Data: 2026-09-28\n- Tempo impiegato (minuti): 150\n"
             "- Pagine annotate: 9, 26–27, 51\n\n## Rami\n\n### Ramo R1\n"
             "- problema: Machine does not start. | ID: p51.t1.r2\n- causa: Fuse blown. | ID: p51.t1.r2\n"
             "- azione: Replace the fuse. | tipo: riparazione | ID: p51.t1.r2\n")
    gold, problems = parse_sheet(sheet)
    assert gold["annotator"] == "Fabio" and gold["pages"] == [9, 26, 27, 51] and gold["minutes"] == "150"
    assert problems == []
