import os
import shutil
import sys
from pathlib import Path
import customtkinter


def main() -> None:
    """Compila um instalador Windows (.exe) otimizado e leve do Muyo Download

    usando o padrão limpo e blindado via PyInstaller.

    Benefícios da arquitetura limpa:
    - Otimização de bytecode (redução de 10% a 15% no peso do arquivo).
    - Isolamento de arquivos temporários de build em pasta de trabalho dedicada.
    - Exclusão inteligente de bibliotecas pesadas do ecossistema Python.
    - Limpeza automática residual, deixando apenas o diretório limpo 'dist/MuyoDownload'.
    """
    try:
        from PyInstaller.__main__ import run as pyinstaller_run
    except ImportError:
        print("[Build] PyInstaller não encontrado. Instale com 'pip install pyinstaller'.")
        sys.exit(1)

    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

    project_root = Path(__file__).resolve().parent
    os.chdir(project_root)

    app_entry = project_root / "main.py"
    if not app_entry.exists():
        print(f"[Build] Ponto de entrada não encontrado: {app_entry}")
        sys.exit(1)

    dist_dir = project_root / "dist"
    app_name = "MuyoDownload"
    app_dist_dir = dist_dir / app_name

    # Isola arquivos temporários do PyInstaller sob build/pyinstaller
    work_dir = project_root / "build" / "pyinstaller"
    work_dir.mkdir(parents=True, exist_ok=True)

    ctk_path = os.path.dirname(customtkinter.__file__)

    # Módulos pesados que não usamos e devem ser sumariamente removidos caso existam no ambiente Python
    exclude_modules = [
        "torch",
        "torchvision",
        "cv2",
        "opencv_python",
        "scipy",
        "sklearn",
        "transformers",
        "tokenizers",
        "sentencepiece",
        "fugashi",
        "manga_ocr",
        "onnxruntime",
        "tensorflow",
        "jax",
        "matplotlib",
        "pandas",
        "wx",
        # Conflitos com bibliotecas Qt (usamos exclusivamente CustomTkinter)
        "PyQt6",
        "PyQt6.sip",
        "PyQt5",
        "PyQt5.sip",
        "PySide6",
    ]

    hidden_imports = [
        "playwright.sync_api",
        "playwright._impl._driver",
        "tkinter.messagebox",
        "requests",
        "bs4",
        "yt_dlp",
        "PIL",
        "src",
        "src.auth",
        "src.catalog_parser",
        "src.config_manager",
        "src.downloader_engine",
        "src.file_namer",
        "src.gui_app",
        "src.updater",
        "src.build_version",
        "urllib.request",
        "zipfile",
    ]

    args: list[str] = [
        str(app_entry),
        "--name",
        app_name,
        "--noconfirm",
        "--noconsole",
        "--clean",
        "--onedir",
        "--contents-directory",
        ".",
        "--distpath",
        str(dist_dir),
        "--workpath",
        str(work_dir),
        "--specpath",
        str(work_dir),
        "--collect-all",
        "src",
        "--collect-all",
        "playwright",
        "--collect-all",
        "customtkinter",
        "--add-data",
        f"{ctk_path};customtkinter/",
        # Otimização: Nível 2 do Bytecode Python (remove assertions e docstrings desnecessários no .exe)
        "--optimize",
        "2",
    ]

    icon_path = project_root / "assets" / "MuyoLogo.ico"
    assets_path = project_root / "assets"
    if icon_path.exists():
        args.extend(["--icon", str(icon_path)])
    if assets_path.exists():
        args.extend(["--add-data", f"{assets_path};assets/"])

    # Injeta explicitamente hidden imports para acelerar a análise da compilação
    for module_name in hidden_imports:
        args.extend(["--hidden-import", module_name])

    # Bloqueia a inclusão de bibliotecas gigantescas
    for module_name in exclude_modules:
        args.extend(["--exclude-module", module_name])

    print("=== INICIANDO COMPILADOR PYINSTALLER (MODO AVANÇADO BLINDADO) ===")
    print(f"[Build] Ponto de entrada : {app_entry}")
    print(f"[Build] Diretório Final: {app_dist_dir}")
    print(f"[Build] Pasta Temporária : {work_dir}")
    print("[Build] Otimizações ativadas:")
    print("[Build]   - Compressão de bytecode Python (--optimize 2)")
    print("[Build]   - Estrutura plana e limpa (--contents-directory .)")
    print("[Build]   - Bloqueio agressivo de bibliotecas pesadas de IA e Qt")

    try:
        pyinstaller_run(args)
    except SystemExit as exc:
        code = int(getattr(exc, "code", 1) or 0)
        if code != 0:
            print(f"[Build] Falha na compilação PyInstaller com código {code}.")
            sys.exit(code)

    # Limpeza de artefatos intermediários
    if work_dir.exists():
        print(f"[Build] Removendo diretório de trabalho temporário: {work_dir}")
        shutil.rmtree(work_dir, ignore_errors=True)
    if (project_root / "build").exists() and not any((project_root / "build").iterdir()):
        shutil.rmtree(project_root / "build", ignore_errors=True)

    # Deleta arquivos .spec soltos caso restem
    for spec in project_root.glob("*.spec"):
        try:
            print(f"[Build] Limpando arquivo .spec residual: {spec}")
            spec.unlink()
        except OSError:
            pass

    print("\n>>> 🏆 COMPILAÇÃO BLINDADA CONCLUÍDA COM SUCESSO! <<<")
    if app_dist_dir.exists():
        print(f"[Build] Aplicativo standalone disponível na pasta limpa:\n        {app_dist_dir}")
    else:
        print("[Build] Aviso: pasta final não verificada, verifique a saída acima.")


if __name__ == "__main__":
    main()
