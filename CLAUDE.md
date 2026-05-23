# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

sbx-toolkit provides two bash scripts for running AI coding agents in [Docker Sandboxes](https://github.com/docker/sbx-releases):

- **`sbx-setup`** — machine-level setup: builds a Docker image that bakes in your agent config (`~/.claude`, mise, etc.) and pushes it to a local registry. Run once per machine, not per project.
- **`sbx-start`** — project-level runner: reads `.sbx.toml` from the current directory, applies network policy / secrets checks, and delegates to `sbx run`.

## Key design constraints

- **Pure bash, no external dependencies** — no jq, python, or node. The TOML parser in `sbx-start` is a hand-rolled awk/grep/sed one-liner.
- **Secrets never touch files or image layers** — `.sbx.toml` holds only secret *names*; values live in the OS keychain via `sbx secret set`.
- **Every default is overridable** — `--template`, `--agent`, `--registry`, `--config`, etc.

## Running the scripts

```bash
# Build your local sandbox environment (run from the repo root)
./sbx-setup --agent claude-code --config ~/.claude

# Use host statusline.py only — skip if absent
./sbx-setup --config ~/.claude --statusline inherit

# Skip statusline entirely
./sbx-setup --config ~/.claude --statusline off

# Preview without executing
./sbx-setup --config ~/.claude --dry-run

# Start a sandbox in any project that has a .sbx.toml
cd /your/project
sbx-start
sbx-start --dry-run
```

The install script puts both binaries on `$PATH`:

```bash
curl -fsSL https://raw.githubusercontent.com/maxkrivich/sbx-toolkit/main/install.sh | bash
```

After install, templates are stored at `${XDG_DATA_HOME:-$HOME/.local/share}/sbx-toolkit/templates/`.

## Repo structure

```
sbx-setup              # Machine setup script
sbx-start              # Project runner script
install.sh             # curl installer — downloads both binaries + templates + kits
sbx.toml.example       # Annotated .sbx.toml template for projects
templates/
  base/Dockerfile      # Thinnest valid sandbox base
  mise/Dockerfile      # Adds mise for polyglot version management
  README.md            # Guide for writing custom templates
kits/
  statusline/
    spec.yaml          # Mixin kit: restores statusLine on every sandbox startup
```

## How sbx-setup works internally

1. Resolves the Dockerfile: `templates/<template>/Dockerfile` or `--dockerfile <path>`
2. Creates a temp build context and copies the Dockerfile + agent config into it
3. Starts a local `registry:2` container on `localhost:5000` if one isn't running
4. Runs `docker build --build-arg AGENT=<agent> --build-arg CONFIG_TARGET=<path>`
5. Pushes the image; prints the `template = "..."` line to paste into `.sbx.toml`

## How sbx-start works internally

1. Parses `.sbx.toml` using `toml_get` (grep/sed) and `toml_get_array` (awk)
2. Checks `sbx secret ls` against `required_secrets` and warns on missing entries
3. Calls `sbx policy set-default <network_policy>` if current policy differs
4. Applies `allowed_domains` / `blocked_domains` via `sbx policy allow/block network`
5. Builds and execs `sbx run --template <template> [--branch <branch>] [--kit <kit>] <agent> .`

## Writing a custom template

Add `templates/my-template/Dockerfile`. Required pattern:

```dockerfile
ARG AGENT=claude-code
FROM docker/sandbox-templates:${AGENT}
ARG AGENT=claude-code   # must re-declare after FROM

USER root
RUN apt-get update && apt-get install -y my-tool && rm -rf /var/lib/apt/lists/*
USER agent
```

Then reference it with `./sbx-setup --template my-template --agent claude-code`.

## .sbx.toml fields

| Field | Required | Default | Notes |
|---|---|---|---|
| `agent` | yes | — | `claude`, `codex`, `kiro`, `shell`, etc. |
| `template` | yes | — | Image ref printed by `sbx-setup` |
| `network_policy` | | `balanced` | `open`, `balanced`, `locked-down` |
| `branch` | | — | `auto`, a branch name, or omit for direct mode |
| `required_secrets` | | — | Names only — warns if missing |
| `allowed_domains` | | — | Added on top of base policy |
| `blocked_domains` | | — | Always win over base policy |
| `extra_workspaces` | | — | Extra paths mounted into the sandbox |
