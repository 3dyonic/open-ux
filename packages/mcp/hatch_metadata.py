from __future__ import annotations

from pathlib import Path

from hatchling.metadata.plugin.interface import MetadataHookInterface

_REPO = "https://github.com/3dyonic/open-ux"
_RAW = "https://raw.githubusercontent.com/3dyonic/open-ux/master"

_PYPI_LINKS = (
    ("](docs/readme-hero.svg)", f"]({_RAW}/docs/readme-hero.svg)"),
    ("](LICENSE)", f"]({_REPO}/blob/master/LICENSE)"),
    ("](catalog/README.md)", f"]({_REPO}/blob/master/catalog/README.md)"),
    ("](clients/plugin)", f"]({_REPO}/tree/master/clients/plugin)"),
    ("](docs/PRIVACY.md)", f"]({_REPO}/blob/master/docs/PRIVACY.md)"),
)


def _for_pypi(text: str) -> str:
    for src, dest in _PYPI_LINKS:
        text = text.replace(src, dest)
    return text


class CustomMetadataHook(MetadataHookInterface):
    """Use the public root README as the package description."""

    def update(self, metadata: dict) -> None:
        repo_readme = Path(self.root).resolve().parent.parent / "README.md"
        local_readme = Path(self.root) / "README.md"
        if repo_readme.is_file() and repo_readme.resolve() != local_readme.resolve():
            readme = repo_readme
        elif local_readme.is_file():
            readme = local_readme
        else:
            raise RuntimeError("README.md not found for package metadata")
        metadata["readme"] = {
            "content-type": "text/markdown",
            "text": _for_pypi(readme.read_text(encoding="utf-8")),
        }
