# `girokmoji adopt` quickstart (agent edition)

`girokmoji adopt <repo-url|path>` clones (or reuses) a repository, ensures tags
are fetchable, runs the existing release pipeline, and emits parseable output so
agents can push the result back to CI/CD without bespoke glue.

## Safety defaults

- `--dry-run` is **on** by default: tags are created only inside the temporary
  checkout and removed before exit.
- Temporary clones live under `/tmp/girokmoji-adopt-*` and are deleted unless
  you pass `--keep-workdir` or `--workdir`.
- Nothing is pushed unless you explicitly add `--apply`.

## Inputs & flags

| Flag | Purpose |
| --- | --- |
| `repo` (positional) | URL (`https://`, `ssh`, `git@`, `file://`) or local path to adopt. |
| `--project-name` | Override the inferred project name (defaults to repo folder name). |
| `--bump {patch,minor,major}` | Which SemVer part to bump (default `patch`). |
| `--ref <ref>` | Branch/tag/commit to checkout before running the release flow. |
| `--dry-run` / `--apply` | Simulate tagging/pushing vs actually doing it (dry-run default). |
| `--format text|json` / `--json` | Output mode. JSON prints a single object on stdout; logs stay on stderr. |
| `--workdir <path>` | Reuse an existing checkout or clone into this directory. |
| `--keep-workdir` | Keep the temp clone for inspection after completion. |
| `--push-remote <name|url>` | Remote name or URL used when pushing during `--apply` (default `origin`). |
| `--depth <n>` | Clone depth; `0` forces full history. |
| `--changelog-out <file>` | Tee the rendered changelog to a file. |
| `--range`, `--strict-ancestor`, `--quiet`, `--verbose` | Passed straight through to the underlying `release` command. |

## Output contract (JSON)

`--format json` (or `--json`) emits exactly one object on stdout:

```json
{
  "repo_url": "https://github.com/acme/api",
  "workdir": "/tmp/girokmoji-adopt-x2",
  "workdir_persisted": false,
  "ref": "main",
  "commit": "abcd1234...",
  "default_branch": "main",
  "previous_tag": "v1.7.3",
  "new_version": "1.8.0",
  "new_tag": "v1.8.0",
  "release_type": "minor",
  "dry_run": true,
  "tag_created": false,
  "pushed": false,
  "changelog": "## 1.8.0 ...",
  "changelog_path": null,
  "next_steps": ["cd ...", "git tag ...", "git push ..."],
  "duration_ms": 2400
}
```

Text mode mirrors these fields with header lines, a numbered `next_steps`
section, and `---- changelog start ----` delimiters around the rendered note.

## Exit codes

| Code | Meaning |
| --- | --- |
| `0` | Success |
| `10` | `CLONE_FAILED` |
| `11` | `FETCH_TAGS_FAILED` |
| `12` | `CHECKOUT_FAILED` |
| `13` | `AUTH_FAILED` (clone/push) |
| `14` | `INVALID_REPO` |
| `15` | `DIRTY_WORKDIR` |
| `20` | `RELEASE_FAILED` |
| `99` | `UNKNOWN` |

Errors in JSON mode follow `{ "error": { "code": ..., "message": ..., "hint": ..., "retryable": bool } }`.

## Copy-paste examples

```bash
# Dry-run JSON for a public repo
girokmoji adopt https://github.com/acme/api --json

# Inspect or hand-edit by keeping the clone
girokmoji adopt https://github.com/acme/api --keep-workdir --format text

# Adopt a local checkout and actually create/push the tag
girokmoji adopt . --apply --push-remote origin --format json
```

## Troubleshooting

- **DIRTY_WORKDIR** → clean/stash the checkout or point `adopt` at a fresh clone.
- **FETCH_TAGS_FAILED / AUTH_FAILED** → ensure `GH_TOKEN`, SSH keys, or
  `GIT_SSH_COMMAND` are set so libgit2 can authenticate.
- **CHECKOUT_FAILED** → double-check `--ref`; the ref must exist after the fetch.
- **Shallow history** → rerun with `--depth 0` (full history) or an appropriate
  depth.

## Security & cleanup notes

- Temporary clones are removed unless you opt into `--keep-workdir` (or provide
  `--workdir`).
- Outputs list shell-ready next steps; if you need the working tree afterwards,
  keep it alive via `--keep-workdir`.
- Adopt never pushes unless `--apply` is set, and only pushes the computed tag to
  the requested remote.
