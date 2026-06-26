# Phase 18 Bonus/Interop Match Agreement

Status: AGREED RESULT RECORDED.

The inter-group match with `sharNamr` uses the one-run result produced on the
`sharNamr` side as the authoritative `bonus_game` result, per the lecturer guidance
that one agreed run is sufficient. The local REST `/decide` rerun evidence is retained
as diagnostic evidence only and is not the submitted bonus result.

## Agreed report

- Report path: `reports/agreed_interop_match_report.json`
- Report type: `bonus_game`
- Group 1: `salareen`
- Group 2: `sharNamr`
- Final totals: `salareen` 40, `sharNamr` 60
- Bonus claim: `salareen` 7, `sharNamr` 10
- Mutual agreement: `true`
- Gmail delivery: not performed

## Game summary

| Index | salareen role | Winner | Moves | salareen score | sharNamr score |
|---:|---|---|---:|---:|---:|
| 0 | thief | thief | 25 | 10 | 5 |
| 1 | thief | thief | 25 | 10 | 5 |
| 2 | thief | cop | 8 | 5 | 20 |
| 3 | cop | thief | 25 | 5 | 10 |
| 4 | cop | thief | 25 | 5 | 10 |
| 5 | cop | thief | 25 | 5 | 10 |

## Safety

No Gmail API call is part of this step. The report is committed only as a JSON
artifact for review and later manual submission when explicitly approved.
