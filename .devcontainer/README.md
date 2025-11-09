# Development Container

This project uses a [Development Container](https://containers.dev/) to provide a consistent development environment.

## Getting Started

1. Install [Docker Desktop](https://www.docker.com/products/docker-desktop)
2. Install [VS Code](https://code.visualstudio.com/) and the [Dev Containers extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers)
3. Open this folder in VS Code
4. When prompted, click "Reopen in Container" (or run command: `Dev Containers: Reopen in Container`)

## Local Customization

To customize your local development environment without modifying the committed configuration, create a `.devcontainer/devcontainer.local.json` file (this file is gitignored).

### Example: Add Additional VS Code Extensions

```json
{
  "customizations": {
    "vscode": {
      "extensions": [
        "esbenp.prettier-vscode",
        "usernamehw.errorlens"
      ]
    }
  }
}
```

### Example: Mount Additional Volumes

```json
{
  "mounts": [
    "source=${localEnv:HOME}/.gitconfig,target=/home/vscode/.gitconfig,type=bind,consistency=cached"
  ]
}
```

### Example: Override or Add Environment Variables

The container sets several Python-related environment variables by default (see `Dockerfile.dev`). You can override them or add new ones using `remoteEnv`:

```json
{
  "remoteEnv": {
    "PYTHONUNBUFFERED": "0",
    "DEBUG": "1",
    "LOG_LEVEL": "DEBUG"
  }
}
```

See `devcontainer.local.json.example` for a complete list of default environment variables that can be overridden.

Alternatively, create a `.devcontainer/.env` file (also gitignored):
```bash
DEBUG=1
LOG_LEVEL=DEBUG
```

And reference it in `devcontainer.local.json`:
```json
{
  "runArgs": ["--env-file", ".devcontainer/.env"]
}
```

### Example: Forward Additional Ports

```json
{
  "forwardPorts": [8080, 3000]
}
```

## How It Works

The Dev Container will:
- Build from `Dockerfile.dev`
- Mount your workspace to `/app`
- Install Git and GitHub CLI features
- Run `uv sync --all-groups` to create a virtual environment at `/app/.venv`
- Configure VS Code to use the virtual environment's Python interpreter
- Set up bash as the default terminal

### Default Environment Variables

The following Python-related environment variables are set in the container:

- **`PYTHONUNBUFFERED=1`** - Ensures real-time output in logs
- **`PYTHONDONTWRITEBYTECODE=1`** - Prevents `.pyc` file creation
- **`PYTHONIOENCODING=utf-8`** - Ensures UTF-8 encoding for I/O
- **`PIP_NO_CACHE_DIR=1`** - Disables pip caching to reduce container size
- **`PIP_DISABLE_PIP_VERSION_CHECK=1`** - Suppresses pip update warnings
- **`UV_NO_CACHE=1`** - Disables uv caching
- **`UV_PROJECT_ENVIRONMENT=/app/.venv`** - Sets the virtual environment location for uv
- **`LANG=C.UTF-8`** - Sets locale for proper Unicode handling
- **`LC_ALL=C.UTF-8`** - Sets all locale categories to UTF-8

These can be overridden in `devcontainer.local.json` using the `remoteEnv` property.

### Virtual Environment

The project uses `uv` to manage dependencies. When the container is created:
1. `uv sync --all-groups` is automatically run to create a virtual environment at `/app/.venv`
2. VS Code is configured to use `/app/.venv/bin/python` as the Python interpreter
3. All dependencies from `pyproject.toml` (including dev groups) are installed

To manually update dependencies, run:
```bash
uv sync --all-groups
```

## Rebuilding the Container

If you modify the Dockerfile or devcontainer configuration:
1. Run command: `Dev Containers: Rebuild Container`
2. Or run: `Dev Containers: Rebuild Container Without Cache` for a clean build
