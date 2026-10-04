"""Optional local source regressions; no extraction-quality claims or API calls."""

from pathlib import Path

import pytest

from backend.kg_v3.reader import read_document
from scripts.kg_v3 import info_asset, load_evidence

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize(
    "manual,segment,sha,phrases",
    [
        (
            "grizzly_g0872",
            "p51.t1.r2",
            "8f3ecaa3b86876d84a6e8b4781fae3d897f1af50d2356737f06b16451a9ec237",
            ["Inspect/replace if at fault", "Emergency stop button", "Page 63"],
        ),
        (
            "lg_lmh2235st",
            "p30.t1.r3",
            "d6fba682b650586d7959f85f8ce1eb1788a55c40f895b067424bdd2890105c32",
            ["Normal: Less than 1 ohm", "Normal: Infinite", "MAGNETRON"],
        ),
        (
            "lincoln_powermig_215mp",
            "p29.t1.r3",
            "0d981135554379c9175510bf670559c50ee9f66db8419aa9d4341ddaf8bba133",
            ["problem persists", "Contact your local Lincoln", "Check for correct input voltage"],
        ),
    ],
)
def test_t03_t07_t08_real_locators_preserve_printed_context(manual, segment, sha, phrases):
    folder = ROOT / "campaign" / manual
    if not (folder / "manual.pdf").exists():
        pytest.skip("optional local corpus unavailable; synthetic acceptance fixtures remain mandatory")
    evidence, count, actual = load_evidence(folder / "manual.pdf", info_asset(folder / "info.yaml"))
    assert actual == sha
    doc = read_document(list(evidence), page_count=count)
    row = doc.segment(segment)
    assert row.bbox and row.table
    assert all(text in row.text for text in phrases)
