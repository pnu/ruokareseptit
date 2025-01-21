"""Navigation definition and utilities"""

import re
from flask import request
from flask import url_for
from flask import session
from flask import g

type NavigationTree = list["NavigationTreeItem"]
type NavigationTreeItem = list[str | NavigationTree | bool]

NAVIGATION: NavigationTree = [
    ["home.index", "Ruokareseptit"],
    ["about.index", "Tietoa", [
        ["about.index", "Palvelu"],
        ["about.instructions", "Ohjeet", [
            ["about.instructions_abc", "ABC"],
            ["about.instructions_xyz", "XYZ"],
            ["https://www.google.com/", "Google"]
        ]],
        ["about.contact", "Yhteystiedot"]
    ]],
    ["auth.register", "Rekisteröidy"],
    ["auth.login", "Kirjaudu"]
]

NAVIGATION_LOGGED_IN: NavigationTree = [
    ["home.index", "Ruokareseptit"],
    ["about.index", "Tietoa", [
        ["about.index", "Palvelu"],
        ["about.instructions", "Ohjeet", [
            ["about.instructions_abc", "ABC"],
            ["about.instructions_xyz", "XYZ"],
            ["https://www.google.com/", "Google"]
        ]],
        ["about.contact", "Yhteystiedot"]
    ]],
    ["profile.index", "👤 Profiili", [
        ["profile.index", "Omat tiedot"],
        ["profile.recipes", "Omat reseptit"],
        ["profile.friends", "Kaverit"],
        ["profile.settings", "Asetukset"],
        ["auth.logout", "Kirjaudu ulos"]
    ]]
]

type NavigationItemDict = dict[str, str]
type NavigationLayer = tuple[int, list[NavigationItemDict]]
type Navigation = list[NavigationLayer]


def navigation_context():
    """Function to be register as context processor, used to inject
    `navigation` to the context."""
    if session.get("uid") is not None:
        navigation = get_navigation(NAVIGATION_LOGGED_IN, request.endpoint)
    else:
        navigation = get_navigation(NAVIGATION, request.endpoint)
    return {"navigation": navigation}


def get_navigation(tree: NavigationTree, endpoint: str):
    """Build a flattened and enumerated list of navigation levels for the
    `base.html` template. Every level is a list of dicts, defining the title
    and url for each navigation item at that level. If the current endpoint
    (eg. `home.index`) matches any of the items (or items below that in the
    navigation tree), the dict has also attribute `class="current"` which
    is used to select the CSS style.

    Eg. structure of the return value:
    `[ (0, [dict, dict, ...]), (1, [dict, dict, ...]) ]`
    """
    pruned, _ = prune(tree, endpoint)
    return flatten(pruned)


def flatten(tree: NavigationTree, level: int = 0) -> Navigation:
    """Flatten navigation tree to a list of enumerated dicts. This is
    passed to the base layout for rendering."""
    this_level, next_level = [], None
    for item in tree:
        endpoint, title = item[0], item[1]
        if re.match(r"\w+(\.\w+)+$", endpoint):
            endpoint = url_for(endpoint)
        if "__USERNAME__" in title and g.get("user") is not None:
            title = title.replace("__USERNAME__", g.user["username"])
        itemdict = {"title": title, "url": endpoint}
        if len(item) > 2:
            itemdict["class"] = "current"
            subtree = item[2]
            next_level = flatten(subtree, level + 1)
        this_level.append(itemdict)
    if len(this_level) == 0:
        return []
    all_levels = [(level, this_level)]
    if next_level is not None:
        all_levels.extend(next_level)
    return all_levels


def prune(tree: NavigationTree, current: str) -> tuple[NavigationTree, bool]:
    """Return pruned `navigation_tree` that contain only items relevant for
    the `current` endpoint. Returned bool indicates if any of the items in
    this tree (or it's subtrees) is an exact match."""
    pruned, any_match = [], False
    for item in tree:
        endpoint: str = item[0]
        title: str = item[1]
        subtree, submatch = None, False
        if len(item) > 2 and isinstance(item[2], list):
            subtree, submatch = prune(item[2], current)
        nav_item = [endpoint, title]
        if endpoint == current or submatch:
            any_match = True
            if subtree is not None:
                nav_item.append(subtree)
            else:
                nav_item.append([])
        pruned.append(nav_item)
    return pruned, any_match
