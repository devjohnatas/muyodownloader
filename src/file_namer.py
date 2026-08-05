import os
import re


class FileNamer:
  """Utilitário responsável por limpar textos de títulos e montar a hierarquia

  de diretórios correta exigida pelo usuário:

  Para Filmes:
      [Pasta Base]/[Nome do Filme]/[Nome do Filme] - [Dublado/Legendado].mp4
  Para Séries:
      [Pasta Base]/[Nome da Série]/Temporada [XX]/[Nome da Série] - T[XX]E[YY] -
      [Dublado/Legendado].mp4
  """

  @staticmethod
  def clean_filename(name: str) -> str:
    """Remove caracteres incompatíveis com o sistema de arquivos do Windows."""
    if not name:
      return 'Obra_Sem_Nome'
    # Remove símbolos proibidos: \ / : * ? " < > |
    cleaned = re.sub(r'[\\/*?:"<>|]', '', name)
    # Substitui múltiplos espaços por um só e limpa pontas
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned if len(cleaned) > 0 else 'Obra_Sem_Nome'

  @staticmethod
  def format_season_num(season_num) -> str:
    """Retorna temporada com pelo menos 2 dígitos (Ex: 01, 02, 10)."""
    try:
      num = int(re.sub(r'\D', '', str(season_num)))
      return f'{num:02d}'
    except:
      return str(season_num).zfill(2)

  @staticmethod
  def format_episode_num(ep_num) -> str:
    """Retorna episódio com pelo menos 2 dígitos (Ex: 01, 05, 12)."""
    try:
      num = int(re.sub(r'\D', '', str(ep_num)))
      return f'{num:02d}'
    except:
      return str(ep_num).zfill(2)

  @classmethod
  def get_movie_filepath(
      cls, base_folder: str, movie_title: str, language: str = 'Dublado'
  ) -> str:
    """Gera o caminho completo do MP4 para Filme, criando a pasta automaticamente se necessário."""
    clean_title = cls.clean_filename(movie_title)
    lang = (
        'Dublado' if 'dub' in language.lower() else (
            'Legendado'
            if 'leg' in language.lower()
            else cls.clean_filename(language)
        )
    )

    movie_dir = os.path.join(base_folder, clean_title)
    os.makedirs(movie_dir, exist_ok=True)

    file_name = f'{clean_title} - {lang}.mp4'
    return os.path.join(movie_dir, file_name)

  @classmethod
  def get_series_filepath(
      cls,
      base_folder: str,
      series_title: str,
      season_num,
      episode_num,
      episode_title: str = '',
      language: str = 'Dublado',
  ) -> str:
    """Gera o caminho completo do MP4 para Série organizando por pasta da obra e de Temporadas."""
    clean_series = cls.clean_filename(series_title)
    s_num = cls.format_season_num(season_num)
    e_num = cls.format_episode_num(episode_num)

    lang = (
        'Dublado' if 'dub' in language.lower() else (
            'Legendado'
            if 'leg' in language.lower()
            else cls.clean_filename(language)
        )
    )

    # Pasta da Série -> Pasta da Temporada
    season_folder = f'Temporada {s_num}'
    target_dir = os.path.join(base_folder, clean_series, season_folder)
    os.makedirs(target_dir, exist_ok=True)

    # Nome do Arquivo no Padrão do Usuário
    clean_ep_title = (
        f' - {cls.clean_filename(episode_title)}'
        if episode_title and len(episode_title.strip()) > 1
        else ''
    )
    file_name = f'{clean_series} - T{s_num}E{e_num}{clean_ep_title} - {lang}.mp4'
    return os.path.join(target_dir, file_name)
