# SnapNote

Aplicativo Android que guarda anotações de texto junto das fotos, gravadas nos metadados EXIF da própria imagem. Desenvolvido como desafio acadêmico da FIAP em parceria com uma fabricante de celulares.

## 1. Descrição

A premissa central do SnapNote é que o arquivo de imagem é autossuficiente e portátil. A anotação é gravada no campo `UserComment` do EXIF do próprio JPEG, em codificação UNICODE (UTF-16), o que preserva acentos e cedilha. Copiar a foto para outro aparelho, enviá-la por qualquer meio ou desinstalar o aplicativo não separa a anotação da imagem: ela viaja com o arquivo.

As fotos ficam na pasta pública `DCIM/SnapNote/` do armazenamento compartilhado do Android, fora do diretório privado do aplicativo, e por isso sobrevivem à desinstalação. O aplicativo notifica o MediaStore a cada gravação, reescrita ou exclusão, de modo que a galeria nativa do aparelho reflita o estado dos arquivos.

O índice SQLite existe apenas como cache de busca. Ele guarda, para cada foto, o caminho e o texto da anotação, além das palavras-chave e dos vínculos entre elas e as fotos. O índice fica no armazenamento privado do aplicativo, é descartável e pode ser integralmente reconstruído a partir dos arquivos: a operação de reconstrução apaga as tabelas e reindexa a pasta de fotos lendo o EXIF de cada imagem.

## 2. Funcionalidades

- Captura de fotos com a câmera do aparelho, com controle de flash (ligado ou desligado) e troca entre câmeras.
- Anotação por texto ou por ditado de voz, usando o reconhecedor de fala nativo do Android em português do Brasil.
- Gravação da anotação no EXIF da imagem. Salvar com o campo vazio deixa a foto sem anotação; apagar o texto de uma anotação existente remove o campo do arquivo.
- Busca por texto na anotação, ignorando maiúsculas e acentos: buscar `farmacia` encontra `Farmácia`.
- Palavras-chave cadastradas pelo usuário. Uma foto pertence ao grupo de uma palavra-chave quando a anotação contém aquela palavra inteira, também sem distinguir maiúsculas e acentos. Os vínculos são recalculados ao salvar uma anotação, ao cadastrar, editar ou remover uma palavra-chave e ao reconstruir o índice.
- Galeria própria com os grupos exibidos como pastas, grade de miniaturas carregadas em segundo plano e visualizador em tela cheia com painel deslizante de informações (anotação, nome do arquivo e data de captura).
- Edição e exclusão de fotos a partir do visualizador.
- Reconstrução do índice sob demanda, com confirmação e indicação de progresso.

O agrupamento é virtual: nenhuma pasta é criada no armazenamento e nenhum arquivo é duplicado ou movido. O vínculo entre foto e palavra-chave vive apenas no índice.

A tela de câmera é um protótipo de interface. Apenas o obturador, o flash, a miniatura da última foto e o botão de inverter câmera são funcionais. Os demais ícones da barra superior, os chips de zoom, o carrossel de modos e o ícone flutuante sobre o preview são decorativos; ao serem tocados, exibem um aviso de que não fazem parte do escopo do protótipo.

## 3. Arquitetura

O código é dividido em três camadas.

- `core/` contém a lógica de domínio, sem qualquer dependência de interface ou de Android:
  - `exif_store.py` grava, lê e remove a anotação no EXIF (piexif).
  - `index.py` mantém o índice SQLite: fotos, palavras-chave e vínculos, incluindo a reconstrução a partir de uma pasta.
  - `search.py` faz a busca por substring sobre texto normalizado.
  - `keywords.py` implementa o casamento por palavra inteira.
  - `text.py` concentra a normalização de acentos e maiúsculas.
- Módulos de caso de uso na raiz, que compõem o núcleo com o sistema de arquivos e a plataforma: `notes.py` (salvar e descartar anotações), `library.py` (listagem, busca, grupos, palavras-chave, exclusão e reconstrução), `storage.py` (resolução de caminhos por plataforma), `media_store.py` (notificação ao MediaStore), `speech.py` (ponte com o SpeechRecognizer), `permissions.py` (permissões em tempo de execução) e `thumbnails.py` (miniaturas com orientação corrigida).
- `ui/` contém as telas em Kivy/KivyMD, que apenas chamam os casos de uso. Cores, medidas e fontes ficam centralizadas em `ui/theme.py`; widgets compartilhados em `ui/widgets.py`.

O núcleo e os casos de uso são executados e testados em desktop, sem Android. Os módulos de plataforma degradam de forma explícita fora do Android: a notificação ao MediaStore vira uma operação nula e o ditado informa que o reconhecimento não está disponível.

## 4. Tecnologias

- Python 3.10
- Kivy 2.3 e KivyMD 1.2.0 (interface)
- camera4kivy e gestures4kivy (câmera via CameraX)
- piexif (leitura e escrita de EXIF)
- Pillow (miniaturas)
- SQLite, pelo módulo `sqlite3` da biblioteca padrão (índice)
- SpeechRecognizer nativo do Android, acessado via pyjnius (ditado)
- Buildozer e python-for-android (empacotamento do APK)

## 5. Como executar em desktop

A execução em desktop serve ao desenvolvimento das telas e da lógica. Câmera e ditado de voz não funcionam fora do Android: o preview exibe a mensagem de erro do camera4kivy por falta de provedor de câmera, o obturador não captura e o botão de microfone informa que o reconhecimento de voz não está disponível. O flash apenas alterna o estado visual.

As dependências de interface não constam de `requirements.txt`, que cobre apenas os testes. As versões abaixo foram as usadas no desenvolvimento.

```bash
python3.10 -m venv .venv-desktop
source .venv-desktop/bin/activate
pip install -r requirements.txt
pip install kivy==2.3.1 kivymd==1.2.0 camera4kivy==0.3.3 gestures4kivy==0.1.4
python main.py
```

A janela abre em proporção de celular (360 x 800). Os dados ficam no diretório de dados do usuário definido pelo Kivy; no Linux, `~/.config/snapnote/`, com as fotos em `DCIM/SnapNote/` e o índice em `snapnote.db`. Para popular a galeria em desktop, copie arquivos JPEG para essa pasta e use a reconstrução do índice na tela de galeria.

## 6. Como gerar o APK

Requisitos de ambiente:

- Linux ou WSL2 com Ubuntu 22.04
- Python 3.10
- JDK 17
- Dependências de sistema do Buildozer, conforme a documentação oficial:

```bash
sudo apt install -y git zip unzip openjdk-17-jdk python3-pip autoconf libtool pkg-config zlib1g-dev libncurses5-dev libncursesw5-dev libtinfo5 cmake libffi-dev libssl-dev
```

Versões travadas no ambiente de build e o motivo de cada uma:

- `cython==0.29.36`: versões 3.x quebram a compilação do Kivy no python-for-android.
- `kivymd==1.2.0`: versão estável compatível com Kivy 2.3.x; a linha 2.x não é usada.
- `pip==24.0` e `virtualenv==20.26.6`: versões mais recentes geram um ambiente interno corrompido no python-for-android, com erro de importação no pip.
- `buildozer==1.5.0`: versão usada no projeto.

Preparação do ambiente:

```bash
python3.10 -m venv .venv
source .venv/bin/activate
pip install pip==24.0 virtualenv==20.26.6 cython==0.29.36 buildozer==1.5.0
```

Geração do APK:

```bash
buildozer android debug
```

A primeira execução baixa o SDK e o NDK do Android e compila o Python e o Kivy para arm64, o que leva bastante tempo. O APK é gerado em `bin/snapnote-0.1-arm64-v8a-debug.apk`.

Para instalar, abrir e acompanhar o log com o aparelho conectado por USB e a depuração ativada:

```bash
buildozer android debug deploy run logcat
```

Configuração relevante em `buildozer.spec`:

- `android.api = 34`, `android.minapi = 21`, `android.archs = arm64-v8a`.
- Permissões: `CAMERA`, `RECORD_AUDIO`, `READ_MEDIA_IMAGES` e `READ_MEDIA_VISUAL_USER_SELECTED` (Android 13 e 14), `READ_EXTERNAL_STORAGE` (até a API 32) e `WRITE_EXTERNAL_STORAGE` (até a API 28). A permissão de armazenamento pedida em tempo de execução é escolhida conforme a versão do Android.
- `p4a.hook = camerax_provider/gradle_options.py`: o diretório `camerax_provider/`, distribuído pelo autor do camera4kivy, adiciona as dependências Gradle do CameraX e o código Java do provedor.
- `android.extra_manifest_xml = manifest/speech_queries.xml`: declara a visibilidade do serviço de reconhecimento de voz, exigida a partir do Android 11 para que o SpeechRecognizer encontre o reconhecedor do sistema.

O aparelho usado nos testes foi um Moto G34 com Android 14. Em aparelhos com Android 10, a gravação em `DCIM/SnapNote/` por caminho de arquivo não é suportada pelo modelo de armazenamento com escopo; a versão 11 ou superior é necessária.

## 7. Como executar os testes

Os testes não dependem de Kivy nem de Android. Com um ambiente contendo apenas `requirements.txt`:

```bash
python3.10 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m pytest
```

A suíte tem 57 testes e gera as próprias imagens JPEG em diretórios temporários. Cobertura por módulo:

- `test_exif_store.py`: ciclo de escrita e leitura com acentos, prefixo de codificação UNICODE, preservação do restante do EXIF, remoção da anotação, arquivo inexistente, formato não suportado e `UserComment` em codificação indefinida.
- `test_index.py`: inserção e atualização, remoção, persistência entre sessões, reconstrução a partir da pasta sem descer em subpastas e listagem de fotos com e sem anotação.
- `test_search.py`: normalização e busca ignorando acentos e maiúsculas.
- `test_keywords.py`: casamento por palavra inteira, ignorando acentos e maiúsculas, recálculo dos vínculos ao cadastrar, renomear e remover palavras-chave, ao salvar anotações e ao reconstruir o índice, unicidade das palavras-chave.
- `test_notes.py` e `test_library.py`: casos de uso de salvar, descartar, listar, filtrar por grupo e termo, excluir, reconstruir e obter a data de captura.
- `test_thumbnails.py`: redução com proporção preservada e aplicação da orientação EXIF.
- `test_speech.py`: degradação da ponte de voz fora do Android.
