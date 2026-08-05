<div align="center">
  <a href="https://github.com/devjohnatas/muyodownloader">
    <img alt="Muyo Download Logo" width="180" src="assets/MuyoLogo.png">
  </a>

  <h1>Muyo Download</h1>
  <p><strong>Gerenciador Automatizado de Downloads e Extração de Mídia para Animes, Séries e Filmes</strong><br/>Aplicação desktop desenvolvida em Python para processamento em lote, extração em provedores de vídeo na web e gerenciamento sequencial de filas com interface gráfica compacta.</p>

  <p>
    <a href="https://github.com/devjohnatas/muyodownloader/releases/latest"><img src="https://img.shields.io/github/v/release/devjohnatas/muyodownloader?label=release&color=F97316&style=flat-square" alt="Latest Release"></a>
    <a href="https://github.com/devjohnatas/muyodownloader/actions/workflows/build.yml"><img src="https://img.shields.io/github/actions/workflow/status/devjohnatas/muyodownloader/build.yml?label=build&color=10B981&style=flat-square" alt="Build Workflow"></a>
    <a href="https://github.com/devjohnatas/muyodownloader/releases"><img src="https://img.shields.io/github/downloads/devjohnatas/muyodownloader/total?color=FB923C&style=flat-square" alt="Downloads"></a>
    <a href="https://github.com/devjohnatas/muyodownloader/blob/main/LICENSE"><img src="https://img.shields.io/github/license/devjohnatas/muyodownloader?color=9333EA&style=flat-square" alt="License"></a>
  </p>
</div>

---

## Visão Geral

O **Muyo Download** é uma aplicação desktop especializada na automação, captura e download sequencial de catálogos e temporadas completas de animes, séries e filmes a partir de diversos portais web e provedores de streaming na internet.

Utilizando uma interface limpa construída em CustomTkinter e um motor de scraping fundamentado no Playwright (Chromium Headless), yt-dlp e BeautifulSoup, o software simplifica o processo de download sem exigir navegação manual intensiva ou visualização de páginas publicitárias intrusivas, extraindo os fluxos diretos de vídeo e padronizando a nomenclatura dos arquivos na máquina local.

---

## Portais Compatíveis e Servidores de Mídia

O motor de extração possui uma arquitetura flexível desenhada para operar em sites de acesso público e também em portais web que necessitem de autenticação de conta de usuário:

<table>
<tr>
<td valign="top" width="50%">

#### Portais e Catálogos Web

| Site / Plataforma | Suporte | Observação |
|---|---|---|
| **[Encontrei.info](https://encontrei.info)** | Suportado | *Requer conta de usuário configurada no software* |
| **[AnimeFire.io](https://animefire.io)** | Suportado | *Catálogo público aberto* |
| **Outros Portais de Vídeo** | Em expansão | *Suporte modular via scrapers* |

</td>
<td valign="top" width="50%">

#### Servidores e Provedores (CDNs)

| Provedor de Vídeo | Resolução Autônoma |
|---|---|
| **MixDrop** (API oculta e extração paralela) | Suportado |
| **StreamTape / Embeds Web** | Suportado |
| **Blogger / Google Drive** | Suportado |
| **Mega / HLS / MP4 Direto** | Suportado *(via yt-dlp)* |

</td>
</tr>
</table>

> *Note: Para portais que exigem autenticação prévia de usuário, o e-mail e senha de acesso devem ser informados de forma segura na aba Configurações da aplicação. O sistema executa o login silenciosamente em segundo plano, sem manter janelas ou abas de navegadores abertas.*

---

## Principais Funcionalidades

- **Processamento Sequencial Contínuo:** A execução dos downloads é processada de forma individual (item por item na fila), o que permite o aproveitamento total da largura de banda da conexão e previne bloqueios de IP causados por requisições excessivas simultâneas junto aos servidores de vídeo.
- **Gerenciamento Dinâmico da Fila de Mídiras:** Possibilita a pesquisa e inclusão de novos animes, séries ou filmes durante uma sessão ativa de transferência, integrando os episódios ao final da fila sem a necessidade de paralisar as tarefas correntes.
- **Interface Ergonômica Otimizada:** Apresentação gráfica compacta (550x580) projetada conforme padrões de softwares desktop modernos, dispondo de uma barra superior unificada em linha única com o controle de seleção alternável e uma grade horizontal para os itens de configuração.
- **Filtragem Aprimorada de Temporadas:** Opções para filtro rápido por seleção de temporadas via menu suspenso ou recorte quantitativo preciso por faixa sequencial de episódios (exemplo: extrair especificamente do episódio 01 até o 12).
- **Estruturação de Diretórios e Áudio Multilíngue:** Salvamento padronizado de arquivos divididos em pastas por título e temporada sob o diretório principal `Muyo Download` no Windows. Permite configuração nativa para baixar versões com áudio Dublado, Legendado ou simultaneamente em ambas as versões para cada episódio.
- **Módulo de Autoatualização Autônoma:** Conectado nativamente à API oficial do GitHub para inspecionar, transferir e atualizar o próprio pacote executável em background sempre que uma nova release for publicada, reiniciando o software pronto para uso na versão recente.

---

## Instalação e Execução

### Executável Standalone (.exe para Windows)

1. Aceda à aba oficial de [Releases do GitHub](https://github.com/devjohnatas/muyodownloader/releases/latest) e faça o download do pacote mais recente (`MuyoDownload-vX.X.X-windows.zip`).
2. Extraia o conteúdo para o diretório local de preferência no seu computador.
3. Inicie o aplicativo clicando duas vezes em `MuyoDownload.exe`. O binário já contempla o ambiente de execução Python, Playwright e yt-dlp sem necessidade de instalações adicionais no sistema.

---

### Execução pelo Código-Fonte (Ambiente Desenvolvedor)

1. Certifique-se de ter o **Python 3.10** ou posterior instalado no sistema operacional.
2. Clone o repositório via linha de comando no seu terminal e acesse a pasta do projeto:
   ```bash
   git clone https://github.com/devjohnatas/muyodownloader.git
   cd muyodownloader
   ```
3. Crie e ative um ambiente virtual dedicado para o gerenciamento de dependências:
   ```powershell
   # Criar o ambiente virtual via Windows
   python -m venv .venv

   # Ativá-lo via PowerShell
   .\.venv\Scripts\activate
   ```
4. Execute a instalação das bibliotecas de requisitos e do navegador autônomo utilizado pelo motor de scraping:
   ```bash
   pip install -r requirements.txt
   playwright install chromium
   ```
5. Para inicializar a interface do sistema via terminal, execute:
   ```bash
   python main.py
   ```
   *No Windows, é possível utilizar diretamente o atalho de script automatizado `iniciar_muyo.bat` na raiz.*

---

## Compilação em Executável (.exe)

O projeto incorpora um pipeline de build automatizado utilizando **PyInstaller**, programado diretamente pelo arquivo `build_exe.py` com regras de otimização de bytecode de nível 2 e ocultação de imports essenciais:

```bash
python build_exe.py
```

Após o processamento e a limpeza dos temporários de compilação, o aplicativo e sua estrutura de pastas estarão prontos para redistribuição comercial ou de uso geral dentro do diretório gerado em `dist/MuyoDownload/`.

---

## Contribuição e Relato de Problemas

O **Muyo Download** é um projeto com foco na contínua evolução dos scrapers para novas plataformas de vídeo e CDNs da internet:

- **Relatar Instabilidades ou Bugs:** Em casos onde domínios sofrerem modificações na estrutura HTML ou alterações em links de players, abra um relato detalhado diretamente na página de [Issues](https://github.com/devjohnatas/muyodownloader/issues), citando a URL exata e comportamentos apresentados no console.
- **Solicitações de Novos Sites:** Para propor a integração com novos catálogos web de séries, mangás ou animes, registre a recomendação via Issues.
- **Pull Requests:** Melhorias arquiteturais no código Python ou implementações adicionais para raspagem de novos reprodutores de vídeo são bem-vindas na branch oficial do projeto através de Pull Requests.

---

## Licenciamento

O código-fonte e documentação deste repositório estão distribuídos nos termos da licença open-source **MIT**. Consulte a íntegra no arquivo [LICENSE](LICENSE) deste projeto para especificações relativas ao uso, distribuição e direitos autorais.
