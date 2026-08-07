from __future__ import annotations

import asyncio

import pytest

from backend.services.ontology_workflow import _run_chunk_with_retry


def test_transient_chunk_failure_retries_only_that_operation():
    calls = []

    def operation():
        calls.append(len(calls) + 1)
        if len(calls) == 1:
            raise RuntimeError("Ontology draft failed before completion: Connection error.")
        return "completed"

    result = asyncio.run(
        _run_chunk_with_retry(operation, attempts=3, base_delay_seconds=0),
    )

    assert result == "completed"
    assert calls == [1, 2]


def test_non_transient_chunk_failure_is_not_retried():
    calls = []

    def operation():
        calls.append(len(calls) + 1)
        raise RuntimeError("Ontology payload violates the approved schema")

    with pytest.raises(RuntimeError, match="approved schema"):
        asyncio.run(
            _run_chunk_with_retry(operation, attempts=3, base_delay_seconds=0),
        )

    assert calls == [1]
