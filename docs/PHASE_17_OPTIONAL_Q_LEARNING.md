# Phase 17 — Optional Q-learning

Q-learning is implemented as an optional policy and is not a normal-mode dependency. The default
configuration keeps `learning.enabled` false, so the fixed heuristic remains the production
fallback.

## Safety boundary

- State keys are built only from `PolicyInput`, which is derived from the public observation DTO.
- Hidden authoritative `GameState` fields are never accepted by the Q-policy.
- Cop and Thief use separate in-memory tables and separate versioned JSON files.
- Legal-action indices are role-specific. Thief barrier indices are rejected.
- Terminal updates use reward only and never bootstrap from a future state.
- MCP action contracts, report schemas, and technical-failure handling are unchanged.

## Configuration and commands

The `learning` object in `config.json` controls `enabled`, `alpha`, `gamma`, `epsilon`, policy seed,
distinct training/evaluation seeds, and separate table paths. Generated files live under ignored
`artifacts/learning/`.

```powershell
python main.py --mode internal --config config.json --engine-only --policy heuristic --quiet
python main.py --mode internal --config config.json --evaluate-learning
```

The evaluation runs six heuristic games and six learning-policy games with the evaluation seed. It
records scores, technical failures, illegal actions, and average moves. If reliability regresses,
`recommended_runtime_policy` is `heuristic`.

To run persisted Q-tables directly, set `learning.enabled` to `true`:

```powershell
python main.py --mode internal --config config.json --engine-only --policy q-learning --quiet
```

## Verification

`tests/unit/test_q_learning.py` covers observation-only encoding, action indices, epsilon-greedy
selection, terminal-safe updates, role separation, persistence, version rejection, and fallback.
`tests/unit/test_learning_evaluation.py` covers deterministic baseline comparison and metrics.
