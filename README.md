<div align="center">
  <a href="https://github.com/devjohnatas/muyodownloader">
    <img alt="Muyo Download Logo" width="190" src="assets/MuyoLogo.png">
  </a>

  <h1>Muyo Download</h1>
  <p><strong>Gerenciador de Downloads em Massa VIP & Robô Inteligente de Captura de Animes e Séries</strong><br/>Extraia catálogos inteiros, filtre temporadas por intervalos e realize downloads em sequência Turbo — tudo com design premium e velocidade máxima.</p>

  <p>
    <a href="https://github.com/devjohnatas/muyodownloader/releases/latest"><img src="https://img.shields.io/github/v/release/devjohnatas/muyodownloader?label=release&color=F97316&style=flat-square" alt="Latest Release"></a>
    <a href="https://github.com/devjohnatas/muyodownloader/actions/workflows/build.yml"><img src="https://img.shields.io/github/actions/workflow/status/devjohnatas/muyodownloader/build.yml?label=build&color=10B981&style=flat-square" alt="Build Workflow"></a>
    <a href="https://github.com/devjohnatas/muyodownloader/releases"><img src="https://img.shields.io/github/downloads/devjohnatas/muyodownloader/total?color=FB923C&style=flat-square" alt="Downloads"></a>
    <a href="https://github.com/devjohnatas/muyodownloader/blob/main/LICENSE"><img src="https://img.shields.io/github/license/devjohnatas/muyodownloader?color=9333EA&style=flat-square" alt="License"></a>
  </p>
</div>

---

## 🔥 O que é o Muyo Download?

O **Muyo Download** é uma ferramenta de automação avançada para desktop desenvolvida em Python, criada especialmente para contornar limitações de navegação manual, anúncios invasivos e travas de velocidade ao baixar seus animes, filmes e séries favoritos de plataformas web e de sites de membros VIP.

Combinando uma interface **CustomTkinter** de estética **Vibra Dark & Orange** com um poderoso motor web impulsionado pelo **Playwright (Chromium Headless)**, **yt-dlp** e **BeautifulSoup**, o aplicativo oferece uma experiência completa e sem esforço: você cola o link da obra e o sistema inspeciona os bastidores dos servidores de streaming em segundos, organizando os arquivos por pasta automaticamente na sua máquina.

---

## ✨ Funcionalidades

### 📥 Portais e Servidores Suportados
O motor do **Muyo Download** é construído sob uma arquitetura modular capaz de decodificar tanto catálogos abertos quanto painéis restritos para assinantes:

<table>
<tr>
<td valign="top" width="50%">

#### 🌐 Plataformas e Catálogos Web

| Site / Portal | Suporte | Observação |
|---|---|---|
| **[Encontrei.info](https://encontrei.info)** | ✅ | *Requer Login VIP* |
| **[AnimeFire.io](https://animefire.io)** | ✅ | *Catálogo Aberto* |
| **Outros Blogs & Portais** | ⏳ | *Expansão contínua* |

</td>
<td valign="top" width="50%">

#### ⚡ Servidores de Streaming (CDN)

| Servidor de Vídeo | Suporte |
|---|---|
| **MixDrop** (Bypass & API Oculta) | ✅ |
| **StreamTape / Embeds** | ✅ |
| **Blogger / Google Drive** | ✅ |
| **Mega / HLS / MP4 Direto** | ✅ *(via yt-dlp)* |

</td>
</tr>
</table>

> 💡 **Sites com restrição VIP** (como o *Encontrei.info*) requerem apenas que você preencha suas credenciais uma única vez na aba **⚙️ Configurações**. O programa cuidará do login silente e da persistência local de sessão nos bastidores com total cibersegurança!

---

### 🚀 Motor de Sequência Contínua (Turbo 1-a-1)
Diferente de gerenciadores tradicionais que sobrecarregam sua internet e causam bloqueios instantâneos por disparar 20 downloads ao mesmo tempo, o **Muyo Download** incorpora o motor sequencial contínuo:
- **Fluxo Contínuo e Sem Travamentos**: Processa a fila episódio por episódio com prioridade de banda máxima, aplicando intervalos de segurança inteligentes (3s) entre cada conclusão para burlar limites anti-DDOS dos servidores CDN.
- **Fila Dinâmica Expandível**: Você pode pesquisar novas obras e pressionar "Adicionar em Sequência" enquanto um lote já está rodando! O sistema anexa os novos vídeos ao final da fila perfeitamente.

---

### 🎨 Design Premium & Ergonomia em 1 Linha
- **Layout Minimalista (`550x580`)**: Janela na proporção vertical exata, evitando telas largas ou barras laterais desperdiçadoras de espaço.
- **Barra de Ferramentas de 1 Linha**: Todos os controles de filtragem consolidados ergonomicamente no centro da tela.
- **Botão Inteligente de Seleção Rápida**: O botão alterna o status em tempo real entre **`✓ Todos`** (para selecionar tudo) e **`✕ Desmarcar`**, eliminando poluição de botões extras na tela.
- **Filtros Por Temporada e Intervalo**: Selecione rapidamente no dropdown "Temporada 01" ou digite no filtro personalizado para marcar apenas um intervalo preciso (Ex: do episódio **01** ao **12**).

---

### 📂 Organização Automática de Arquivos
Todos os downloads são centralizados na pasta raiz **`Muyo Download`** (por padrão, dentro de sua pasta de Downloads do Windows). O sistema renomeia e padroniza a estrutura local automaticamente:

```text
C:\Users\SEU-USUARIO\Downloads\
 └── Muyo Download\                  <=== Pasta Raiz Principal do Projeto
      ├── Demon Slayer\
      │    ├── Temporada 01\
      │    │    ├── Demon Slayer - T01E01 - Dublado.mp4
      │    │    └── Demon Slayer - T01E02 - Dublado.mp4
      │    └── Temporada 02\
      │         └── Demon Slayer - T02E01 - Dublado.mp4
      └── O Senhor dos Anéis\
           └── O Senhor dos Anéis - Dublado.mp4
```
*Suporta escolha nativa de áudio: **Dublado**, **Legendado** ou **Ambos (Dub + Leg)** — se selecionar Ambos, ele baixa as duas versões de cada episódio em sequência!*

---

### 🔄 Autoatualização Inteligente (Self-Update Engine)
O aplicativo possui o sistema de atualização autônomo diretamente integrado à API do GitHub:
- Ao abrir o aplicativo ou clicar em **"🔍 Buscar Atualização"** nas Configurações, o programa consulta o repositório oficial [devjohnatas/muyodownloader](https://github.com/devjohnatas/muyodownloader).
- Se detectar uma nova versão no aplicativo compilado (`.exe`), o instalador baixa o pacote em background, aplica os arquivos silenciosamente e reinicia o aplicativo atualizado sem nenhuma intervenção manual!
- Em ambiente de desenvolvimento Git, realiza verificação direta por hash de commit e executa `git pull` limpo.

---

## 🖥️ Como Utilizar

### 📦 Versão Compilada (Releases Windows `.exe`)
1. Acesse a seção de [Releases do GitHub](https://github.com/devjohnatas/muyodownloader/releases) e baixe a última versão compatível (`MuyoDownload-vX.X.X-windows.zip`).
2. Extraia o arquivo zip na pasta de sua preferência.
3. Dê um duplo clique em **`MuyoDownload.exe`**. O programa já vem completo com todas as dependências embutidas!

---

### 🛠️ Rodando via Código-fonte (Modo Desenvolvedor)
1. Certifique-se de ter o **Python 3.10 ou superior** instalado em seu computador.
2. Clone o repositório oficial e entre na pasta:
   ```bash
   git clone https://github.com/devjohnatas/muyodownloader.git
   cd muyodownloader
   ```
3. Crie e ative um ambiente virtual (recomendado):
   ```powershell
   # Criar o ambiente virtual no Windows
   python -m venv .venv

   # Ativar no PowerShell
   .\.venv\Scripts\activate
   ```
4. Instale as bibliotecas Python e o navegador autônomo do Playwright:
   ```bash
   pip install -r requirements.txt
   playwright install chromium
   ```
5. Inicie o sistema pelo terminal:
   ```bash
   python main.py
   ```
   *Ou, no Windows, utilize o atalho rápido de duplo clique **`iniciar_muyo.bat`**.*

---

## 🏗️ Como Compilar em Executável (.exe)

O projeto engloba uma pipeline avançada com **PyInstaller** no script `build_exe.py`, projetada com otimização de bytecode e blindagem contra bibliotecas extras não utilizadas:

```bash
python build_exe.py
```
*Ao terminar a compilação, a pasta limpa **`dist/MuyoDownload/`** conterá o aplicativo independente **`MuyoDownload.exe`**, devidamente carimbado com o ícone oficial da chama e pronto para distribuição sem requerer instalações de terminal.*

---

## 🤝 Como Contribuir

O **Muyo Download** é um projeto pensado para máxima performance na comunidade! Toda ajuda é incrivelmente bem-vinda:

- 🐛 **Relatar Bug ou Problema**: Encontrou erro num link específico? Abra uma [Issue](https://github.com/devjohnatas/muyodownloader/issues) descrevendo o URL da série e os passos para reproduzir.
- 🌐 **Solicitar Suporte a Novas Plataformas**: Quer que o motor Baixe de um novo site de animes ou mangás? Crie uma sugestão no painel de Issues!
- 🔧 **Pull Requests**: Sinta-se convidado a enviar melhorias e novos scrapers na branch principal via PR!

---

## 📄 Licença

Este projeto e código-fonte estão distribuídos sob a licença **MIT**. Consulte o arquivo [LICENSE](LICENSE) para mais detalhes.

---

<p align="center">
  <em>🔥 Desenvolvido com foco na melhor experiência visual, velocidade turbo e máxima automação!</em>
</p>
