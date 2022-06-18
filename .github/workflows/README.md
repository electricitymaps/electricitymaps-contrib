# CI

All CI workflows should be executed in the `CI.yml` workflow using reusable workflows and the workflow_call trigger.

To add another workflow to the CI workflow create a new job that looks like this:

```yml
job_example:
  name: Example job
  uses: ./.github/workflows/example.yml
```
