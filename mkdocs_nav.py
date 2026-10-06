"""mkdocs nav hook: the site's table of contents is generated, never hand-merged.

``data/gen/nav.yml`` is written by ``tools/gen_curriculum_index.py`` from ``data/src/curriculum.yaml``,
and mkdocs has no ``!include`` constructor of its own, so the fragment is read back here at build time
and handed to the very same :func:`mkdocs.structure.nav.get_navigation` that mkdocs uses for the ``nav:``
block in the config file. Nothing about the navigation is duplicated between the two languages, the
curriculum, and the site: the curriculum is the source and this file is one call.

If the fragment is missing (a repository at milestone M0, before a curriculum exists) the nav is left
exactly as the config authored it, which is what lets an empty tree still build.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from mkdocs.config.base import Config
from mkdocs.structure.files import Files
from mkdocs.structure.nav import Navigation, get_navigation

NAV_FRAGMENT = Path(__file__).resolve().parent / "data" / "gen" / "nav.yml"


def _load_fragment() -> list[dict[str, Any]]:
    if not NAV_FRAGMENT.exists():
        return []
    loaded = yaml.safe_load(NAV_FRAGMENT.read_text(encoding="utf-8"))
    return list(loaded or [])


def on_nav(nav: Navigation, config: Config, files: Files) -> Navigation:
    """Rebuild the navigation from the generated fragment, when a fragment exists.

    ``config['nav']`` is the only channel mkdocs gives a plugin to describe a tree, so the fragment is
    written into it and the build's own :func:`get_navigation` does the rest -- no hand-rolled
    ``Section``/``Page`` construction that would break on the next mkdocs release.
    """
    fragment = _load_fragment()
    if not fragment:
        return nav
    config["nav"] = fragment
    return get_navigation(files, config)
