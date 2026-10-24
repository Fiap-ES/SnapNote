# SnapNote

[![Python](https://img.shields.io/badge/Python-3.10-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Kivy](https://img.shields.io/badge/Kivy-2.3.1-4584B6)](https://kivy.org/)
[![KivyMD](https://img.shields.io/badge/KivyMD-1.2.0-0F80E6)](https://kivymd.readthedocs.io/)
[![Buildozer](https://img.shields.io/badge/Buildozer-Android-3DDC84?logo=android&logoColor=white)](https://github.com/kivy/buildozer)
[![Google Gemini](https://img.shields.io/badge/AI-Google%20Gemini-4285F4?logo=google&logoColor=white)](https://ai.google.dev/)
[![ML Kit](https://img.shields.io/badge/OCR-Google%20ML%20Kit-FFCA28?logo=firebase&logoColor=black)](https://developers.google.com/ml-kit)
[![YouTube](https://img.shields.io/badge/YouTube-Vídeo%20Pitch%20%26%20Demo-FF0000?logo=youtube&logoColor=white)](https://youtu.be/0CPvpbiuu4Q?is=o4TaOXjgMaykryGK)

SnapNote é um aplicativo móvel Android (com suporte a ambiente desktop para desenvolvimento) desenvolvido como desafio acadêmico da **FIAP** em parceria com uma fabricante de dispositivos móveis.

O diferencial central do SnapNote é **armazenar anotações de texto e metadados diretamente dentro do próprio arquivo da foto** (no cabeçalho EXIF do JPEG, via campo `UserComment` em UTF-16BE). Dessa forma, a anotação é inseparável da imagem: copiar, compartilhar ou mover o arquivo preserva as notas, e reinstalar o aplicativo não apaga o histórico.

---

## 👥 Integrantes do Grupo

| Nome | RM |
| :--- | :--- |
| **Bruno Guilherme Gonçalves de Oliveira** | RM573697 |
| **Gabriel Cardoso de Sá Finzetto** | RM571846 |
| **Gabriel Luna Maia** | RM570982 |
| **João Lucas Magordo Rodrigues** | RM572419 |
| **Murilo Vieira dos Reis** | RM573764 |

---

## 🎬 Vídeo de Apresentação e Demonstração

Para a banca avaliadora do Challenge, foi produzido um vídeo completo de apresentação que une a narrativa (storytelling) do problema com a demonstração prática das funcionalidades do aplicativo em execução:

📺 **Assista no YouTube:** [SnapNote - Demonstração e Storytelling (Challenge FIAP)](https://youtu.be/0CPvpbiuu4Q?is=o4TaOXjgMaykryGK)

---

## 🌟 Principais Recursos

- **Persistência EXIF Portável**: Anotações gravadas no campo `UserComment` (UTF-16BE) e data de captura em `DateTimeOriginal`. Fotos salvas em `DCIM/SnapNote`, integradas à galeria nativa do aparelho via `MediaScannerConnection`.
- **Sugestões Inteligentes de Anotação (Dual Pipeline)**:
  - **Google Gemini Vision**: Envia uma versão reduzida em memória (máx. 1024 px) para gerar uma descrição concisa e contextual em português.
  - **Google ML Kit OCR (Offline Fallback)**: Reconhecimento de texto local on-device em caso de ausência de rede, chave não configurada ou esgotamento do tempo limite.
- **Ditado e Busca por Voz**: Reconhecimento de fala integrado ao Android (`SpeechRecognizer`) com suporte a busca rápida na galeria e ditado de anotações com diálogo de confirmação.
- **Classificação Inteligente & Taxonomia Hierárquica**:
  - Classificação automática por taxonomia acadêmica (`assets/taxonomy.json` com Áreas, Tópicos e Subtópicos em Cálculo, Álgebra Linear, Física, Programação, etc.).
  - Gestão de palavras-chave personalizadas com agrupamento automático em pastas virtuais.
- **Galeria com Navegação Avançada**:
  - Aba **Fotos**: visualização cronológica agrupada por seções de data (*Hoje*, *Ontem*, data por extenso).
  - Aba **Pastas**: álbuns por palavras-chave e navegação hierárquica por árvore taxonômica.
  - Busca textual em tempo real, sem distinção de acentos ou maiúsculas/minúsculas.
- **Visualizador em Tela Cheia (PhotoPager)**:
  - Transição de fotos por deslizamento (swipe) com animações fluidas e mola de arraste.
  - Tira horizontal de miniaturas sincronizada (`ThumbnailStrip`).
  - Ocultação de barras com um toque (modo imersivo) e cartão de detalhes do metadados.
- **Desempenho Otimizado**: Carregamento assíncrono de miniaturas com cache LRU em `ThreadPoolExecutor`, decodificação de rotação EXIF (`exif_transpose`) e indexação SQLite local com remoção em cascata (`ON DELETE CASCADE`).

---

## 🏗️ Arquitetura do Projeto

O projeto adota uma arquitetura em camadas com separação clara de responsabilidades:

```
SnapNote/
├── core/                        # Camada de Domínio e Dados Pura (sem dependências de GUI)
│   ├── exif_store.py            # Leitura/escrita de EXIF (UserComment UTF-16BE e DateTimeOriginal)
│   ├── index.py                 # Banco de dados SQLite local, esquemas, índices e migrações
│   ├── keywords.py              # Correspondência de termos inteiros por Regex
│   ├── search.py                # Busca normalizada sem sensibilidade a acentos/caixa
│   ├── taxonomy.py              # Parser, árvore hierárquica e classificador de taxonomia
│   └── text.py                  # Normalização Unicode NFKD
│
├── ui/                          # Camada de Apresentação (Kivy / KivyMD)
│   ├── camera_screen.py         # Tela de câmera, controles de captura e ilha pós-captura
│   ├── gallery_screen.py        # Grade de fotos, alternador Fotos/Pastas e busca
│   ├── detail_screen.py         # Visualizador em tela cheia com metadados e atalhos
│   ├── keywords_screen.py       # Gestão de palavras-chave (cadastro, edição, remoção)
│   ├── settings_screen.py       # Configuração de tempo limite da IA Gemini
│   ├── photo_pager.py           # Carrossel de fotos com detecção de gestos de arraste
│   ├── note_panel.py            # Painel flutuante de anotação
│   ├── note_editor.py           # Campo de edição com suporte a ditado
│   ├── dictation.py             # Comportamento de entrada por voz na UI
│   ├── thumbnail_loader.py      # Carregamento concorrente e cache de miniaturas
│   ├── thumbnail_strip.py       # Tira horizontal deslizante de miniaturas
│   ├── theme.py                 # Paleta visual Dark/Amber, tipografia e métricas
│   ├── dialogs.py               # Diálogos modais (confirmação, progresso, entrada)
│   ├── dates.py                 # Formatação localizada de seções de data
│   └── widgets.py               # Componentes visuais reutilizáveis
│
├── camerax_provider/            # Provedor CameraX Android para integração Camera4Kivy
│   ├── gradle_options.py        # Hook de compilação Gradle para p4a/Buildozer
│   └── camerax_src/             # Implementação Java da ponte com CameraX
│
├── assets/                      # Recursos estáticos
│   ├── demo/                    # Imagens JPEG de demonstração inicial
│   └── taxonomy.json            # Árvore hierárquica acadêmica de áreas e tópicos
│
├── manifest/                    # Configurações do Android Manifest
│   └── speech_queries.xml       # Declaração <queries> para reconhecimento de voz no Android 11+
│
├── tests/                       # Suíte de testes automatizados (pytest)
│   ├── conftest.py              # Fixtures para criação de imagens e bancos efêmeros
│   ├── test_exif_store.py       # Testes de gravação e leitura de metadados EXIF
│   ├── test_index.py            # Testes do índice SQLite e migrações
│   ├── test_taxonomy.py         # Testes de classificação automática
│   ├── test_search.py           # Testes de pesquisa normalizada
│   ├── test_keywords.py         # Testes de correspondência de termos
│   ├── test_vision.py           # Testes do cliente Gemini e fallbacks
│   ├── test_ocr.py              # Testes de OCR via ML Kit com mocks JNI
│   ├── test_speech.py           # Testes de reconhecimento de voz
│   └── ...                      # Testes adicionais de serviços e lógica
│
├── main.py                      # Ponto de entrada do app Kivy e ciclo de vida
├── library.py                   # Casos de uso de consulta e gerenciamento de fotos
├── notes.py                     # Casos de uso de salvamento/remoção de anotações
├── storage.py                   # Resolução de caminhos (Android vs Desktop) e publicação
├── settings.py                  # Armazenamento e validação de configurações locais
├── suggestions.py               # Orquestrador de sugestões (Gemini -> fallback ML Kit)
├── vision.py                    # Integração HTTP com a API Google Gemini Vision
├── ocr.py                       # Integração JNI com Google ML Kit Text Recognition
├── speech.py                    # Integração JNI com Android SpeechRecognizer
├── permissions.py               # Gestão de permissões Android em tempo de execução
├── media_store.py               # Notificação ao Android MediaStore
├── thumbnails.py                # Redimensionamento e orientação de imagens via Pillow
├── demo.py                      # Carga única de fotos de exemplo com anotações e datas
├── buildozer.spec               # Especificação de empacotamento do APK Android
└── requirements.txt             # Dependências Python base
```

---

## ⚙️ Pré-requisitos e Instalação

### Ambiente Desktop (Desenvolvimento)

O modo desktop permite testar toda a navegação, galeria, visualização, taxonomia, busca, configurações e integração com o Gemini.

> [!NOTE]
> Câmera física, OCR via ML Kit e ditado por voz dependem de APIs exclusivas do Android. No desktop, a câmera exibe um aviso de indisponibilidade e os recursos nativos usam fallbacks seguros.

Recomenda-se utilizar **Python 3.10** para paridade com o ambiente do Buildozer.

#### No Linux / macOS:

```bash
# 1. Clonar ou navegar até o diretório do projeto
cd SnapNote

# 2. Criar e ativar o ambiente virtual
python3.10 -m venv .venv
source .venv/bin/activate

# 3. Instalar as dependências base
pip install -r requirements.txt

# 4. Instalar as dependências de interface
pip install kivy==2.3.1 kivymd==1.2.0 camera4kivy==0.3.3 gestures4kivy==0.1.4

# 5. Executar a aplicação
python main.py
```

#### No Windows (PowerShell):

```powershell
# 1. Criar e ativar o ambiente virtual com Python 3.10
py -3.10 -m venv .venv
.venv\Scripts\Activate.ps1

# 2. Instalar as dependências base e dependências gráficas do Kivy
pip install -r requirements.txt
pip install kivy_deps.angle kivy_deps.sdl2 kivy_deps.glew
pip install kivy==2.3.1 kivymd==1.2.0 camera4kivy==0.3.3 gestures4kivy==0.1.4

# 3. Executar a aplicação
python main.py
```

### Localização dos Dados no Desktop

- **Fotos**: salvas na pasta `DCIM/SnapNote/` dentro do diretório de dados do usuário:
  - **Linux**: `~/.config/snapnote/DCIM/SnapNote/`
  - **Windows**: `%APPDATA%\snapnote\DCIM\SnapNote\`
  - **Android**: Armazenamento primário compartilhado `/sdcard/DCIM/SnapNote/`
- **Banco de Dados e Configurações**: `snapnote.db`, `settings.json` e o marcador `demo_loaded` ficam gravados no mesmo diretório de dados.

Na primeira execução, o app carrega automaticamente 14 fotos de demonstração anotadas e datadas a partir de `assets/demo/`.

---

## 🔑 Configuração da Chave do Google Gemini

Ao fotografar, o SnapNote envia a imagem otimizada para o Google Gemini gerar uma sugestão de anotação. A chave de API **nunca** deve ser incluída no controle de versão.

Defina a chave na raiz do projeto em um dos seguintes formatos:

### Opção 1: `.env` (Recomendado para Desktop)
```env
GEMINI_API_KEY=AIzaSy...sua_chave_aqui
```

### Opção 2: `secrets.json` (Obrigatório para Android)
```json
{
  "GEMINI_API_KEY": "AIzaSy...sua_chave_aqui"
}
```

> [!IMPORTANT]
> O Buildozer empacota no APK somente os arquivos cujas extensões constam em `source.include_exts` no `buildozer.spec`. Por padrão, arquivos `.env` **não** são empacotados. Para que a chave funcione no celular, utilize o `secrets.json`. Ambos os arquivos já estão incluídos no `.gitignore`. Trate qualquer APK gerado com a chave embutida como estritamente privado.

### Comportamento sem Chave ou Offline

Se a chave não for informada, se o dispositivo estiver sem internet ou se a requisição estourar o tempo limite (padrão de 15 segundos, ajustável nas configurações):
1. O aplicativo não trava nem interrompe a experiência.
2. O pipeline recorre de forma transparente ao **ML Kit OCR local**, que lê textos impressos ou manuscritos diretamente da foto no próprio aparelho.
3. Nenhuma anotação é gravada sem o clique explícito em **Salvar**.

---

## 📱 Guia de Uso no Celular (Android)

1. **Captura de Fotos**:
   - O aplicativo abre diretamente na câmera.
   - Toque no obturador central para capturar. A foto é salva instantaneamente no álbum público `DCIM/SnapNote`.
   - Um painel flutuante (*ilha*) surge na base com a miniatura, ícone de anotação (cérebro dourado) e exclusão rápida.
   - O ícone superior de raio alterna o flash; o ícone ao lado do obturador inverte entre a câmera traseira e frontal.

2. **Edição e Sugestão de Anotações**:
   - Toque no ícone do cérebro na ilha de captura (ou no lápis de edição na galeria).
   - O campo abre com a sugestão gerada pela IA (Gemini ou OCR local) identificada por um aviso superior.
   - Edite manualmente ou toque no ícone do microfone para **ditar por voz**.
   - Se já houver texto digitado, o aplicativo solicita confirmação antes de sobrescrever com o áudio ditado.
   - Toque em **Salvar** para persistir no EXIF da foto e atualizar o índice local.

3. **Navegação na Galeria**:
   - Toque na miniatura no canto inferior esquerdo da câmera para abrir a galeria.
   - A pílula inferior alterna entre duas visualizações:
     - **Fotos**: grade cronológica com cabeçalhos agrupados por *Hoje*, *Ontem* e datas anteriores.
     - **Pastas**: lista de álbuns categorizados por **Palavras-chave** (ícone de etiqueta) e pela **Taxonomia Acadêmica** (ícone de árvore).
   - Ao tocar em uma pasta da taxonomia, navegue hierarquicamente por *Área* -> *Tópico* -> *Subtópico*.

4. **Busca Textual e por Voz**:
   - Digite no campo superior para filtrar fotos instantaneamente em tempo real.
   - A busca é insensível a maiúsculas/minúsculas e acentuação (`farmacia` encontra `Farmácia`).
   - Toque no microfone ao lado do campo de busca para pesquisar falando.

5. **Gerenciamento de Palavras-Chave**:
   - Na galeria, toque no ícone de etiquetas na barra superior.
   - Adicione novos termos (ex: `recibo`, `aula`, `resumo`), edite termos existentes ou exclua-os.
   - As fotos cujas anotações contiverem a palavra inteira serão vinculadas automaticamente ao respectivo álbum.

6. **Visualizador em Tela Cheia e Carrossel**:
   - Toque em qualquer foto na grade para abri-la no visualizador interativo.
   - Deslize para a esquerda/direita para navegar entre as fotos vizinhas.
   - A tira inferior de miniaturas acompanha a navegação com destaque dourado na foto corrente; toque em qualquer miniatura para saltar diretamente para ela.
   - Toque na foto para ocultar/exibir as barras de navegação (modo imersivo).
   - O ícone `(i)` exibe os detalhes do arquivo: texto da anotação, nome do arquivo e data/hora de captura.

7. **Configurações e Reconstrução do Índice**:
   - Toque no ícone de engrenagem para ajustar o **Tempo limite da descrição por IA** (entre 5 e 60 segundos).
   - Toque no ícone de sincronização na galeria para **reconstruir o índice**, relendo todas as fotos e metadados EXIF da pasta `DCIM/SnapNote`.

---

## 🧪 Testes Automatizados

SnapNote possui uma suíte com **mais de 135 testes automatizados** cobrindo a camada de lógica de negócios, normalização, taxonomia, persistência EXIF, migrações de banco, clientes de IA e mocks de JNI.

Para executar os testes:

```bash
# Executar a suíte de testes do core e serviços
pytest
```

Caso deseje executar testes específicos em ambientes isolados sem bibliotecas gráficas do Kivy instaladas:

```bash
pytest tests/test_exif_store.py tests/test_index.py tests/test_taxonomy.py tests/test_search.py tests/test_vision.py
```

---

## 📦 Como Gerar o Pacote Android (APK)

A compilação do APK para Android é realizada através do **Buildozer** em ambiente Linux (ou via WSL2 no Windows).

### 1. Requisitos do Sistema de Build

- Ubuntu 22.04 LTS (ou equivalente no WSL2)
- Python 3.10+, Git, OpenJDK 17, `zip`, `unzip`, dependências de build do Android SDK/NDK:

```bash
sudo apt update
sudo apt install -y git zip unzip openjdk-17-jdk python3-pip autoconf libtool pkg-config zlib1g-dev libncurses5-dev libncursesw5-dev libtinfo5 cmake libffi-dev libssl-dev
pip install --upgrade buildozer cython virtualenv
```

### 2. Configurações Específicas do Buildozer

O arquivo `buildozer.spec` já está pré-configurado com:
- **API Target**: Android API 34 (Android 14) / Min API 21 (Android 5.0).
- **Arquitetura**: `arm64-v8a`.
- **Permissões Android**: `CAMERA`, `RECORD_AUDIO`, `INTERNET`, `ACCESS_NETWORK_STATE`, além de permissões de armazenamento granulares (`READ_MEDIA_IMAGES` e `READ_MEDIA_VISUAL_USER_SELECTED` para Android 13/14, e legadas para versões anteriores).
- **Hooks Gradle**: `p4a.hook = camerax_provider/gradle_options.py` para injetar as bibliotecas CameraX do Jetpack.
- **Dependências Nativas**: Google ML Kit Text Recognition (`com.google.mlkit:text-recognition:16.0.0`).
- **Queries de Manifesto**: `manifest/speech_queries.xml` para garantir visibilidade do serviço de reconhecimento de voz no Android 11+.

### 3. Compilando o APK

Coloque o seu `secrets.json` com a chave do Gemini na raiz do projeto e execute:

```bash
buildozer android debug
```

O arquivo APK final será gerado no diretório `bin/` (ex: `bin/snapnote-0.1-arm64-v8a-debug.apk`).

Para instalar diretamente em um dispositivo conectado via USB com depuração ativada:

```bash
buildozer android deploy run
```

---

## 📄 Licença

Projeto desenvolvido para fins educacionais e de pesquisa no âmbito acadêmico da FIAP. Consulte os arquivos de licença específicos das bibliotecas de terceiros (como `camerax_provider/LICENSE`).
