"""Navigation definition and utilities"""

import re
from flask import request
from flask import url_for
from flask import session
from flask import g

type NavigationTree = list["NavigationTreeItem"]
type NavigationTreeItem = list[str | NavigationTree | bool]

NAVIGATION_COMMON_ITEMS = [
    ["home.index", "Ruokareseptit"],
    [
        "recipes.browse.index",
        "Reseptit",
        [
            ["recipes.browse.index", "Kaikki"],
            # ["recipes.categories.index", "Kategoriat", [
            #     ["recipes.categories.index", "Kaikki"],
            #     ["recipes.categories.abc", "ABC"],
            #     ["recipes.categories.xyz", "XYZ"],
            #     ["https://www.google.com/", "Google"]
            # ]],
            ["recipes.search.index", "Haku"],
        ],
    ],
]

NAVIGATION: NavigationTree = [
    *NAVIGATION_COMMON_ITEMS,
    ["auth.register", "Rekisteröidy"],
    ["auth.login", "Kirjaudu"],
]

NAVIGATION_LOGGED_IN: NavigationTree = [
    *NAVIGATION_COMMON_ITEMS,
    [
        "my.recipes.index",
        "Omat  ( 👤 __USERNAME__ )",
        [
            ["my.recipes.index", "Reseptit"],
            ["my.recipes.create", "Luo uusi resepti"],
            ["my.reviews.index", "Arvostelut"],
            ["auth.logout", "Kirjaudu ulos"],
        ],
    ],
]

type NavigationItem = tuple[int, dict[str, str]]
type NavigationLayer = tuple[int, list[NavigationItem]]
type Navigation = list[NavigationLayer]


def register_context_processor(app):
    """Register context processor"""
    app.context_processor(navigation_context)


def navigation_context():
    """Function to be register as context processor, used to inject
    `navigation` to the context.
    """
    if session.get("uid"):
        navigation = get_navigation(NAVIGATION_LOGGED_IN, request.endpoint)
    else:
        navigation = get_navigation(NAVIGATION, request.endpoint)
    return {"navigation": navigation}


def get_navigation(tree: NavigationTree, endpoint: str):
    """Build a flattened and enumerated list of navigation levels for the
    `base.html` template. Every level is a list of `(index, dict)`, defining
    the title and url for each navigation item at that level. If the current
    endpoint (eg. `home.index`) matches any of the items (or items below that
    in the navigation tree), the dict has also attribute `class="current"`
    which is used to select the CSS style.

    Eg. structure of the return value:
    `[ (0, [(0, dict), (1, dict), ...]), (1, [(0, dict), (1, dict), ...]) ]`
    """
    pruned, _ = prune(tree, endpoint)
    return flatten(pruned)


def flatten(tree: NavigationTree, level: int = 0) -> Navigation:
    """Flatten navigation tree to an enumerated list of enumerated
    dicts. This is passed to the base layout for rendering.
    """
    this_level, next_level = [], None
    for item in tree:
        endpoint, title = item[0], item[1]
        endpoint = url_for_endpoint(endpoint)
        if "__USERNAME__" in title and g.get("user"):
            title = title.replace("__USERNAME__", g.user["username"])
        itemdict = {"title": title, "url": endpoint}
        if len(item) > 2:
            itemdict["class"] = "current"
            subtree = item[2]
            next_level = flatten(subtree, level + 1)
        this_level.append(itemdict)
    if len(this_level) == 0:
        return []
    all_levels = [(level, enumerate(this_level))]
    if next_level:
        all_levels.extend(next_level)
    return all_levels


def url_for_endpoint(endpoint: str) -> str:
    """URL for any given endpoint name. Contains logic for
    passing current URL as parameter `next` etc.
    """
    if re.match(r"\w+(\.\w+)+$", endpoint):
        if endpoint in ("auth.login", "auth.register"):
            if request.endpoint not in ("auth.login", "auth.register"):
                next_url = request.url
            else:
                next_url = request.args.get("next")
            endpoint = url_for(endpoint, next=next_url)
        else:
            endpoint = url_for(endpoint)
    return endpoint


def prune(tree: NavigationTree, current: str) -> tuple[NavigationTree, bool]:
    """Return pruned `navigation_tree` that contain only items relevant for
    the `current` endpoint. Returned bool indicates if any of the items in
    this tree (or it's subtrees) is an exact match.
    """
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
            if subtree:
                nav_item.append(subtree)
            else:
                nav_item.append([])
        pruned.append(nav_item)
    return pruned, any_match
