import os
import sys
import shutil
import tempfile
import time
import json
import re
import urllib.request
import urllib.error
import zipfile
import subprocess
import webbrowser
from typing import Callable, Tuple, Optional

try:
    from src.build_version import APP_BUILD_VERSION
except ImportError:
    APP_BUILD_VERSION = "1.0.0"

APP_NAME = "Muyo Download"
APP_VERSION = APP_BUILD_VERSION
GITHUB_REPO = "devjohnatas/muyodownload"
GITHUB_RELEASES_URL = f"https://github.com/{GITHUB_REPO}/releases/latest"
GITHUB_API_LATEST_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"


def is_frozen() -> bool:
    """Verifica se o programa está executando via instalador compilado (.exe)."""
    return getattr(sys, "frozen", False)


def version_tuple(version: str) -> tuple:
    """Converte string de versão (Ex: 'v1.2.0') em tupla comparável (1, 2, 0)."""
    cleaned = (version or "").strip()
    if cleaned.lower().startswith("v"):
        cleaned = cleaned[1:]
    parts = [int(part) for part in re.findall(r"\d+", cleaned)]
    if not parts:
        return (0,)
    return tuple(parts)


def fetch_latest_release() -> dict:
    """Consulta a API do GitHub para obter a última release publicada no repositório."""
    request = urllib.request.Request(
        GITHUB_API_LATEST_URL,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": APP_NAME.replace(" ", "-"),
        },
    )
    with urllib.request.urlopen(request, timeout=10) as response:
        payload = response.read().decode("utf-8")
        return json.loads(payload)


def pick_release_asset_url(release_data: dict) -> Tuple[Optional[str], str]:
    """Procura por arquivo .zip ou .exe nos assets da release no GitHub."""
    assets = release_data.get("assets") or []
    for asset in assets:
        name = str(asset.get("name") or "").lower()
        url = str(asset.get("browser_download_url") or "").strip()
        if name.endswith(".zip") and url:
            return url, "zip"
    for asset in assets:
        name = str(asset.get("name") or "").lower()
        url = str(asset.get("browser_download_url") or "").strip()
        if name.endswith(".exe") and url:
            return url, "exe"
    return None, ""


def download_file(
    url: str,
    target_path: str,
    progress_callback: Optional[Callable[[int, int], None]] = None,
    max_retries: int = 3,
) -> None:
    """Baixa arquivo em streaming com suporte a progresso e novas tentativas automáticas."""
    last_exc = None
    for attempt in range(max_retries + 1):
        try:
            request = urllib.request.Request(
                url,
                headers={
                    "Accept": "application/octet-stream",
                    "User-Agent": APP_NAME.replace(" ", "-"),
                },
            )
            with urllib.request.urlopen(request, timeout=60) as response:
                total_bytes = 0
                content_length = response.headers.get("Content-Length")
                if content_length:
                    try:
                        total_bytes = int(content_length)
                    except (TypeError, ValueError):
                        total_bytes = 0

                bytes_read = 0
                with open(target_path, "wb") as out:
                    while True:
                        chunk = response.read(1024 * 256)
                        if not chunk:
                            break
                        out.write(chunk)
                        bytes_read += len(chunk)
                        if progress_callback:
                            progress_callback(bytes_read, total_bytes)
            return
        except urllib.error.HTTPError as exc:
            last_exc = exc
            if exc.code in (404, 502, 503) and attempt < max_retries:
                if progress_callback:
                    progress_callback(-1, -1)
                time.sleep(4 * (attempt + 1))
                continue
            raise
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            last_exc = exc
            if attempt < max_retries:
                time.sleep(4 * (attempt + 1))
                continue
            raise
    if last_exc:
        raise last_exc


def resolve_payload_dir(payload_dir: str, exe_name: str) -> str:
    """Localiza o diretório raiz dentro da extração que contém o executável."""
    direct_exe = os.path.join(payload_dir, exe_name)
    if os.path.isfile(direct_exe):
        return payload_dir

    candidates = []
    for root, _, files in os.walk(payload_dir):
        if exe_name in files:
            rel = os.path.relpath(root, payload_dir)
            depth = 0 if rel == "." else rel.count(os.sep) + 1
            candidates.append((depth, root))

    if not candidates:
        return payload_dir

    candidates.sort(key=lambda item: item[0])
    return candidates[0][1]


def run_external_updater(*, staged_dir: str, payload_dir: str, app_dir: str, exe_name: str) -> None:
    """Cria e executa um script em lote externo para fechar o app, substituir os arquivos e reiniciar."""
    updater_cmd = os.path.join(staged_dir, "apply_update.cmd")
    current_pid = os.getpid()
    log_file = os.path.join(app_dir, "updater.log")
    
    lines = [
        "@echo off",
        "setlocal",
        f'set TARGET_PID={current_pid}',
        f'set "STAGED_DIR={staged_dir}"',
        f'set "PAYLOAD_DIR={payload_dir}"',
        f'set "APP_DIR={app_dir}"',
        f'set "EXE_NAME={exe_name}"',
        f'set "LOG_FILE={log_file}"',
        'echo Iniciando atualizacao do Muyo Download... > "%LOG_FILE%"',
        'echo Aguardando fechamento do app (PID %TARGET_PID%)... >> "%LOG_FILE%"',
        ":wait_loop",
        'tasklist /FI "PID eq %TARGET_PID%" | findstr /I "%TARGET_PID%" >nul',
        "if %ERRORLEVEL%==0 (",
        "  timeout /t 1 /nobreak >nul",
        "  goto wait_loop",
        ")",
        'echo Aplicando novos arquivos do repositorio GitHub... >> "%LOG_FILE%"',
        'robocopy "%PAYLOAD_DIR%" "%APP_DIR%" /E /R:5 /W:1 /NP >> "%LOG_FILE%" 2>&1',
        'copy /y "%PAYLOAD_DIR%\\*.*" "%APP_DIR%" >> "%LOG_FILE%" 2>&1',
        'echo Atualizacao instalada! Reiniciando nova versao... >> "%LOG_FILE%"',
        'if exist "%APP_DIR%\\%EXE_NAME%" (',
        '  start "" "%APP_DIR%\\%EXE_NAME%"',
        ") else (",
        '  echo Erro: Executavel "%APP_DIR%\\%EXE_NAME%" nao encontrado na raiz! >> "%LOG_FILE%"',
        ")",
        ":cleanup",
        'timeout /t 2 /nobreak >nul',
        'rmdir /s /q "%STAGED_DIR%" 2>nul',
        'echo Processo de autoatualizacao concluido! >> "%LOG_FILE%"',
    ]

    with open(updater_cmd, "w", encoding="utf-8", newline="\r\n") as f:
        f.write("\r\n".join(lines) + "\r\n")

    subprocess.Popen(
        ["cmd", "/c", updater_cmd],
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        close_fds=True,
    )


def self_update_from_release(release_data: dict, progress_cb: Optional[Callable[[int, int, str], None]] = None) -> tuple:
    """Executa todo o ciclo de download, extração e aplicação da atualização autônoma no executável."""
    if not is_frozen():
        return False, "Autoatualização autônoma de arquivos só opera diretamente no aplicativo compilado (.exe)."

    asset_url, file_type = pick_release_asset_url(release_data)
    if not asset_url:
        return False, "Nenhum arquivo de instalação (.zip ou .exe) foi encontrado na release mais recente do GitHub."

    app_dir = os.path.dirname(sys.executable)
    exe_path = sys.executable
    if not os.path.isdir(app_dir) or not os.path.isfile(exe_path):
        return False, "Não foi possível identificar com precisão o diretório da aplicação local."

    update_root = tempfile.mkdtemp(prefix="Muyo-Update-")
    payload_dir = os.path.join(update_root, "payload")
    os.makedirs(payload_dir, exist_ok=True)
    
    exe_name = os.path.basename(exe_path)
    file_ext = ".zip" if file_type == "zip" else ".exe"
    download_path = os.path.join(update_root, f"update_package{file_ext}")

    if progress_cb:
        progress_cb(0, 0, "Baixando nova versão do servidor GitHub...")

    def _on_progress(received: int, total: int):
        if progress_cb:
            msg = f"Baixando pacote... ({received // (1024*1024)}/{total // (1024*1024)} MB)" if total > 0 else "Baixando atualização..."
            progress_cb(received, total, msg)

    try:
        download_file(asset_url, download_path, progress_callback=_on_progress)
        
        if progress_cb:
            progress_cb(100, 100, "Preparando novos arquivos da atualização...")

        if file_type == "zip":
            with zipfile.ZipFile(download_path, "r") as zf:
                zf.extractall(payload_dir)
            resolved_payload = resolve_payload_dir(payload_dir, exe_name)
        else:
            # Arquivo executável avulso
            target_exe = os.path.join(payload_dir, exe_name)
            shutil.copy2(download_path, target_exe)
            resolved_payload = payload_dir

        if not os.path.isfile(os.path.join(resolved_payload, exe_name)):
            raise FileNotFoundError(f"O executável principal '{exe_name}' não foi localizado no pacote baixado do GitHub.")
            
    except Exception as exc:
        shutil.rmtree(update_root, ignore_errors=True)
        return False, f"Erro no download ou descompactação do pacote de atualização: {exc}"

    if progress_cb:
        progress_cb(100, 100, "Atualização pronta! Aplicando no sistema...")

    run_external_updater(
        staged_dir=update_root,
        payload_dir=resolved_payload,
        app_dir=app_dir,
        exe_name=exe_name,
    )
    return True, "Atualização verificada com sucesso! Reiniciando o aplicativo..."
