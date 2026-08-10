"""Provider-free regression model for the root/mailbox dispatch contract."""
from __future__ import annotations

from dataclasses import dataclass


def valid_packet(packet: str) -> bool:
    lines = packet.splitlines()
    return bool(lines) and lines[0] == "TASK"


def valid_role(role: str, allowed: set[str]) -> bool:
    return bool(role) and role in allowed


@dataclass
class FixtureTransaction:
    role: str
    task_name: str
    receipt: str
    expires_at: int = 100
    prepared: bool = True
    spawned: bool = False
    receipt_status: str = "not_found"

    def ready(self, spawn_role: str, fork_turns: str, now: int = 1) -> str:
        if not self.prepared:
            return "REFUSED_UNPREPARED"
        if now > self.expires_at:
            self.prepared = False
            return "REFUSED_EXPIRED"
        if spawn_role != self.role:
            return "REFUSED_ROLE_MISMATCH"
        if fork_turns != "none":
            return "REFUSED_PHYSICAL_THREAD_CONTRACT"
        return "READY_TO_SPAWN"

    def spawn_failed(self) -> None:
        self.prepared = False

    def spawn_accepted(self) -> None:
        self.spawned = True
        self.prepared = False

    def verify(self) -> str:
        if not self.spawned or self.receipt_status != "hook_emitted":
            return "TRANSPORT_FAILURE"
        return "DISPATCHED"


def main() -> None:
    allowed = {"deepseek_auditor", "deepseek_coder", "deepseek_worker"}
    assert valid_packet("TASK\n\nOBJECTIVE\nfixture")
    queue: list[str] = []
    for invalid in ("TASK: fixture", " TASK\n", "metadata\nTASK\n", "\ufeffTASK\n"):
        assert not valid_packet(invalid)
        assert queue == []
    assert not valid_role("", allowed)
    assert not valid_role("arbitrary_role", allowed)

    # No PREPARE means no supported spawn.
    missing = FixtureTransaction("deepseek_auditor", "missing", "fixture-0", prepared=False)
    assert missing.ready("deepseek_auditor", "none") == "REFUSED_UNPREPARED"

    transaction = FixtureTransaction("deepseek_auditor", "fixture_dispatch", "fixture-1")
    assert transaction.ready("deepseek_coder", "none") == "REFUSED_ROLE_MISMATCH"
    assert transaction.ready("deepseek_auditor", "all") == "REFUSED_PHYSICAL_THREAD_CONTRACT"
    assert transaction.ready("deepseek_auditor", "none") == "READY_TO_SPAWN"
    transaction.spawn_accepted()
    assert transaction.verify() == "TRANSPORT_FAILURE"
    transaction.receipt_status = "hook_emitted"
    assert transaction.verify() == "DISPATCHED"

    failed = FixtureTransaction("deepseek_coder", "spawn_failure", "fixture-2")
    assert failed.ready("deepseek_coder", "none") == "READY_TO_SPAWN"
    failed.spawn_failed()
    assert not failed.prepared

    expired = FixtureTransaction("deepseek_worker", "expired", "fixture-3", expires_at=1)
    assert expired.ready("deepseek_worker", "none", now=2) == "REFUSED_EXPIRED"
    assert not expired.prepared

    remaining = [item for item in (missing, transaction, failed, expired) if item.prepared]
    assert remaining == []
    print("EXTERNAL WORKER TRANSPORT CONTRACT PASS: strict TASK grammar, prepare gate, exact role, fresh child, hook receipt, compensation, expiry, queue zero")


if __name__ == "__main__":
    main()
