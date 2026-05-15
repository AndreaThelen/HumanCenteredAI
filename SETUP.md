# Setup

This repository contains [OpenMATB](./OpenMATB/), an open-source re-implementation of the NASA Multi-Attribute Task Battery. The project is managed with [uv](https://docs.astral.sh/uv/), an extremely fast Python package and project manager.

## 1. Install uv

### Windows (PowerShell)

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### macOS / Linux

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Alternatives

- **winget** (Windows): `winget install --id=astral-sh.uv -e`
- **Homebrew** (macOS): `brew install uv`
- **pipx**: `pipx install uv`

After installation, open a new terminal and verify:

```bash
uv --version
```

## 2. Install Python 3.13

OpenMATB pins Python to 3.13 (see `OpenMATB/.python-version`). Let uv fetch and manage it for you:

```bash
uv python install 3.13
```

## 3. Sync project dependencies

From the repository root, move into the OpenMATB directory and let uv create the `.venv` and install everything declared in `pyproject.toml` / `uv.lock`:

```bash
cd OpenMATB
uv sync
```

This will:
- create `OpenMATB/.venv/` using Python 3.13,
- install `pyglet`, `pylsl`, `pyparallel`, and `rstr` at the versions locked in `uv.lock`.

## 4. Run MATB

From within the `OpenMATB/` directory:

```bash
uv run python main.py
```

`uv run` activates the project environment automatically — no need to manually activate `.venv`.

The application reads `config.ini` for startup options (language, screen index, fullscreen, scenario path, clock speed). Edit `OpenMATB/config.ini` to change the scenario or display settings before launching.

## Common tasks

| Action | Command (from `OpenMATB/`) |
|---|---|
| Run the app | `uv run python main.py` |
| Add a dependency | `uv add <package>` |
| Remove a dependency | `uv remove <package>` |
| Update the lockfile | `uv lock` |
| Refresh the venv from lock | `uv sync` |
| Run any python command | `uv run python <args>` |

## Troubleshooting

- **`uv: command not found`** — restart your terminal so the installer's PATH change takes effect, or follow the manual PATH instructions printed by the installer.
- **Joystick / tracking task** — the tracking module expects a connected joystick. Without one, other tasks still work but the tracking task will be idle.
- **`inpout32.dll` / parallel port errors on non-Windows hosts** — `pyparallel` is only required for parallel-port triggers (EEG sync). On macOS/Linux you can ignore parallel-port warnings if you're not using that hardware.
- **Scenario errors** — check `OpenMATB/last_scenario_errors.log` after a failed run.

## References

- uv documentation: https://docs.astral.sh/uv/
- OpenMATB README: [`OpenMATB/README.md`](./OpenMATB/README.md)
- OpenMATB wiki / tutorials: https://github.com/juliencegarra/OpenMATB/wiki
