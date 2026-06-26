# Phase 18 Interop Match Agreement

Status: AGREED RESULT RECORDED.

The inter-group match with `sharNamr` uses the one-run result produced on the
`sharNamr` side as the authoritative interop result, per the lecturer guidance that
one agreed run is sufficient. The local REST `/decide` rerun evidence is retained as
local diagnostic evidence only and is not the submitted interop result.

## Agreed report

- Report path: `reports/agreed_interop_match_report.json`
- Our group: `salareen`
- Opponent group: `sharNamr`
- Our first role: `thief`
- Final totals: `salareen` 40, `sharNamr` 60
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
