<div align="center">
  <a href="https://github.com/devjohnatas/muyodownloader">
    <img alt="Muyo Download Logo" width="180" src="assets/MuyoLogo.png">
  </a>

  <h1>Muyo Download</h1>
  <p><strong>Gerenciador de Downloads para Animes, Séries e Filmes</strong><br/>Extraia temporadas inteiras, organize seus vídeos por pastas e faça downloads em sequência de forma automatizada.</p>

  <p>
    <a href="https://github.com/devjohnatas/muyodownloader/releases/latest"><img src="https://img.shields.io/github/v/release/devjohnatas/muyodownloader?label=release&color=F97316&style=flat-square" alt="Latest Release"></a>
    <a href="https://github.com/devjohnatas/muyodownloader/actions/workflows/build.yml"><img src="https://img.shields.io/github/actions/workflow/status/devjohnatas/muyodownloader/build.yml?label=build&color=10B981&style=flat-square" alt="Build Workflow"></a>
    <a href="https://github.com/devjohnatas/muyodownloader/releases"><img src="https://img.shields.io/github/downloads/devjohnatas/muyodownloader/total?color=FB923C&style=flat-square" alt="Downloads"></a>
    <a href="https://github.com/devjohnatas/muyodownloader/blob/main/LICENSE"><img src="https://img.shields.io/github/license/devjohnatas/muyodownloader?color=9333EA&style=flat-square" alt="License"></a>
  </p>
</div>

---

## O que é o Muyo Download?

O **Muyo Download** é um aplicativo desktop desenvolvido em Python para download automatizado de animes, séries e filmes direto de catálogos da internet, evitando anúncios e limitações de navegação manual.

A ferramenta combina uma interface gráfica compacta com um motor de extração de links focado no processamento sequencial contínuo, salvando os vídeos de forma padronizada e organizados por título e temporada direto no computador.

---

## Plataformas Suportadas

O sistema baixa vídeos tanto de catálogos abertos quanto de plataformas que necessitam de conta cadastrada:

<table>
<tr>
<td valign="top" width="50%">

#### Catálogos e Portais de Vídeo

| Site / Plataforma | Suporte | Observação |
|---|---|---|
| [Encontrei.info](https://encontrei.info) | Suportado | *(requer login na aba Configurações)* |
| [AnimeFire.io](https://animefire.io) | Suportado | |
| [Aniture](https://aniture-pt.com.br) | Suportado | |
| [SushiAnimes](https://sushianimes.com.br) | Suportado | |
| Outros portais web | Em expansão | |

</td>
<td valign="top" width="50%">

#### Servidores de Streaming (CDN)

| Servidor | Suporte |
|---|---|
| MixDrop | Suportado |
| StreamTape | Suportado |
| Blogger / Google Drive | Suportado |
| Mega / MP4 Direto | Suportado *(via yt-dlp)* |

</td>
</tr>
</table>

---

## Funcionalidades

- **Central FFmpeg Integrada (NOVO):** Aba exclusiva para conversão rápida de mídias, divisão de dual áudio e extração de sons em MP3/WAV.
- **Download Sequencial Contínuo:** Baixa vídeo por vídeo (1 a 1) para utilizar 100% da velocidade da internet, com pausas inteligentes de segurança no final de cada arquivo para evitar desconexões ou bloqueios nos provedores.
- **Fila Dinâmica:** Permite pesquisar e acrescentar novos episódios ou temporadas na lista sem parar os downloads em andamento.
- **Filtros por Intervalo:** Recorte rápido de episódios (ex: do 01 ao 12) ou seleção por temporada completa via menu suspenso.
- **Organização de Áudio e Pastas:** Cria automaticamente a pasta do título com suas subpastas na pasta `Muyo Download`, baixando na preferência desejada: Dublado, Legendado ou Ambos.
- **Atualização Automática:** Consulta novidades nas Releases do GitHub e realiza a atualização autônoma do aplicativo sem intervenção manual.

---

## Como Utilizar

### Versão Executável (.exe)
1. Baixe o pacote compactado mais recente na aba de [Releases do GitHub](https://github.com/devjohnatas/muyodownloader/releases/latest).
2. Extraia o arquivo para a pasta de sua preferência.
3. Dê um duplo clique em `MuyoDownload.exe` para abrir o aplicativo pronto para uso.

---

### Versão via Código-Fonte (Python 3.10+)
1. Clone o repositório e acesse o diretório:
   ```bash
   git clone https://github.com/devjohnatas/muyodownloader.git
   cd muyodownloader
   ```
2. Crie e ative seu ambiente virtual (opcional):
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\activate
   ```
3. Instale as dependências e o navegador Playwright:
   ```bash
   pip install -r requirements.txt
   playwright install chromium
   ```
4. Inicie o sistema via terminal ou pelo arquivo `iniciar_muyo.bat`:
   ```bash
   python main.py
   ```

---

## Como Compilar (.exe)

Para gerar o arquivo executável standalone utilizando o **PyInstaller** com as configurações otimizadas do projeto:

```bash
python build_exe.py
```
*O executável finalizado e limpo estará disponível na pasta `dist/MuyoDownload/`.*

---

## Licença

Distribuído sob a licença **MIT**. Consulte o arquivo [LICENSE](LICENSE) para maiores detalhes.
