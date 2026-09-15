from pathlib import Path

from core import exif_store
from core.index import TaxonomyGroup, open_index
from core.taxonomy import EMBEDDED_PATH, TaxonomyPath, children_of, classify, embedded, load, parse
from tests.conftest import MakeJpeg

SMALL = parse({
    "areas": [
        {
            "nome": "Cálculo",
            "termos": ["cálculo"],
            "topicos": [
                {
                    "nome": "Derivadas",
                    "termos": ["derivada", "derivadas"],
                    "subtopicos": [{"nome": "Regra da cadeia", "termos": ["regra da cadeia"]}],
                },
                {"nome": "Integrais", "termos": ["integral"], "subtopicos": []},
            ],
        },
        {
            "nome": "Compras",
            "termos": ["compra"],
            "topicos": [{"nome": "Farmácia", "termos": ["farmácia"], "subtopicos": []}],
        },
    ]
})


def test_full_three_level_path() -> None:
    assert classify(SMALL, "usei a Regra da Cadeia na prova") == [
        TaxonomyPath("Cálculo", "Derivadas", "Regra da cadeia")
    ]


def test_partial_path_stops_at_topic() -> None:
    assert classify(SMALL, "estudando derivadas hoje") == [TaxonomyPath("Cálculo", "Derivadas")]


def test_area_alone_when_only_its_term_appears() -> None:
    assert classify(SMALL, "prova de cálculo amanhã") == [TaxonomyPath("Cálculo")]


def test_deepest_node_wins_over_its_parents() -> None:
    assert classify(SMALL, "cálculo: derivadas pela regra da cadeia") == [
        TaxonomyPath("Cálculo", "Derivadas", "Regra da cadeia")
    ]


def test_photo_can_belong_to_two_paths() -> None:
    assert classify(SMALL, "recibo da farmacia e uma integral") == [
        TaxonomyPath("Cálculo", "Integrais"),
        TaxonomyPath("Compras", "Farmácia"),
    ]


def test_text_without_terms_is_unclassified() -> None:
    assert classify(SMALL, "foto do gato no sofá") == []
    assert classify(SMALL, "derivadamente") == []


def test_children_follow_taxonomy_order() -> None:
    assert [node.name for node in children_of(SMALL, None)] == ["Cálculo", "Compras"]
    assert [node.name for node in children_of(SMALL, TaxonomyPath("Cálculo"))] == ["Derivadas", "Integrais"]
    assert children_of(SMALL, TaxonomyPath("Cálculo", "Derivadas", "Regra da cadeia")) == ()


def test_path_navigation_helpers() -> None:
    leaf = TaxonomyPath("Cálculo", "Derivadas", "Regra da cadeia")
    assert leaf.name == "Regra da cadeia" and leaf.parent == TaxonomyPath("Cálculo", "Derivadas")
    assert leaf.parent.parent == TaxonomyPath("Cálculo") and TaxonomyPath("Cálculo").parent is None
    assert TaxonomyPath("Cálculo").child("Derivadas").child("Regra da cadeia") == leaf


def test_embedded_taxonomy_loads_with_three_levels() -> None:
    taxonomy = load(EMBEDDED_PATH)
    assert taxonomy == embedded()
    assert classify(taxonomy, "recibo da farmácia") == [
        TaxonomyPath("Documentos", "Fiscais", "Recibos"),
        TaxonomyPath("Compras", "Farmácia"),
    ]


def test_index_stores_paths_and_recalculates_after_editing(tmp_path: Path, make_jpeg: MakeJpeg) -> None:
    photo = make_jpeg("fotos/a.jpg", note="anotações de derivadas")

    with open_index(tmp_path / "index.db", SMALL) as index:
        index.upsert(photo)
        assert index.classified(TaxonomyPath("Cálculo", "Derivadas")) == [index.all_photos()[0]]
        assert index.taxonomy_children(None) == [TaxonomyGroup(TaxonomyPath("Cálculo"), 1)]

        exif_store.write_note(photo, "compra na farmácia")
        index.upsert(photo)
        assert index.classified(TaxonomyPath("Cálculo", "Derivadas")) == []
        assert index.taxonomy_children(None) == [TaxonomyGroup(TaxonomyPath("Compras"), 1)]
        assert index.taxonomy_children(TaxonomyPath("Compras")) == [
            TaxonomyGroup(TaxonomyPath("Compras", "Farmácia"), 1)
        ]


def test_rebuild_classifies_every_photo_and_counts_distinct_photos(tmp_path: Path, make_jpeg: MakeJpeg) -> None:
    make_jpeg("fotos/a.jpg", note="regra da cadeia e integral")
    make_jpeg("fotos/b.jpg", note="prova de cálculo")
    make_jpeg("fotos/c.jpg", note="sem classificação")

    with open_index(tmp_path / "index.db", SMALL) as index:
        index.rebuild(tmp_path / "fotos")

        assert index.taxonomy_children(None) == [TaxonomyGroup(TaxonomyPath("Cálculo"), 2)]
        assert index.taxonomy_children(TaxonomyPath("Cálculo")) == [
            TaxonomyGroup(TaxonomyPath("Cálculo", "Derivadas"), 1),
            TaxonomyGroup(TaxonomyPath("Cálculo", "Integrais"), 1),
        ]
        assert len(index.classified(TaxonomyPath("Cálculo"))) == 2
        assert [Path(p.path).name for p in index.classified(TaxonomyPath("Cálculo", "Derivadas", "Regra da cadeia"))] == ["a.jpg"]
