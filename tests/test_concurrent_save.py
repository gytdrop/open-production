"""Concurrent save safety: per-instance RLock guards ProductionService.save.

ProductionService.save() and load() now hold the same per-instance RLock,
so writes serialize cleanly within one Python process. load()-modify-save
sequences that span more than one call must use ProductionService.transaction()
to hold the lock across the whole check-then-act operation.
"""
from __future__ import annotations

import concurrent.futures
import threading
from dataclasses import replace
from pathlib import Path

import pytest

from src.schema.production_document import (
    AuditEntry, IntentDocument, utc_now_iso,
)
from src.service.production_service import ProductionService


@pytest.fixture
def svc(tmp_path: Path) -> ProductionService:
    return ProductionService(storage_dir=tmp_path)


def _audit_entry(i: int) -> AuditEntry:
    return AuditEntry(
        id="evt_conc" + str(i).zfill(10),
        ts=utc_now_iso(),
        actor="concurrent_test",
        action_type="comment",
        payload={"i": i},
    )


def test_concurrent_saves_dont_lose_updates(svc: ProductionService):
    """8 threads x 25 saves each through transaction() must not lose any updates."""
    prod = svc.init("concurrency", intent=IntentDocument(topic="X"))
    prod_id = prod.id

    def save_iter(i: int) -> int:
        with svc.transaction():
            p = svc.load(prod_id)
            p2 = replace(p, audit_trail=p.audit_trail + [_audit_entry(i)])
            svc.save(p2)
            return i

    N_THREADS, N_ITERS = 8, 25
    total = N_THREADS * N_ITERS
    with concurrent.futures.ThreadPoolExecutor(max_workers=N_THREADS) as ex:
        futs = [ex.submit(save_iter, i) for i in range(total)]
        results = [f.result(timeout=30) for f in futs]
    assert len(results) == total

    final = svc.load(prod_id)
    # svc.init() added 1 audit_trail entry, so total includes it.
    assert len(final.audit_trail) == total + 1, (
        f"expected {0} entries, got {1}".format(total + 1, len(final.audit_trail))
    )
    ids = [e.id for e in final.audit_trail]
    assert len(set(ids)) == total + 1, "duplicate ids present"


def test_save_with_concurrent_status_reads(svc: ProductionService):
    """save() + status() interleaved from many threads must not raise."""
    prod = svc.init("mixed", intent=IntentDocument(topic="X"))
    prod_id = prod.id
    errors = []

    def save_loop(i: int) -> None:
        for j in range(15):
            try:
                with svc.transaction():
                    p = svc.load(prod_id)
                    p2 = replace(p, audit_trail=p.audit_trail + [_audit_entry(i * 100 + j)])
                    svc.save(p2)
            except Exception as exc:
                errors.append("save: " + str(exc))

    def status_loop() -> None:
        for _ in range(50):
            try:
                svc.status(prod_id)
            except Exception as exc:
                errors.append("status: " + str(exc))

    threads = []
    for i in range(4):
        threads.append(threading.Thread(target=save_loop, args=(i,)))
    threads.append(threading.Thread(target=status_loop))
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert errors == [], errors[:3]

    final = svc.load(prod_id)
    # 1 init + 4 threads x 15 saves each = 61 entries
    assert len(final.audit_trail) == 1 + 4 * 15


def test_save_serializes_without_transaction(svc: ProductionService):
    """Bare save() from many threads (no read) must all succeed."""
    prod = svc.init("write_only", intent=IntentDocument(topic="X"))
    prod_id = prod.id

    def write_only(i: int) -> int:
        p = svc.load(prod_id)  # 1 read
        # no transaction: each thread sees the latest state (already-locked load is fine)
        # but the modify must be lock-free - just append a fresh audit entry from a
        # stand-alone Production snapshot
        p2 = replace(p, audit_trail=p.audit_trail + [_audit_entry(i)])
        svc.save(p2)  # locked
        return i

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
        futs = [ex.submit(write_only, i) for i in range(40)]
        for f in futs:
            f.result(timeout=30)

    # Note: this test is intentionally lossy - some saves will overwrite earlier
    # ones because each thread reads the latest state before saving. The point is
    # no save() ever raises (no PermissionError, no hash mismatch).
    final = svc.load(prod_id)
    assert len(final.audit_trail) >= 1  # init always present; concurrent saves may overwrite

