# jobninja-tools

Shared utilities for JobNinja services.

## Install

From PyPI (once published):

```bash
pip install jobninja-tools
# or
uv add jobninja-tools
```

Import name is `jn_tools`:

```python
from jn_tools.cloud_watch_client import CloudWatchClient
```

## Development

Requires Python 3.13 and [uv](https://docs.astral.sh/uv/).

```bash
uv sync --extra dev
uv run pre-commit install
uv run pytest
uv run ruff check .
uv run ruff format .
```

## Releasing

Versions are derived from git tags via `hatch-vcs`.

1. Pre-release to TestPyPI: `git tag v0.1.0rc1 && git push origin v0.1.0rc1`
2. Production release to PyPI: `git tag v0.1.0 && git push origin v0.1.0`

The `release.yml` workflow builds the sdist+wheel and publishes via PyPI Trusted Publishers (OIDC).
