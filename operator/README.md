# PRAXIST Operator Adapter (contract v0.1)

This directory is a **portable operator implementation**. It does not import Hermes and does not require a specific agent SDK. Any front-end can call it.

## Commands

```bash
python operator/praxist_operator.py --operator hermes --operator-version 1.0 validate <task-project>
python operator/praxist_operator.py --operator hermes --operator-version 1.0 status <run-id> --task-project <task-project>
python operator/praxist_operator.py --operator hermes --operator-version 1.0 collect <run-id> --task-project <task-project> --out <evidence-dir>
python operator/praxist_operator.py --operator hermes --operator-version 1.0 run <task-project> --config operator-config.json
```

## What each command guarantees

- `validate` checks the task project, required files, evaluator location, protected surface, and hashes.
- `status` returns the contract status shape (state, generation, best metric, artifacts).
- `collect` copies run summaries, frontier, evaluation summaries and sessions into a standard evidence directory and writes `manifest.json`.
- `run` launches the existing `praxist.run` engine with an explicit provider/model config.

## C1 conformance

Run:

```bash
python operator/conformance.py \
  --task-project /path/to/task \
  --run-id run_id \
  --out conformance.json
```

It invokes the adapter under two operator identities and checks that:

- task/evaluator hashes match;
- status semantics match;
- evidence manifest contents and artifact hashes match;
- only the `operator` field differs.

On the BO transfer run `run_bo_hardened_v2_1`, C1 passed with 107 artifacts and zero content diffs.

## What this does not prove yet

- C2: launching a new run through the adapter with a second operator.
- C3: a genuinely different front-end agent producing the same evidence.
- C4: RSI boundary (candidate/evaluator separation, append-only promotion).

Those are the next gates. C1 only proves the adapter has a stable, agent-independent shape.

## Known portability warnings

`validate` warns on absolute/local path tokens such as `/tmp/` or `/home/` in `task.yaml`. The current experimental tasks still contain a runtime Python path; removing that is part of the next cleanup before C3.
