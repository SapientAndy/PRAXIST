# Promotion review — redaction candidates

Status: **not approved**. This file records an external audit that is stricter
than the current 23-case sealed evaluator.

## Gen 0 — `gen0_peer1_lineprefilter_v2`

- sealed score: 6.999577
- sealed correctness: 23/23
- status: proposed

## Gen 1 — `gen1_peer0_marker_dispatch_v2`

- sealed score: 12.132611
- sealed correctness: 23/23
- status: proposed

## Safe tradeoff — `gen1_peer1_span_slice`

- sealed score: 5.209935
- sealed correctness: 23/23
- external differential fuzz: **0 output mismatches, 0 hit mismatches in 1,200 cases**
- status: proposed; recommended for human approval as the safer parent

This candidate is slower than the rejected 12.13x candidate, but it preserves
the full redaction behavior on the cross-line and duplicate-secret cases that
the fast candidate fails. It is the candidate the promotion gate should prefer
until the sealed evaluator is hardened.

## Differential audit

A separate external fuzz check compared the gen-1 candidate against the pristine
module on 1,200 generated strings, including cross-line markers, duplicate
secrets, Unicode, and near-miss tokens.

```text
cases=1200 output_mismatches=119 hit_only_mismatches=118
```

Examples:

- `"Bearer \nabcdefghijklmnop"`: the baseline redacts the token across the
  newline; the candidate leaves it unredacted because the line-level prefilter
  does not treat a line ending in `Bearer ` as a cross-line risk.
- Repeated secrets on separate lines: the candidate's hit list has one entry per
  line/pattern occurrence, while the baseline records one hit per pattern class
  over the whole text.

The sealed 23-case set does not cover these shapes. Therefore the 12.13x score
is a **benchmark-specific throughput result**, not evidence that the candidate
preserves the full redaction contract.

## Decision

Do not approve either candidate as a parent. Do not copy it into the pristine
`workspace/redaction.py`.

Required next step: add cross-line and differential cases to the sealed
evaluator, then rerun the candidate through it. A candidate that fails the
hardened evaluator is rejected regardless of speed. This is the correct
human-gate behavior: the research loop found a fast candidate, and the audit
prevented it from becoming the next generation's parent.
