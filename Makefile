.PHONY: test catalog install install-pip

# Contributor path: uv + packages/mcp/uv.lock → packages/mcp/.venv
install:
	uv sync --frozen --extra dev --directory packages/mcp

# Fallback when uv is not installed (floating pip ranges; not the lockfile)
install-pip:
	pip install -e "packages/mcp[dev]"

catalog:
	cd packages/mcp && uv run python -m open_ux validate-catalog

test:
	cd packages/mcp && uv run python -m pytest -q
