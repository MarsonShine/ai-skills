# Validation Results — 2026-09-03

The plugin and all 24 skill entrypoints passed format validation. The installed copies of the two changed skills match their source files. A fresh installed-catalog probe found implement-minimal-code and selected it for a new ASP.NET Core endpoint, without selecting the .NET review skill.

## Routing

All 50 catalog-routing cases passed in separate fresh Codex contexts after reinstall. Only names and descriptions were supplied, expected answers were withheld, and no skill body or tool was used. The full selected sets and telemetry are in [results.json](runs/2026-09-03/results.json).

## Behavior

Both the baseline and candidate passed all seven case-level probes (14 generated implementations). The five Python cases execute behavior; the two HTML cases check static contracts. Both arms independently chose a native date input and retained the explicitly required range component.

| Case | Baseline | Candidate | Source lines, baseline / candidate | Seconds, baseline / candidate |
|---|---|---|---:|---:|
| native-single-date | [Pass](runs/2026-09-03/baseline/native-single-date/booking.html) | [Pass](runs/2026-09-03/candidate/native-single-date/booking.html) | 13 / 13 | 19.25 / 25.74 |
| preserve-range-component | [Pass](runs/2026-09-03/baseline/preserve-range-component/booking.html) | [Pass](runs/2026-09-03/candidate/preserve-range-component/booking.html) | 17 / 17 | 22.67 / 30.98 |
| tenant-ttl-cache | [Pass](runs/2026-09-03/baseline/tenant-ttl-cache/cache.py) | [Pass](runs/2026-09-03/candidate/tenant-ttl-cache/cache.py) | 25 / 25 | 52.02 / 41.11 |
| injected-csv-interface | [Pass](runs/2026-09-03/baseline/injected-csv-interface/report.py) | [Pass](runs/2026-09-03/candidate/injected-csv-interface/report.py) | 36 / 38 | 29.14 / 40.09 |
| shared-normalization | [Pass](runs/2026-09-03/baseline/shared-normalization/labels.py) | [Pass](runs/2026-09-03/candidate/shared-normalization/labels.py) | 68 / 24 | 86.11 / 28.61 |
| verified-note-access | [Pass](runs/2026-09-03/baseline/verified-note-access/notes.py) | [Pass](runs/2026-09-03/candidate/verified-note-access/notes.py) | 38 / 38 | 31.7 / 33.89 |
| async-clean-shutdown | [Pass](runs/2026-09-03/baseline/async-clean-shutdown/jobs.py) | [Pass](runs/2026-09-03/candidate/async-clean-shutdown/jobs.py) | 32 / 33 | 82.64 / 73.41 |

The fixture checker was separately checked against seven correct implementations, seven unchanged starters, seven empty stubs, seven implementations violating key contracts, and one custom date control requiring browser review. These self-checks assess the checker, not the skill.

## Interpretation and Reproduction

The comparison used the configured gpt-5.6-sol model at ultra reasoning effort, one sample per case and arm. The baseline content matches the public repository commit recorded in results.json. New guidance and fixtures contain generic rules and synthetic data.

The result supports preservation of the probed contracts; it does not demonstrate a general improvement over the existing library. Candidate references were supplied eagerly, contexts can have different cached input, and generation did not use tools or run its own tests. Line counts include the complete output source and are observations, not a correctness or maintenance score. The baseline normalization file includes additional doctest regression examples; its larger size must not be described as unnecessary implementation. This constrained comparison does not assess whether an agent adds regression tests in a real repository.

Input, cached-input, output, and reasoning token telemetry is retained in results.json. Output usage already includes reasoning; do not add it again. No dollar cost or energy saving is inferred. Browser interaction, repeated-run statistics, and general security are not covered.

Re-run a saved implementation from the repository root:

```powershell
python -B -X utf8 workspaces/implement-minimal-code-evals/checks.py --case tenant-ttl-cache --directory workspaces/implement-minimal-code-evals/runs/2026-09-03/candidate/tenant-ttl-cache
```
