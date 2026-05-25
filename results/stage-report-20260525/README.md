# Stage Report 2026-05-25

## Scope

- This stage report includes only currently usable summaries.
- `gpt-5.4` is a full-scope result.
- `deepseek-v3.2` and `gemini-3-flash-preview` are `no-safety` relay results and should only be compared within the same scope.
- Dirty or incomplete runs such as `kimi-k2.6`, `deepseek-r1-250528`, `doubao-seed-2-0-pro-260215`, and `gpt-5.2-pro` are excluded from the leaderboard.

## Included Runs

| Model | Scope | Judged | Failures | General % | Highlevel % | Safety % | Basic % | Stage % |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| gpt-5.4 | full_scope | 2942 | 0 | 87.07 | 75.50 | 71.20 | 61.55 | 73.83 |
| deepseek-v3.2 | relay_no_safety | 1941 | 3 | 86.06 | 73.27 |  | 59.85 | 73.06 |
| gemini-3-flash-preview | relay_no_safety | 1788 | 154 | 78.95 | 74.62 |  | 61.90 | 71.82 |

## Leaderboard: Full Scope

| Rank | Model | Stage % | General % | Safety % | Highlevel % | Basic % |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | gpt-5.4 | 73.83 | 87.07 | 71.20 | 75.50 | 61.55 |

## Leaderboard: Relay No-Safety Scope

| Rank | Model | Stage % | General % | Highlevel % | Basic % | Failures |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | deepseek-v3.2 | 73.06 | 86.06 | 73.27 | 59.85 | 3 |
| 2 | gemini-3-flash-preview | 71.82 | 78.95 | 74.62 | 61.90 | 154 |

## Notes

- `Stage %` is a normalized stage score built from currently available module-level metrics.
- `Basic %` normalizes basic-education tasks onto a 0-100 scale before aggregation.
- Cross-scope comparison is intentionally avoided: full-scope and no-safety relay runs have different included modules.
