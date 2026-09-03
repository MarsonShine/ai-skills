# Minimal Implementation Behavior Evaluations

These fixtures probe whether implementation guidance preserves requirements while choosing small solutions. They belong to the repository evaluation workspace and are not installable skills.

## Cases

The seven requests cover an ordinary date field, an explicitly chosen range component, tenant-scoped TTL caching, an externally consumed CSV sink interface, shared label normalization, verified note access, and asynchronous shutdown.

Each entry in `cases.json` supplies a user request, starter files, and one output file. Give the evaluator only the request and starter files; keep grading criteria and `checks.py` outside its input. Save its complete output file in a separate directory alongside the starter files.

## Run the Checks

From the repository root:

```powershell
python -B -X utf8 workspaces/implement-minimal-code-evals/checks.py --case tenant-ttl-cache --directory <output-directory>
```

The command returns JSON with individual observations and a success or failure exit code. HTML probes inspect static form contracts. A custom date control that cannot be verified statically requires browser review; it is not evidence of either success or failure. Python probes execute normal, boundary, and failure behavior using the standard library.

## Comparing Skill Versions

Use fresh contexts, the same configured model and reasoning effort, identical requests, and the same repository instructions. For the baseline, use the catalog before the change. For the candidate, use the updated catalog and applicable implementation guidance. Do not feed expected answers or earlier runs back into either condition.

The recorded source-generation comparison supplies the candidate entrypoint and reference together and disables evaluator tool use. This holds inputs constant but does not simulate on-demand reference loading, repository exploration, or an agent running its own tests. The local checker executes the generated code afterward.

Treat these as bounded behavior probes. Report completeness and check results before source size, time, or token observations. Cached input, reasoning effort, one-run variance, and eagerly supplied references affect those observations; they do not establish a cost or energy saving. Browser interaction and general security are outside the automated probes.
