"""Smoke test for the fork's cost patch: no network, no LLM, no run."""

import json
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, "/mnt/c/Users/andyl/Projects/PRAXIST-desktop-engine")

from praxist.core.ledgers import BudgetLedger

with tempfile.TemporaryDirectory() as tmp:
    os.environ["PRAXIST_PRICE_USD_PER_MTOK"] = "0.28"
    ledger = BudgetLedger(Path(tmp), "run_test")
    record = ledger.append_usage(
        request_id=None,
        grant_id=None,
        actor_ref="agent:test",
        stage_id="stage:test",
        action_type="usage",
        actual_usage={"tokens": 2_000_000.0},
        reason="smoke",
    )
    print(json.dumps({k: record.get(k) for k in ("cost_usd", "cost_basis", "actual_usage")}))
    assert record["cost_usd"] == 0.56, record
    os.environ.pop("PRAXIST_PRICE_USD_PER_MTOK")
    record2 = ledger.append_usage(
        request_id=None,
        grant_id=None,
        actor_ref="agent:test",
        stage_id="stage:test",
        action_type="usage",
        actual_usage={"tokens": 1_000_000.0},
        reason="smoke",
    )
    assert "cost_usd" not in record2, record2
    print("OK price-off omits cost")
