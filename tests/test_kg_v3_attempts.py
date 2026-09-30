"""A resumed run reports the time and the model usage of all its attempts."""

from __future__ import annotations

from scripts.kg_v3 import with_earlier_attempts


def test_a_first_run_is_one_attempt():
    report = {"seconds": {"extract": 60.0}, "usage": {"calls": 9, "estimated_cost_usd": 0.07}}
    assert with_earlier_attempts(report, None) == {**report, "attempts": 1}


def test_a_resume_adds_its_time_and_usage_to_the_earlier_attempts():
    earlier = {"attempts": 1, "seconds": {"pdf_read": 7.3, "extract": 61.4, "end_to_end": 152.2, "map": 21.7},
               "usage": {"calls": 30, "prompt_tokens": 1000, "completion_tokens": 200, "estimated_cost_usd": 0.1,
                         "by_operation": {"extract": 10}},
               "agent_usage": {"calls": 4, "estimated_cost_usd": 0.01}}
    resume = {"status": "approved", "seconds": {"pdf_read": 7.6, "extract": 0.07, "end_to_end": 14.0},
              "usage": {"calls": 0, "prompt_tokens": 0, "completion_tokens": 0, "estimated_cost_usd": 0.0,
                        "by_operation": {}}}
    merged = with_earlier_attempts(resume, earlier)
    assert merged["status"] == "approved" and merged["attempts"] == 2
    assert merged["seconds"] == {"pdf_read": 14.9, "extract": 61.47, "end_to_end": 166.2, "map": 21.7}
    assert merged["usage"]["calls"] == 30 and merged["usage"]["estimated_cost_usd"] == 0.1
    assert merged["usage"]["by_operation"] == {"extract": 10}
    assert merged["agent_usage"]["estimated_cost_usd"] == 0.01
