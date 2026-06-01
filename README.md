# dotfiles

Personal dotfiles for my [OM1 `devenv`](https://github.com/om1inc/devenv) instance:
**bash** as the login shell, [**starship**](https://starship.rs) prompt (default config),
and a tmux config tuned for long-lived SSM/SSH sessions.

## How it's used

The devenv provisioner clones this repo and runs [`setup`](./setup) as my user on
every `devenv up` / `devenv rebuild`. It's wired in `om1inc/devenv`'s
`terraform/environments/shared-services/environment.tfvars`:

```hcl
"jyates" = {
  volume_size     = 250
  dotfiles_repo   = "https://github.com/<your-github>/dotfiles"
  dotfiles_branch = "main"
  dotfiles_script = "setup"
}
```

> The provisioner clones with **no credentials**, so this repo must stay **public**.

## What `setup` does

1. Symlinks `~/.bashrc`, `~/.bash_profile`, `~/.tmux.conf` (backs up any real files first).
2. Creates `~/.gitconfig` including [`git/gitconfig_template`](./git/gitconfig_template)
   with identity `Tucker Yates <jyates@om1.com>` (skipped inside devcontainers,
   which inherit the host gitconfig).
3. Symlinks `~/.docker/config.json` to enable the ECR credential helper.
4. **Sets the default login shell to `/bin/bash`** via `chsh` (uses the devenv's
   passwordless sudo). This is the durable replacement for the host default of zsh.
5. Best-effort installs starship and the ECR helper if missing (no-ops on a
   already-provisioned host).

Everything except the symlinks is best-effort: failures warn and continue.

## Layout

| Path | Purpose |
|------|---------|
| `setup` | Provisioning entrypoint (`dotfiles_script`) |
| `bash/.bashrc` | Interactive bash config: history, aliases, completion, starship init |
| `bash/.bash_profile` | Login shells source `~/.bashrc` |
| `tmux/.tmux.conf` | tmux defaults (mouse, 50k scrollback, sane splits) |
| `git/gitconfig_template` | Shared git config, *included* by `~/.gitconfig` |
| `docker/config.json` | ECR credential helper |

## Local escape hatch

`~/.bashrc.local` (untracked) is sourced last if present — put machine-specific
tweaks there without touching this repo.

## Running it manually

```bash
git clone https://github.com/<your-github>/dotfiles ~/dotfiles
~/dotfiles/setup
exec bash -l   # or just reconnect
```
