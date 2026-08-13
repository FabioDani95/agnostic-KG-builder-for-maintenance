"""Durable, fail-closed budget reservations for real LLM calls.

The ledger is intentionally independent from the OpenAI client.  A caller must
reserve the conservative cost envelope *before* invoking the API and finalize
the reservation afterwards.  An unfinished reservation keeps its complete
worst-case charge, including after a process crash.
"""

from __future__ import annotations

import fcntl
import json
import os
import threading
import uuid
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Callable, Iterator, Mapping

from backend.services.run_metrics import pricing_for_model

_SCHEMA_VERSION = 1
_MONEY_QUANTUM = Decimal("0.000000000001")


class BudgetLedgerError(RuntimeError):
    """Base class for budget-ledger failures."""


class BudgetExceededError(BudgetLedgerError):
    """Raised before an API call when its reservation would exceed the budget."""

    def __init__(
        self,
        *,
        budget_usd: Decimal,
        committed_usd: Decimal,
        active_reserved_usd: Decimal,
        requested_usd: Decimal,
    ) -> None:
        self.budget_usd = budget_usd
        self.committed_usd = committed_usd
        self.active_reserved_usd = active_reserved_usd
        self.requested_usd = requested_usd
        remaining = budget_usd - committed_usd - active_reserved_usd
        super().__init__(
            "Real-call budget exhausted before API invocation: "
            f"requested ${requested_usd}, remaining ${max(Decimal('0'), remaining)} "
            f"(budget ${budget_usd})."
        )


class BudgetConfigurationError(BudgetLedgerError):
    """Raised when an existing ledger is opened with a different budget."""


class LedgerCorruptionError(BudgetLedgerError):
    """Raised fail-closed when the durable event stream cannot be trusted."""


class DuplicateCallIdError(BudgetLedgerError):
    """Raised when a call id has already been reserved."""


class UnknownReservationError(BudgetLedgerError):
    """Raised when finalization references a missing reservation."""


def _as_decimal(value: Decimal | float | int | str, *, field: str) -> Decimal:
    try:
        parsed = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"{field} must be a finite non-negative number") from exc
    if not parsed.is_finite() or parsed < 0:
        raise ValueError(f"{field} must be a finite non-negative number")
    return parsed.quantize(_MONEY_QUANTUM)


def _money_json(value: Decimal) -> float:
    return float(value.quantize(_MONEY_QUANTUM))


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds")


def _nonempty_label(value: str, *, field: str, maximum: int = 512) -> str:
    label = str(value or "").strip()
    if not label:
        raise ValueError(f"{field} must be non-empty")
    if len(label) > maximum:
        raise ValueError(f"{field} exceeds {maximum} characters")
    return label


@dataclass(frozen=True)
class TokenEnvelope:
    """Upper token bounds used to price one call conservatively."""

    max_prompt_tokens: int
    max_completion_tokens: int

    def __post_init__(self) -> None:
        if int(self.max_prompt_tokens) < 0 or int(self.max_completion_tokens) < 0:
            raise ValueError("Token envelope values must be non-negative")

    def as_dict(self) -> dict[str, Any]:
        return {
            "max_prompt_tokens": int(self.max_prompt_tokens),
            "max_completion_tokens": int(self.max_completion_tokens),
            "cached_input_credit_assumed": False,
            "prompt_pricing_assumption": "all_prompt_tokens_are_cache_write",
        }


@dataclass(frozen=True)
class ActualTokenUsage:
    """Observed usage returned by a completed API call."""

    prompt_tokens: int
    completion_tokens: int
    cached_prompt_tokens: int = 0
    cache_write_prompt_tokens: int = 0

    def __post_init__(self) -> None:
        values = (
            self.prompt_tokens,
            self.completion_tokens,
            self.cached_prompt_tokens,
            self.cache_write_prompt_tokens,
        )
        if any(int(value) < 0 for value in values):
            raise ValueError("Actual token usage values must be non-negative")
        if int(self.cached_prompt_tokens) > int(self.prompt_tokens):
            raise ValueError("cached_prompt_tokens cannot exceed prompt_tokens")
        non_cached = int(self.prompt_tokens) - int(self.cached_prompt_tokens)
        if int(self.cache_write_prompt_tokens) > non_cached:
            raise ValueError(
                "cache_write_prompt_tokens cannot exceed non-cached prompt tokens"
            )

    def as_dict(self) -> dict[str, int]:
        return {
            "prompt_tokens": int(self.prompt_tokens),
            "completion_tokens": int(self.completion_tokens),
            "total_tokens": int(self.prompt_tokens) + int(self.completion_tokens),
            "cached_prompt_tokens": int(self.cached_prompt_tokens),
            "cache_write_prompt_tokens": int(self.cache_write_prompt_tokens),
        }


@dataclass(frozen=True)
class BudgetSnapshot:
    absolute_budget_usd: Decimal
    committed_usd: Decimal
    active_reserved_usd: Decimal
    remaining_usd: Decimal
    reservation_count: int
    finalized_count: int

    def as_dict(self) -> dict[str, Any]:
        return {
            "absolute_budget_usd": _money_json(self.absolute_budget_usd),
            "committed_usd": _money_json(self.committed_usd),
            "active_reserved_usd": _money_json(self.active_reserved_usd),
            "remaining_usd": _money_json(self.remaining_usd),
            "reservation_count": self.reservation_count,
            "finalized_count": self.finalized_count,
        }


@dataclass(frozen=True)
class CallFinalization:
    call_id: str
    status: str
    charged_cost_usd: Decimal
    actual_cost_usd: Decimal | None
    envelope_breached: bool


@dataclass(frozen=True)
class CallReservation:
    call_id: str
    worst_case_cost_usd: Decimal
    model: str
    reasoning_effort: str
    stage: str
    run_id: str
    pdf_id: str
    token_envelope: TokenEnvelope


EnvelopeCostEstimator = Callable[[TokenEnvelope, Mapping[str, Any]], Decimal | float | int]


def _apply_long_context_multipliers(
    *,
    prompt_tokens: int,
    pricing: Mapping[str, Any],
) -> tuple[Decimal, Decimal]:
    threshold = int(pricing.get("long_context_threshold_tokens", 0) or 0)
    is_long = threshold > 0 and int(prompt_tokens) > threshold
    input_multiplier = Decimal(
        str(pricing.get("long_context_input_multiplier", 1.0) or 1.0)
    ) if is_long else Decimal("1")
    output_multiplier = Decimal(
        str(pricing.get("long_context_output_multiplier", 1.0) or 1.0)
    ) if is_long else Decimal("1")
    return input_multiplier, output_multiplier


def conservative_envelope_cost_usd(
    envelope: TokenEnvelope,
    pricing: Mapping[str, Any],
) -> Decimal:
    """Price every possible prompt token as a cache write with no hit credit."""

    prompt = int(envelope.max_prompt_tokens)
    completion = int(envelope.max_completion_tokens)
    input_multiplier, output_multiplier = _apply_long_context_multipliers(
        prompt_tokens=prompt,
        pricing=pricing,
    )
    cache_write_rate = Decimal(str(pricing["input_per_million"])) * Decimal(
        str(pricing.get("cache_write_multiplier", 1.0) or 1.0)
    )
    output_rate = Decimal(str(pricing["output_per_million"]))
    cost = (
        Decimal(prompt) / Decimal(1_000_000) * cache_write_rate * input_multiplier
        + Decimal(completion) / Decimal(1_000_000) * output_rate * output_multiplier
    )
    return cost.quantize(_MONEY_QUANTUM)


def actual_usage_cost_usd(
    usage: ActualTokenUsage,
    pricing: Mapping[str, Any],
) -> Decimal:
    """Compute actual cost against the pricing snapshot captured at reservation."""

    prompt = int(usage.prompt_tokens)
    cached = int(usage.cached_prompt_tokens)
    cache_write = int(usage.cache_write_prompt_tokens)
    ordinary = max(0, prompt - cached - cache_write)
    input_multiplier, output_multiplier = _apply_long_context_multipliers(
        prompt_tokens=prompt,
        pricing=pricing,
    )
    input_rate = Decimal(str(pricing["input_per_million"]))
    cached_rate_raw = pricing.get("cached_input_per_million")
    cached_rate = input_rate if cached_rate_raw is None else Decimal(str(cached_rate_raw))
    cache_write_rate = input_rate * Decimal(
        str(pricing.get("cache_write_multiplier", 1.0) or 1.0)
    )
    output_rate = Decimal(str(pricing["output_per_million"]))
    cost = (
        (
            Decimal(ordinary) / Decimal(1_000_000) * input_rate
            + Decimal(cached) / Decimal(1_000_000) * cached_rate
            + Decimal(cache_write) / Decimal(1_000_000) * cache_write_rate
        )
        * input_multiplier
        + Decimal(int(usage.completion_tokens))
        / Decimal(1_000_000)
        * output_rate
        * output_multiplier
    )
    return cost.quantize(_MONEY_QUANTUM)


class ReservedCall:
    """Context wrapper that conservatively closes an unfinalized reservation."""

    def __init__(self, ledger: "RealCallBudgetLedger", reservation: CallReservation):
        self.ledger = ledger
        self.reservation = reservation
        self._finalization: CallFinalization | None = None
        self._mutex = threading.Lock()

    @property
    def call_id(self) -> str:
        return self.reservation.call_id

    @property
    def finalized(self) -> bool:
        return self._finalization is not None

    def finalize(
        self,
        *,
        status: str = "succeeded",
        usage: ActualTokenUsage | None = None,
        actual_cost_usd: Decimal | float | int | str | None = None,
    ) -> CallFinalization:
        with self._mutex:
            if self._finalization is None:
                self._finalization = self.ledger.finalize(
                    self.call_id,
                    status=status,
                    usage=usage,
                    actual_cost_usd=actual_cost_usd,
                    call_was_made=True,
                )
            return self._finalization

    def mark_not_called(self, *, status: str = "cancelled_before_call") -> CallFinalization:
        with self._mutex:
            if self._finalization is None:
                self._finalization = self.ledger.finalize(
                    self.call_id,
                    status=status,
                    call_was_made=False,
                )
            return self._finalization

    def __enter__(self) -> "ReservedCall":
        return self

    def __exit__(self, exc_type: Any, exc: Any, traceback: Any) -> bool:
        del exc, traceback
        if not self.finalized:
            # Once the context is entered we cannot prove that the remote API
            # was not invoked.  Unknown usage therefore retains the full bound.
            status = "failed_unknown_cost" if exc_type is not None else "completed_unknown_cost"
            self.finalize(status=status)
        return False


class RealCallBudgetLedger:
    """Append-only JSONL ledger with process-safe, atomic budget reservations."""

    def __init__(
        self,
        path: str | Path,
        *,
        absolute_budget_usd: Decimal | float | int | str,
        envelope_cost_estimator: EnvelopeCostEstimator = conservative_envelope_cost_usd,
        clock: Callable[[], str] = _utc_now,
    ) -> None:
        self.path = Path(path).expanduser().resolve()
        self.lock_path = self.path.with_name(f"{self.path.name}.lock")
        self.absolute_budget_usd = _as_decimal(
            absolute_budget_usd,
            field="absolute_budget_usd",
        )
        if self.absolute_budget_usd <= 0:
            raise ValueError("absolute_budget_usd must be positive")
        self._envelope_cost_estimator = envelope_cost_estimator
        self._clock = clock
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    @contextmanager
    def _exclusive_lock(self) -> Iterator[None]:
        descriptor = os.open(self.lock_path, os.O_RDWR | os.O_CREAT, 0o600)
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX)
            yield
        finally:
            fcntl.flock(descriptor, fcntl.LOCK_UN)
            os.close(descriptor)

    def _initialize(self) -> None:
        with self._exclusive_lock():
            events = self._read_events_unlocked()
            if not events:
                self._append_event_unlocked({
                    "schema_version": _SCHEMA_VERSION,
                    "event": "ledger_initialized",
                    "timestamp": self._clock(),
                    "absolute_budget_usd": _money_json(self.absolute_budget_usd),
                    "accounting_policy": "finalized_actual_plus_unfinished_worst_case",
                })
                return
            stored = self._authorized_budget(events)
            if stored != self.absolute_budget_usd:
                raise BudgetConfigurationError(
                    "Existing real-call ledger has absolute budget "
                    f"${stored}, not requested ${self.absolute_budget_usd}"
                )
            self._build_state(events)

    @staticmethod
    def _authorized_budget(events: list[dict[str, Any]]) -> Decimal:
        """Validate and return the latest append-only operator authorization."""

        if not events or events[0].get("event") != "ledger_initialized":
            raise LedgerCorruptionError("Ledger is missing its initialization event")
        authorized = _as_decimal(
            events[0].get("absolute_budget_usd"),
            field="stored absolute_budget_usd",
        )
        for index, event in enumerate(events[1:], start=2):
            if event.get("event") != "budget_increased":
                continue
            previous = _as_decimal(
                event.get("previous_absolute_budget_usd"),
                field=f"previous_absolute_budget_usd at event {index}",
            )
            increased = _as_decimal(
                event.get("absolute_budget_usd"),
                field=f"absolute_budget_usd at event {index}",
            )
            if previous != authorized or increased <= authorized:
                raise LedgerCorruptionError(
                    f"Invalid budget increase at event {index}"
                )
            authorized = increased
        return authorized

    def increase_budget(
        self,
        new_absolute_budget_usd: Decimal | float | int | str,
        *,
        authorization_note: str,
    ) -> "RealCallBudgetLedger":
        """Append a monotonic budget authorization without rewriting history."""

        increased = _as_decimal(
            new_absolute_budget_usd,
            field="new_absolute_budget_usd",
        )
        note = _nonempty_label(
            authorization_note,
            field="authorization_note",
            maximum=1000,
        )
        if increased <= self.absolute_budget_usd:
            raise ValueError("new_absolute_budget_usd must increase the current budget")
        with self._exclusive_lock():
            events = self._read_events_unlocked()
            authorized = self._authorized_budget(events)
            if authorized != self.absolute_budget_usd:
                raise BudgetConfigurationError(
                    "Ledger authorization changed before this increase was appended"
                )
            self._build_state(events)
            self._append_event_unlocked({
                "schema_version": _SCHEMA_VERSION,
                "event": "budget_increased",
                "timestamp": self._clock(),
                "previous_absolute_budget_usd": _money_json(authorized),
                "absolute_budget_usd": _money_json(increased),
                "authorization_note": note,
            })
        return RealCallBudgetLedger(
            self.path,
            absolute_budget_usd=increased,
            envelope_cost_estimator=self._envelope_cost_estimator,
            clock=self._clock,
        )

    def _read_events_unlocked(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        events: list[dict[str, Any]] = []
        with self.path.open("rb") as stream:
            for line_number, raw_line in enumerate(stream, start=1):
                if not raw_line.strip():
                    continue
                try:
                    event = json.loads(raw_line)
                except (json.JSONDecodeError, UnicodeDecodeError) as exc:
                    # Ignoring a torn reservation could permit an overspend.
                    raise LedgerCorruptionError(
                        f"Invalid JSONL event at line {line_number}; refusing new calls"
                    ) from exc
                if not isinstance(event, dict):
                    raise LedgerCorruptionError(
                        f"Ledger event at line {line_number} is not an object"
                    )
                events.append(event)
        return events

    def _append_event_unlocked(self, event: Mapping[str, Any]) -> None:
        existed = self.path.exists()
        payload = (
            json.dumps(dict(event), sort_keys=True, separators=(",", ":")) + "\n"
        ).encode("utf-8")
        descriptor = os.open(
            self.path,
            os.O_WRONLY | os.O_CREAT | os.O_APPEND,
            0o600,
        )
        try:
            written = 0
            while written < len(payload):
                written += os.write(descriptor, payload[written:])
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
        if not existed:
            directory_descriptor = os.open(self.path.parent, os.O_RDONLY)
            try:
                os.fsync(directory_descriptor)
            finally:
                os.close(directory_descriptor)

    def _build_state(self, events: list[dict[str, Any]]) -> dict[str, Any]:
        reservations: dict[str, dict[str, Any]] = {}
        finalizations: dict[str, dict[str, Any]] = {}
        for index, event in enumerate(events):
            if int(event.get("schema_version", -1)) != _SCHEMA_VERSION:
                raise LedgerCorruptionError(f"Unsupported schema at event {index + 1}")
            event_type = event.get("event")
            if index == 0 and event_type == "ledger_initialized":
                continue
            if event_type == "budget_increased":
                continue
            call_id = str(event.get("call_id") or "")
            if not call_id:
                raise LedgerCorruptionError(f"Missing call_id at event {index + 1}")
            if event_type == "call_reserved":
                if call_id in reservations:
                    raise LedgerCorruptionError(f"Duplicate reservation for {call_id}")
                reservations[call_id] = event
            elif event_type == "call_finalized":
                if call_id not in reservations:
                    raise LedgerCorruptionError(f"Finalization precedes reservation for {call_id}")
                if call_id in finalizations:
                    raise LedgerCorruptionError(f"Duplicate finalization for {call_id}")
                finalizations[call_id] = event
            else:
                raise LedgerCorruptionError(f"Unknown ledger event {event_type!r}")

        committed = sum(
            (
                _as_decimal(event["charged_cost_usd"], field="charged_cost_usd")
                for event in finalizations.values()
            ),
            Decimal("0"),
        )
        active = sum(
            (
                _as_decimal(event["worst_case_cost_usd"], field="worst_case_cost_usd")
                for call_id, event in reservations.items()
                if call_id not in finalizations
            ),
            Decimal("0"),
        )
        return {
            "reservations": reservations,
            "finalizations": finalizations,
            "committed_usd": committed.quantize(_MONEY_QUANTUM),
            "active_reserved_usd": active.quantize(_MONEY_QUANTUM),
        }

    def snapshot(self) -> BudgetSnapshot:
        with self._exclusive_lock():
            state = self._build_state(self._read_events_unlocked())
            return self._snapshot_from_state(state)

    def _snapshot_from_state(self, state: Mapping[str, Any]) -> BudgetSnapshot:
        committed = state["committed_usd"]
        active = state["active_reserved_usd"]
        remaining = max(Decimal("0"), self.absolute_budget_usd - committed - active)
        return BudgetSnapshot(
            absolute_budget_usd=self.absolute_budget_usd,
            committed_usd=committed,
            active_reserved_usd=active,
            remaining_usd=remaining.quantize(_MONEY_QUANTUM),
            reservation_count=len(state["reservations"]),
            finalized_count=len(state["finalizations"]),
        )

    def reserve(
        self,
        *,
        stage: str,
        run_id: str,
        pdf_id: str,
        model: str,
        reasoning_effort: str,
        token_envelope: TokenEnvelope,
        call_id: str | None = None,
        worst_case_cost_usd: Decimal | float | int | str | None = None,
    ) -> CallReservation:
        stage = _nonempty_label(stage, field="stage")
        run_id = _nonempty_label(run_id, field="run_id")
        pdf_id = _nonempty_label(pdf_id, field="pdf_id")
        model = _nonempty_label(model, field="model")
        reasoning_effort = _nonempty_label(reasoning_effort, field="reasoning_effort")
        resolved_call_id = _nonempty_label(
            call_id or str(uuid.uuid4()),
            field="call_id",
            maximum=128,
        )
        pricing = pricing_for_model(model)
        if worst_case_cost_usd is None:
            calculated = self._envelope_cost_estimator(token_envelope, pricing)
            worst_case = _as_decimal(calculated, field="calculated worst_case_cost_usd")
            cost_basis = "token_envelope_pricing_snapshot"
        else:
            worst_case = _as_decimal(
                worst_case_cost_usd,
                field="worst_case_cost_usd",
            )
            cost_basis = "caller_supplied_conservative_envelope"

        with self._exclusive_lock():
            events = self._read_events_unlocked()
            state = self._build_state(events)
            if resolved_call_id in state["reservations"]:
                raise DuplicateCallIdError(f"Call id already reserved: {resolved_call_id}")
            projected = state["committed_usd"] + state["active_reserved_usd"] + worst_case
            if projected > self.absolute_budget_usd:
                raise BudgetExceededError(
                    budget_usd=self.absolute_budget_usd,
                    committed_usd=state["committed_usd"],
                    active_reserved_usd=state["active_reserved_usd"],
                    requested_usd=worst_case,
                )
            event = {
                "schema_version": _SCHEMA_VERSION,
                "event": "call_reserved",
                "timestamp": self._clock(),
                "call_id": resolved_call_id,
                "stage": stage,
                "run_id": run_id,
                "pdf_id": pdf_id,
                "model": model,
                "reasoning_effort": reasoning_effort,
                "token_envelope": token_envelope.as_dict(),
                "pricing_snapshot": pricing,
                "cost_basis": cost_basis,
                "worst_case_cost_usd": _money_json(worst_case),
                "committed_before_usd": _money_json(state["committed_usd"]),
                "active_reserved_before_usd": _money_json(state["active_reserved_usd"]),
                "absolute_budget_usd": _money_json(self.absolute_budget_usd),
            }
            # This durable append and fsync complete before the reservation is
            # returned, so the caller cannot issue an unaccounted API request.
            self._append_event_unlocked(event)

        return CallReservation(
            call_id=resolved_call_id,
            worst_case_cost_usd=worst_case,
            model=model,
            reasoning_effort=reasoning_effort,
            stage=stage,
            run_id=run_id,
            pdf_id=pdf_id,
            token_envelope=token_envelope,
        )

    def call(self, **reservation_kwargs: Any) -> ReservedCall:
        """Reserve immediately and return a context/finalization wrapper."""

        return ReservedCall(self, self.reserve(**reservation_kwargs))

    def finalize(
        self,
        call_id: str,
        *,
        status: str,
        usage: ActualTokenUsage | None = None,
        actual_cost_usd: Decimal | float | int | str | None = None,
        call_was_made: bool = True,
    ) -> CallFinalization:
        resolved_call_id = _nonempty_label(call_id, field="call_id", maximum=128)
        status = _nonempty_label(status, field="status", maximum=128)
        if not call_was_made and usage is not None:
            raise ValueError("A call that was not made cannot have token usage")
        if not call_was_made and actual_cost_usd is not None:
            parsed = _as_decimal(actual_cost_usd, field="actual_cost_usd")
            if parsed != 0:
                raise ValueError("A call that was not made must have zero actual cost")

        with self._exclusive_lock():
            events = self._read_events_unlocked()
            state = self._build_state(events)
            reservation = state["reservations"].get(resolved_call_id)
            if reservation is None:
                raise UnknownReservationError(
                    f"No reservation exists for call id {resolved_call_id}"
                )
            existing = state["finalizations"].get(resolved_call_id)
            if existing is not None:
                return self._finalization_from_event(existing)

            worst_case = _as_decimal(
                reservation["worst_case_cost_usd"],
                field="worst_case_cost_usd",
            )
            observed_cost: Decimal | None
            cost_basis: str
            if not call_was_made:
                observed_cost = Decimal("0").quantize(_MONEY_QUANTUM)
                charged = observed_cost
                cost_basis = "not_called"
            elif actual_cost_usd is not None:
                observed_cost = _as_decimal(actual_cost_usd, field="actual_cost_usd")
                charged = observed_cost
                cost_basis = "caller_supplied_actual"
            elif usage is not None:
                observed_cost = actual_usage_cost_usd(
                    usage,
                    reservation["pricing_snapshot"],
                )
                charged = observed_cost
                cost_basis = "actual_usage_pricing_snapshot"
            else:
                # A network error or process-level ambiguity can still incur a
                # remote charge.  Do not release money without observed usage.
                observed_cost = None
                charged = worst_case
                cost_basis = "unknown_usage_retains_worst_case"

            envelope_breached = charged > worst_case
            event = {
                "schema_version": _SCHEMA_VERSION,
                "event": "call_finalized",
                "timestamp": self._clock(),
                "call_id": resolved_call_id,
                "status": status,
                "call_was_made": bool(call_was_made),
                "actual_usage": usage.as_dict() if usage is not None else None,
                "actual_cost_usd": (
                    _money_json(observed_cost) if observed_cost is not None else None
                ),
                "charged_cost_usd": _money_json(charged),
                "reserved_worst_case_cost_usd": _money_json(worst_case),
                "cost_basis": cost_basis,
                "envelope_breached": envelope_breached,
            }
            self._append_event_unlocked(event)
            return self._finalization_from_event(event)

    def _finalization_from_event(self, event: Mapping[str, Any]) -> CallFinalization:
        actual = event.get("actual_cost_usd")
        return CallFinalization(
            call_id=str(event["call_id"]),
            status=str(event["status"]),
            charged_cost_usd=_as_decimal(
                event["charged_cost_usd"],
                field="charged_cost_usd",
            ),
            actual_cost_usd=(
                _as_decimal(actual, field="actual_cost_usd")
                if actual is not None
                else None
            ),
            envelope_breached=bool(event.get("envelope_breached", False)),
        )

    def events(self) -> list[dict[str, Any]]:
        """Return a defensive copy suitable for campaign reporting."""

        with self._exclusive_lock():
            return json.loads(json.dumps(self._read_events_unlocked()))
