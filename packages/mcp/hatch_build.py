from __future__ import annotations

from pathlib import Path

from hatchling.builders.hooks.plugin.interface import BuildHookInterface


class CustomBuildHook(BuildHookInterface):
    """Ship repo catalog/ in the wheel and sdist (not copied into git src/)."""

    def initialize(self, version: str, build_data: dict) -> None:
        in_tree = Path(self.root) / "src" / "open_ux" / "data" / "catalog"
        repo = Path(self.root).resolve().parent.parent / "catalog"
        if (in_tree / "schema.json").is_file():
            catalog = in_tree
        elif (repo / "schema.json").is_file():
            catalog = repo
        else:
            raise RuntimeError(
                "catalog/schema.json not found; expected repo catalog/ or "
                "sdist src/open_ux/data/catalog"
            )
        dest = (
            "src/open_ux/data/catalog"
            if self.target_name == "sdist"
            else "open_ux/data/catalog"
        )
        build_data.setdefault("force_include", {})
        build_data["force_include"][str(catalog)] = dest
        repo_root = Path(self.root).resolve().parent.parent
        helpers_registry = repo_root / "helpers" / "registry.json"
        if helpers_registry.is_file():
            reg_dest = (
                "src/open_ux/data/helpers/registry.json"
                if self.target_name == "sdist"
                else "open_ux/data/helpers/registry.json"
            )
            build_data["force_include"][str(helpers_registry)] = reg_dest
        if self.target_name == "sdist":
            repo_readme = Path(self.root).resolve().parent.parent / "README.md"
            if repo_readme.is_file():
                build_data["force_include"][str(repo_readme)] = "README.md"
