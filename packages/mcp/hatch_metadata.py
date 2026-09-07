from __future__ import annotations

from pathlib import Path

from hatchling.metadata.plugin.interface import MetadataHookInterface


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
            "text": readme.read_text(encoding="utf-8"),
        }
