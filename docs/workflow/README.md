# Delivery Registry

The delivery registry tracks active and completed OpenIM requirements.

Use one YAML file per requirement. Do not keep all active work in one global YAML file, because parallel branches would constantly conflict.

Directory layout:

```text
docs/workflow/
  active/      # requirements currently being shaped, designed, built, tested, or released
  done/        # accepted requirements
  archived/    # rejected, deferred, or abandoned requirements
  schema.md    # field reference and allowed values
  template.yml # starting point for a new requirement registry file
```

Rules:

- Create a registry file before non-trivial work leaves the idea stage.
- Name files as `REQ-0000-short-name.yml`, `BUG-0000-short-name.yml`, or `CHORE-0000-short-name.yml`.
- Keep the registry file on the same branch as the work it tracks.
- Update the registry file whenever a gate changes.
- Move the file from `active/` to `done/` after acceptance.
- Move the file from `active/` to `archived/` when the work is rejected, deferred, or abandoned.

For a new requirement, copy:

```text
docs/workflow/template.yml
```

to:

```text
docs/workflow/active/REQ-0000-short-name.yml
```

Then fill in the GitHub Issue, docs, branch, worktree, and review fields as the work progresses.
