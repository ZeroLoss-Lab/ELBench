# Stage Report 2026-05-25

## Scope

- This stage report includes only currently usable summaries.
- `gpt-5.4` is a full-scope result.
- `deepseek-v3.2` is a `no-safety` relay result and should only be compared within the same scope.
- Dirty, incomplete, expensive, or incompatible runs such as `gemini-3-flash-preview`, `kimi-k2.6`, `deepseek-r1-250528`, `doubao-seed-2-0-pro-260215`, and `gpt-5.2-pro` are excluded from the leaderboard.

## Included Runs

| Model | Scope | Judged | Failures | General % | Highlevel % | Safety % | Basic % | Stage % |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| gpt-5.4 | full_scope | 2942 | 0 | 87.07 | 75.50 | 71.20 | 61.55 | 73.83 |
| deepseek-v3.2 | relay_no_safety | 1942 | 3 | 86.06 | 73.30 |  | 59.85 | 73.07 |

## Leaderboard: Full Scope

| Rank | Model | Stage % | General % | Safety % | Highlevel % | Basic % |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | gpt-5.4 | 73.83 | 87.07 | 71.20 | 75.50 | 61.55 |

## Leaderboard: Relay No-Safety Scope

| Rank | Model | Stage % | General % | Highlevel % | Basic % | Failures |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | deepseek-v3.2 | 73.07 | 86.06 | 73.30 | 59.85 | 3 |

## Notes

- `Stage %` is a normalized stage score built from currently available module-level metrics.
- `Basic %` normalizes basic-education tasks onto a 0-100 scale before aggregation.
- Cross-scope comparison is intentionally avoided: full-scope and no-safety relay runs have different included modules.
