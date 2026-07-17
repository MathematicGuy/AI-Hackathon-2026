from __future__ import annotations

from html.parser import HTMLParser
from typing import Iterable, Optional

from .utils import clean_text


class Node:
    __slots__ = ("tag", "attrs", "children", "parent", "data")

    def __init__(self, tag: str = "#document", attrs: Optional[dict[str, str]] = None, parent: "Node | None" = None):
        self.tag = tag.lower()
        self.attrs = {str(k).lower(): (v if v is not None else "") for k, v in (attrs or {}).items()}
        self.children: list[Node] = []
        self.parent = parent
        self.data: str = ""

    def add(self, node: "Node") -> None:
        node.parent = self
        self.children.append(node)

    def text_content(self) -> str:
        if self.tag == "#text":
            return self.data
        return " ".join(child.text_content() for child in self.children)

    def descendants(self, include_self: bool = False) -> Iterable["Node"]:
        if include_self:
            yield self
        for child in self.children:
            if child.tag == "#text":
                continue
            yield child
            yield from child.descendants()

    def first(self, selector: str) -> "Node | None":
        return next(iter(select_nodes(self, selector)), None)

    def select(self, selector: str) -> list["Node"]:
        return list(select_nodes(self, selector))


class _TreeParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.root = Node()
        self.stack = [self.root]

    @property
    def current(self) -> Node:
        return self.stack[-1]

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        node = Node(tag, dict(attrs), self.current)
        self.current.add(node)
        if tag.lower() not in {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}:
            self.stack.append(node)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.current.add(Node(tag, dict(attrs), self.current))

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        for index in range(len(self.stack) - 1, 0, -1):
            if self.stack[index].tag == tag:
                del self.stack[index:]
                return

    def handle_data(self, data: str) -> None:
        if data:
            self.current.add(Node("#text", parent=self.current))
            self.current.children[-1].data = data

    def handle_comment(self, data: str) -> None:
        return


def parse_html(value: str | bytes) -> Node:
    if isinstance(value, bytes):
        value = value.decode("utf-8", errors="replace")
    parser = _TreeParser()
    parser.feed(value)
    parser.close()
    return parser.root


def node_text(node: Node | None) -> str:
    return clean_text(node.text_content() if node else "")


def _split_selector(selector: str) -> list[str]:
    tokens: list[str] = []
    current: list[str] = []
    bracket = 0
    for char in selector.strip():
        if char == "[":
            bracket += 1
        elif char == "]":
            bracket = max(0, bracket - 1)
        if char.isspace() and bracket == 0:
            if current:
                tokens.append("".join(current))
                current = []
        else:
            current.append(char)
    if current:
        tokens.append("".join(current))
    return tokens


def _match_token(node: Node, token: str) -> bool:
    if node.tag == "#text":
        return False
    attrs = dict(node.attrs)
    # Attribute selectors (presence or exact value; enough for observed DOM).
    attr_matches = __import__("re").findall(r"\[([^\]=~^$*]+)(?:([~^$*]?=)[\"']?([^\] \"']+)[\"']?)?\]", token)
    for name, operator, expected in attr_matches:
        name = name.strip().lower()
        actual = attrs.get(name)
        if actual is None:
            return False
        if operator:
            expected = expected.strip()
            if operator == "=" and actual != expected:
                return False
            if operator == "^=" and not actual.startswith(expected):
                return False
            if operator == "$=" and not actual.endswith(expected):
                return False
            if operator == "*=" and expected not in actual:
                return False
            if operator == "~=" and expected not in actual.split():
                return False
    token = __import__("re").sub(r"\[[^\]]+\]", "", token)
    tag_match = __import__("re").match(r"^[A-Za-z][\w-]*|^\*", token)
    if tag_match and tag_match.group(0) not in ("*", node.tag):
        return False
    for ident in __import__("re").findall(r"\.([\w-]+)", token):
        if ident not in attrs.get("class", "").split():
            return False
    ident = __import__("re").search(r"#([\w-]+)", token)
    if ident and attrs.get("id") != ident.group(1):
        return False
    return True


def _matches_chain(node: Node, tokens: list[str]) -> bool:
    if not tokens or not _match_token(node, tokens[-1]):
        return False
    ancestor = node.parent
    for token in reversed(tokens[:-1]):
        while ancestor is not None and not _match_token(ancestor, token):
            ancestor = ancestor.parent
        if ancestor is None:
            return False
        ancestor = ancestor.parent
    return True


def select_nodes(root: Node, selector: str) -> Iterable[Node]:
    tokens = _split_selector(selector)
    if not tokens:
        return
    for node in root.descendants():
        if _matches_chain(node, tokens):
            yield node


def attr(node: Node | None, name: str, default: str | None = None) -> str | None:
    if node is None:
        return default
    return node.attrs.get(name.lower(), default)
