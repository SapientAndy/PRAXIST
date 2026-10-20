"""Smoke test for inferred lineage: same variant in a later generation."""

import json
import os
import sys
import tempfile

sys.path.insert(0, "/mnt/c/Users/andyl/Projects/PRAXIST-desktop-engine")

with tempfile.TemporaryDirectory() as tmp:
    os.environ["LOCAL_STORE_DIR"] = tmp
    from praxist.plugins.workflow_stages.research_loop.backend.tools import local_store as ls

    ls.init_db()
    first = {
        "id": "find-gen0",
        "finding_type": "result",
        "title": "first",
        "content": "",
        "metrics": {},
        "variant_name": "gen0_peer1_merge_sort",
        "notes": "",
        "peer_id": "gen0_peer0",
        "generation_id": 0,
        "timestamp": "2026-01-01T00:00:00",
    }
    second = dict(first, id="find-gen1", generation_id=1, title="retry", variant_name="gen1_peer0_merge_sort_v2")
    ls.insert_finding(first)
    ls.insert_finding(second)

    ids = ls.earlier_findings_for_variant("gen1_peer0_merge_sort", 1)
    print(json.dumps(ids))
    assert ids == ["find-gen0"], ids
    assert ls.earlier_findings_for_variant("gen1_peer0_merge_sort", 0) == []
    assert ls.normalize_variant_name("gen3_peer12_merge_sort_v4") == "merge_sort"
    print("OK lineage inference")
