# SnapNote

## O que é

SnapNote é um desafio acadêmico da FIAP em parceria com uma fabricante de celulares. É um aplicativo Android que guarda anotações de texto dentro dos metadados da própria foto (o campo EXIF do arquivo JPEG) e permite buscá-las depois pelo texto ou por palavras-chave.

Como a anotação fica gravada no arquivo, ela viaja junto com a foto: copiar a imagem para outro aparelho ou compartilhá-la leva a anotação junto, e desinstalar o aplicativo não a apaga. As fotos ficam na pasta `DCIM/SnapNote` do celular, visíveis também na galeria nativa.

## Como rodar no computador

A versão de computador serve para desenvolvimento. Câmera e ditado de voz só funcionam no Android: no computador o preview mostra um aviso de câmera indisponível, o obturador não captura e o microfone informa que o reconhecimento de voz não está disponível.

Com Python 3.10:

```bash
python3.10 -m venv .venv-desktop
source .venv-desktop/bin/activate
pip install -r requirements.txt
pip install kivy==2.3.1 kivymd==1.2.0 camera4kivy==0.3.3 gestures4kivy==0.1.4
python main.py
```

Os dados ficam no diretório de dados do usuário do Kivy; no Linux, `~/.config/snapnote/`, com as fotos em `DCIM/SnapNote/`. Para ver a galeria com conteúdo, copie arquivos JPEG para essa pasta e toque em reconstruir índice na tela de galeria.

## Como usar no celular

O aplicativo abre na câmera. Na primeira vez, ele pede permissão para usar a câmera e para acessar as fotos do aparelho.

**Tirar uma foto.** Toque no botão redondo no centro da barra inferior. A foto é salva na hora, sem anotação, e um painel flutuante aparece sobre o preview com a miniatura da foto e uma linha de ícones. Nele, o ícone dourado do cérebro, à direita, abre um painel de anotação sobre a própria câmera, e a lixeira apaga a foto recém-tirada, após confirmação. Tocar fora do painel o fecha; a foto continua salva. O ícone de raio na barra superior liga e desliga o flash; o ícone de setas circulares, à direita do obturador, troca entre a câmera traseira e a frontal. A tela de câmera é um protótipo de interface: os demais ícones da barra superior e do painel (compartilhar e editar), os controles de zoom, os modos (Noite, Retrato, Vídeo e outros) e o ícone sobre o preview são apenas decorativos e mostram um aviso ao serem tocados.

**Escrever ou ditar a anotação.** O painel de anotação, o mesmo na câmera e na edição pela galeria, tem um campo de texto. Escreva a anotação ou toque no microfone e fale; na primeira vez o aplicativo pede permissão para usar o microfone. O texto reconhecido substitui o conteúdo do campo. Se já houver texto, o aplicativo pergunta antes de substituir. Toque em Salvar para gravar a anotação na foto ou em Cancelar para voltar sem alterar nada. Salvar com o campo vazio deixa a foto sem anotação.

**Buscar por texto.** A miniatura no canto inferior esquerdo da câmera abre a galeria. Digite no campo de busca no topo: a lista é filtrada enquanto você escreve, sem diferenciar maiúsculas de minúsculas nem acentos. Buscar `farmacia` encontra `Farmácia`.

**Cadastrar palavras-chave e ver as fotos agrupadas.** Na galeria, toque no ícone de etiquetas na barra superior. Use o botão de mais para cadastrar um termo, toque em um termo para editá-lo ou na lixeira para removê-lo. Toda foto cuja anotação contém a palavra inteira entra no grupo daquele termo: `recibo` agrupa "recibo da farmácia", mas não "recibos". De volta à galeria, cada grupo com fotos aparece como uma pasta acima da grade; toque nela para ver só as fotos daquele grupo e use a seta para voltar. As pastas são apenas uma forma de ver as fotos: nada é copiado nem movido no aparelho.

**Visualizar uma foto com sua anotação.** Toque em uma miniatura para abrir a foto em tela cheia. Na barra flutuante inferior, o ícone de informação mostra a anotação, o nome do arquivo e a data da captura; tocar de novo, ou fora do cartão, o oculta. O lápis dentro desse cartão abre o painel de anotação para edição, e a lixeira da barra exclui a foto, com confirmação. Favoritar, editar e compartilhar na barra são decorativos.

Se as fotos e a galeria ficarem fora de sincronia, por exemplo depois de reinstalar o aplicativo, toque no ícone de reconstruir índice na barra da galeria: ele relê todas as fotos da pasta `DCIM/SnapNote` e refaz os grupos.
