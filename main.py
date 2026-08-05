import os
import sys
import traceback

# Configuração para evitar erro do Playwright no executável e isolar navegadores
_old_dir = os.path.join(os.getenv('LOCALAPPDATA', os.path.expanduser('~')), 'EncontreiDownloader')
_app_dir = os.path.join(os.getenv('LOCALAPPDATA', os.path.expanduser('~')), 'MuyoDownload')

if os.path.exists(_old_dir) and not os.path.exists(_app_dir):
  try:
    os.rename(_old_dir, _app_dir)
  except Exception:
    _app_dir = _old_dir

os.makedirs(_app_dir, exist_ok=True)

_pw_path = os.path.join(_app_dir, 'playwright-browsers')
os.environ['PLAYWRIGHT_BROWSERS_PATH'] = _pw_path
os.environ['PLAYWRIGHT_BROWSERS_PATH_0'] = _pw_path

def _handle_exception(exc_type, exc_value, exc_traceback):
  err_file = os.path.join(_app_dir, 'crash_error.log')
  try:
    with open(err_file, 'a', encoding='utf-8') as f:
      f.write('--- ERRO FATAL EM EXECUÇÃO ---\n')
      traceback.print_exception(exc_type, exc_value, exc_traceback, file=f)
  except Exception:
    pass
  try:
    import tkinter as tk
    from tkinter import messagebox
    root = tk.Tk()
    root.withdraw()
    messagebox.showerror(
        "Erro na Aplicação",
        f"Ocorreu um erro inesperado no Muyo Download:\n\n{exc_value}\n\nDetalhes gravados em:\n{err_file}"
    )
    root.destroy()
  except Exception:
    pass

sys.excepthook = _handle_exception

# Importações explícitas para o PyInstaller
import src.auth
import src.catalog_parser
import src.config_manager
import src.downloader_engine
import src.file_namer
import src.gui_app
from src.gui_app import MuyoDownloadApp

if __name__ == '__main__':
  try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
  except Exception:
    pass

  app = MuyoDownloadApp()
  app.mainloop()
