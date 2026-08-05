import json
import os
import sys
from pathlib import Path


class ConfigManager:
  """Gerencia a persistência das configurações do usuário (credenciais do usuário, pasta

  padrão de downloads e idioma).
  """

  def __init__(self, config_filename='settings.json'):
    home_dir = Path.home()
    default_dl_path = os.path.join(
        home_dir, 'Downloads', 'Muyo Download'
    )

    if getattr(sys, 'frozen', False):
      base_dir = os.path.dirname(sys.executable)
    else:
      base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    self.config_path = os.path.join(base_dir, config_filename)
    self.defaults = {
        'email': '',
        'password': '',
        'default_folder': default_dl_path,
        'default_lang': 'Dublado',
        'max_concurrent_downloads': 1,
    }
    self.settings = self.defaults.copy()
    self.settings.update(self.load_config())

  def load_config(self) -> dict:
    if os.path.exists(self.config_path):
      try:
        with open(self.config_path, 'r', encoding='utf-8') as f:
          data = json.load(f)
          dirty = False
          # Segurança: Limpa automaticamente credenciais antigas ou hardcoded caso encontradas no arquivo
          if data.get('email') == 'pierleeb@gmail.com' or data.get('password') == 'Jhonatas20@':
            data['email'] = ''
            data['password'] = ''
            dirty = True
          # Migra pastas antigas para o novo padrão oficial 'Muyo Download'
          if 'Downloads_Muyo' in str(data.get('default_folder', '')) or 'EncontreiDownloader' in str(data.get('default_folder', '')):
            data['default_folder'] = self.defaults['default_folder']
            dirty = True
          for k, v in self.defaults.items():
            if k not in data:
              data[k] = v
              dirty = True
          if dirty:
            self.settings = data
            self.save_config()
          return data
      except Exception as e:
        print(f'Erro ao carregar settings.json: {e}. Usando padrões.')

    self.save_config(self.defaults)
    return self.defaults.copy()

  def save_config(self, new_settings: dict = None):
    if new_settings:
      self.settings.update(new_settings)
    try:
      os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
      with open(self.config_path, 'w', encoding='utf-8') as f:
        json.dump(self.settings, f, indent=4, ensure_ascii=False)
      return True
    except Exception as e:
      print(f'Erro ao salvar configurações no disco: {e}')
      return False

  def get(self, key, default=None):
    return self.settings.get(key, default)

  def set(self, key, value):
    self.settings[key] = value
    self.save_config()
