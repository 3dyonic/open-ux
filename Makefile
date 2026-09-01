.PHONY: test catalog install

install:
	pip install -e "packages/mcp[dev]"

catalog:
	python -m open_ux validate-catalog

test:
	cd packages/mcp && python -m pytest -q
