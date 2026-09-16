import logging
import shutil
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from pathlib import Path

import library
import notes
from core import exif_store

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class DemoPhoto:
    file_name: str
    note: str
    days_ago: int
    taken_at: time


# Os dias contam a partir da data da carga, nunca hoje nem ontem, para que a
# galeria mostre várias seções de data em vez de só "Hoje" e "Ontem".
DEMO_PHOTOS = (
    DemoPhoto("lousa-regra-cadeia.jpg", "Aula de regra da cadeia, derivada de função composta", 2, time(10, 15)),
    DemoPhoto("caderno-integrais.jpg", "Exercícios de integração por partes", 2, time(11, 40)),
    DemoPhoto("lousa-limites.jpg", "Revisão de limites laterais e continuidade", 5, time(9, 20)),
    DemoPhoto("quadro-matrizes.jpg", "Cálculo de matriz inversa por escalonamento", 9, time(14, 5)),
    DemoPhoto("caderno-vetores.jpg", "Anotações sobre autovalores e autovetores", 9, time(15, 30)),
    DemoPhoto("lista-mercado.jpg", "Lista de compras do mercado", 13, time(18, 45)),
    DemoPhoto("lousa-newton.jpg", "Leis de Newton aplicadas a plano inclinado", 17, time(10, 0)),
    DemoPhoto("circuito-eletrico.jpg", "Exercício de lei de Ohm em circuito série", 17, time(11, 20)),
    DemoPhoto("reuniao-quadro.jpg", "Brainstorm da reunião de planejamento", 22, time(16, 10)),
    DemoPhoto("cronograma-projeto.jpg", "Cronograma de entrega do projeto", 22, time(17, 0)),
    DemoPhoto("quadro-sql.jpg", "Modelagem com inner join entre tabelas", 27, time(13, 30)),
    DemoPhoto("diagrama-arvore.jpg", "Estrutura de árvore binária de busca", 33, time(9, 50)),
    DemoPhoto("nota-fiscal.jpg", "Nota fiscal da compra de livros", 41, time(12, 20)),
    DemoPhoto("recibo-papel.jpg", "Recibo do material de estudo", 41, time(12, 35)),
)


def load_demo(
    assets_dir: Path, photos_dir: Path, index_path: Path, marker_path: Path, today: date | None = None
) -> bool:
    if marker_path.exists():
        return False
    today = today or date.today()
    for photo in DEMO_PHOTOS:
        try:
            _load_photo(photo, assets_dir, photos_dir, index_path, today)
        except Exception:
            log.exception("foto de demonstração %s não carregada", photo.file_name)
    marker_path.write_text(datetime.now().isoformat())
    return True


def _load_photo(photo: DemoPhoto, assets_dir: Path, photos_dir: Path, index_path: Path, today: date) -> None:
    destination = photos_dir / photo.file_name
    # Um arquivo que sobrou de uma instalação anterior pode ter sido editado
    # pelo usuário; ele só volta ao índice.
    if destination.exists():
        library.index_photo(destination, index_path)
        return
    try:
        shutil.copyfile(assets_dir / photo.file_name, destination)
        taken_at = datetime.combine(today - timedelta(days=photo.days_ago), photo.taken_at)
        exif_store.write_capture_time(destination, taken_at)
        notes.save_note(destination, photo.note, index_path)
    except Exception:
        destination.unlink(missing_ok=True)
        raise
