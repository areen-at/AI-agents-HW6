# Phase 18 Bonus/Interop Match Agreement

Status: AGREED RESULT RECORDED.

The inter-group match with `sharNamr` uses the one-run result produced on the
`sharNamr` side as the authoritative `bonus_game` result, per the lecturer guidance
that one agreed run is sufficient. The local REST `/decide` rerun evidence is retained
as diagnostic evidence only and is not the submitted bonus result.

## Agreed report

- Report path: `reports/agreed_interop_match_report.json`
- Report type: `bonus_game`
- Group 1: `sharNamr`
- Group 2: `salareen`
- Final totals: `sharNamr` 60, `salareen` 40
- Bonus claim: `sharNamr` 10, `salareen` 7
- Mutual agreement: `true`
- Gmail delivery: not performed

## Game summary

| Index | sharNamr role | Winner | Moves | sharNamr score | salareen score |
|---:|---|---|---:|---:|---:|
| 0 | cop | thief | 25 | 5 | 10 |
| 1 | cop | thief | 25 | 5 | 10 |
| 2 | cop | cop | 8 | 20 | 5 |
| 3 | thief | thief | 25 | 10 | 5 |
| 4 | thief | thief | 25 | 10 | 5 |
| 5 | thief | thief | 25 | 10 | 5 |

## Safety

No Gmail API call is part of this step. The report is committed only as a JSON
artifact for review and later manual submission when explicitly approved.
