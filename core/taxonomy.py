import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from core.keywords import matches

EMBEDDED_PATH = Path(__file__).resolve().parent.parent / "assets" / "taxonomy.json"


@dataclass(frozen=True)
class Node:
    name: str
    terms: tuple[str, ...]
    children: tuple["Node", ...] = ()


@dataclass(frozen=True)
class Taxonomy:
    areas: tuple[Node, ...]


@dataclass(frozen=True)
class TaxonomyPath:
    area: str
    topic: str | None = None
    subtopic: str | None = None

    @property
    def name(self) -> str:
        return self.subtopic or self.topic or self.area

    @property
    def parent(self) -> "TaxonomyPath | None":
        if self.subtopic is not None:
            return TaxonomyPath(self.area, self.topic)
        if self.topic is not None:
            return TaxonomyPath(self.area)
        return None

    def child(self, name: str) -> "TaxonomyPath":
        if self.topic is None:
            return TaxonomyPath(self.area, name)
        return TaxonomyPath(self.area, self.topic, name)


def parse(data: dict) -> Taxonomy:
    return Taxonomy(tuple(_node(area, "topicos", "subtopicos") for area in data["areas"]))


def load(path: Path) -> Taxonomy:
    return parse(json.loads(path.read_text(encoding="utf-8")))


@lru_cache(maxsize=1)
def embedded() -> Taxonomy:
    return load(EMBEDDED_PATH)


def classify(taxonomy: Taxonomy, note: str) -> list[TaxonomyPath]:
    # Cada caminho vai até o nó mais profundo com evidência no texto; um
    # termo de subtópico aciona o tópico e a área que o contêm mesmo que os
    # termos deles não apareçam.
    paths: list[TaxonomyPath] = []
    for area in taxonomy.areas:
        within_area: list[TaxonomyPath] = []
        for topic in area.children:
            subtopics = [child.name for child in topic.children if _triggered(child, note)]
            if subtopics:
                within_area += [TaxonomyPath(area.name, topic.name, name) for name in subtopics]
            elif _triggered(topic, note):
                within_area.append(TaxonomyPath(area.name, topic.name))
        if not within_area and _triggered(area, note):
            within_area.append(TaxonomyPath(area.name))
        paths += within_area
    return paths


def children_of(taxonomy: Taxonomy, parent: TaxonomyPath | None) -> tuple[Node, ...]:
    if parent is None:
        return taxonomy.areas
    area = _named(taxonomy.areas, parent.area)
    if parent.topic is None:
        return area.children
    topic = _named(area.children, parent.topic)
    return () if parent.subtopic is not None else topic.children


def _node(raw: dict, *child_keys: str) -> Node:
    children: tuple[Node, ...] = ()
    if child_keys:
        children = tuple(_node(child, *child_keys[1:]) for child in raw.get(child_keys[0], []))
    return Node(raw["nome"], tuple(raw["termos"]), children)


def _triggered(node: Node, note: str) -> bool:
    return any(matches(term, note) for term in node.terms)


def _named(nodes: tuple[Node, ...], name: str) -> Node:
    return next(node for node in nodes if node.name == name)
