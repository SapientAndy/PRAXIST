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

C2 also passed: `praxist_bo_c2` (1 peer × 1 generation, task project without
absolute paths) was launched through this adapter, reached best metric
`1.874299`, and produced 24 evidence artifacts.

C3 also passed: the independent Node.js client (`node_operator.js`) launched
`run_c3_1`, reached best metric `1.881592`, and produced 22 evidence artifacts
with the same hashes as the Python adapter.

## Credentials

`run` accepts an optional `env_file` in the operator config. It loads
`KEY=VALUE` pairs into the subprocess environment and never writes them to
status or evidence.

## What this does not prove yet

- C4: RSI boundary with a multi-module candidate, held-out evaluation, and
  promotion evidence.

C1/C2/C3 prove two independent operator implementations agree on task hashes,
status semantics, and evidence. They do not prove cross-machine or cross-provider
losslessness.

## Known portability warnings

`validate` warns on absolute/local path tokens such as `/tmp/` or `/home/` in `task.yaml`. The current experimental tasks still contain a runtime Python path; removing that is part of the next cleanup before C3.
