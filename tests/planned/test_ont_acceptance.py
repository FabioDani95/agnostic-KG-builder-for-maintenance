from __future__ import annotations

from pathlib import Path

import pytest

from backend.services.ontology_schema_service import (
    APPROVED_ONTOLOGY_SHA256,
    ontology_contract,
)


def test_ac_ont_001(tmp_path):
    contract = ontology_contract()
    assert contract.sha256 == APPROVED_ONTOLOGY_SHA256
    assert contract.path.name == "ontology_schema.JSON"

    mutated = tmp_path / "ontology_schema.JSON"
    mutated.write_bytes(Path(contract.path).read_bytes() + b"\n")
    with pytest.raises(RuntimeError, match="checksum mismatch"):
        ontology_contract(mutated)

