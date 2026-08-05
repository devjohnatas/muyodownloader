import re
from bs4 import BeautifulSoup


class CatalogParser:
  """Analisador Avançado de URLs do encontrei.info.

  Suporta leitura via HTML e chamadas diretas na API do Videobox para coletar 
  todas as temporadas (Temporada 1, 2, 3...) de forma transparente.
  """

  def __init__(self, auth_manager):
    self.auth = auth_manager
    self.session = auth_manager.get_session()

  def parse_url(self, url: str) -> dict:
    url = url.strip()
    if not url.startswith('http'):
      url = 'https://' + url

    if 'animefire' in url.lower():
      return self._parse_animefire_catalog(url)

    try:
      resp = self.session.get(url, timeout=20)
      if resp.status_code != 200:
        return {
            'error': (
                f'Erro ao acessar página (Status HTTP: {resp.status_code})'
            )
        }

      soup = BeautifulSoup(resp.text, 'html.parser')

      # 1. Extrair Título da Obra
      title_el = (
          soup.find('h1')
          or soup.find('h2', class_='ipsType_pageTitle')
          or soup.find('title')
      )
      raw_title = title_el.get_text(strip=True) if title_el else 'Obra Sem Nome'

      clean_title = re.sub(
          r'(?i)(-\s*)?assistir\s+|^assistir\s+|(dublado|legendado|dual'
          r' áudio|online|hd|fhd|4k|\s*-\s*etv.*$)',
          '',
          raw_title,
      ).strip()
      clean_title = re.sub(r'\s+', ' ', clean_title).strip()
      if not clean_title:
        clean_title = 'Obra Identificada'

      # 2. Identificar se é Série / Anime e buscar Video ID do site
      is_series = False
      if any(
          w in url.lower() for w in ['/series/', '/animes/', '/temporada/']
      ) or 'serie' in raw_title.lower():
        is_series = True

      video_id = None
      vb_sec = soup.find(lambda t: t.has_attr('data-video-id'))
      if vb_sec:
        video_id = str(vb_sec.get('data-video-id')).strip()
      if not video_id:
        # Tentar extrair do link final da url (ex: ...-29470/)
        m_id = re.search(r'-(\d+)(?:/)?$', url)
        if m_id:
          video_id = m_id.group(1)

      # 3. Descobrir Todas as Temporadas (Lendo botões data-season no DOM)
      available_seasons = set()
      for el in soup.find_all(lambda t: t.has_attr('data-season')):
        s_val = str(el.get('data-season')).strip()
        if s_val.isdigit():
          available_seasons.add(int(s_val))
      if not available_seasons:
        available_seasons.add(1)

      episodes_found = {}

      # 4. Busca Padrão de Episódios no HTML visível
      for a in soup.find_all('a', href=True):
        href = a['href'].strip()
        text = a.get_text(strip=True)
        if '/episodios/online/' in href or '/ep/' in href:
          match = re.search(r'(\d{1,2})x(\d{1,3})', href, re.IGNORECASE)
          if not match:
            match = re.search(r'(\d{1,2})x(\d{1,3})', text, re.IGNORECASE)
          if match:
            season = int(match.group(1))
            episode = int(match.group(2))
            key = (season, episode)
            ep_title = re.sub(r'^\d+\s*', '', text).strip()
            if len(ep_title) < 2 or re.match(r'^\d+x\d+$', ep_title):
              ep_title = f'Episódio {episode}'

            episodes_found[key] = {
                'type': 'episode',
                'series_title': clean_title,
                'season': season,
                'episode': episode,
                'title': ep_title[:50],
                'url': href,
                'display_text': (
                    f'Temporada {season:02d} - Ep {episode:02d}'
                    f' ({ep_title[:40]})'
                ),
            }
            available_seasons.add(season)

      # 5. Busca Avançada Multi-Temporada via API Exclusiva do Encontrei
      if is_series and video_id:
        api_base = 'https://encontrei.info/index.php?app=videobox&module=video&controller=view&do=episodesList'
        headers = {
            'X-Requested-With': 'XMLHttpRequest',
            'Accept': 'application/json',
        }
        for s_num in sorted(list(available_seasons)):
          try:
            api_url = f'{api_base}&id={video_id}&season={s_num}&audio=Dublado'
            api_res = self.session.get(api_url, headers=headers, timeout=12)
            if api_res.status_code == 200:
              data = api_res.json()
              eps_list = data.get('episodes', [])
              for ep in eps_list:
                ep_num_str = str(ep.get('number', '0')).strip()
                if not ep_num_str.isdigit():
                  continue
                ep_num = int(ep_num_str)
                key = (s_num, ep_num)
                ep_url = ep.get('url', '').strip()
                ep_title = ep.get('title', '').strip()
                if not ep_title or len(ep_title) < 2:
                  ep_title = f'Episódio {ep_num}'
                if ep_url and key not in episodes_found:
                  episodes_found[key] = {
                      'type': 'episode',
                      'series_title': clean_title,
                      'season': s_num,
                      'episode': ep_num,
                      'title': ep_title[:50],
                      'url': ep_url,
                      'display_text': (
                          f'Temporada {s_num:02d} - Ep {ep_num:02d}'
                          f' ({ep_title[:40]})'
                      ),
                  }
          except Exception as e:
            print(f'Aviso: falha na API para temporada {s_num}: {e}')

      if len(episodes_found) > 0 or (is_series and len(episodes_found) > 0):
        sorted_keys = sorted(episodes_found.keys())
        ep_list = [episodes_found[k] for k in sorted_keys]
        seasons = sorted(list(set([k[0] for k in sorted_keys])))

        return {
            'type': 'series',
            'title': clean_title,
            'seasons': seasons,
            'total_episodes': len(ep_list),
            'items': ep_list,
        }
      else:
        return {
            'type': 'movie',
            'title': clean_title,
            'items': [{
                'type': 'movie',
                'title': clean_title,
                'url': url,
                'display_text': f'🎬 Filme: {clean_title}',
            }],
        }
    except Exception as e:
      return {'error': f'Erro ao processar URL na rede: {e}'}

  def _parse_animefire_catalog(self, url: str) -> dict:
    try:
      url = url.strip()
      url_clean = re.sub(r'/\d+(?:/)?$', '', url)
      if '/animes/' in url_clean and '-todos-os-episodios' not in url_clean.lower():
        url_catalog = url_clean.rstrip('/') + '-todos-os-episodios'
      else:
        url_catalog = url_clean

      headers = {
          'User-Agent': (
              'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
              ' (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
          )
      }

      resp = self.session.get(url_catalog, headers=headers, timeout=20, allow_redirects=True)
      if resp.status_code == 404:
        resp = self.session.get(url, headers=headers, timeout=20, allow_redirects=True)

      if resp.status_code != 200:
        return {
            'error': (
                f'Erro ao acessar página do AnimeFire (Status HTTP: {resp.status_code})'
            )
        }

      soup = BeautifulSoup(resp.text, 'html.parser')

      title_el = soup.find('h1') or soup.find('h2') or soup.find('title')
      raw_title = title_el.get_text(strip=True) if title_el else 'Obra Sem Nome'

      clean_title = re.sub(
          r'(?i)(-\s*)?assistir\s+|^assistir\s+|-?\s*todos os episódios.*$|-?\s*animefire.*$',
          '',
          raw_title,
      ).strip()
      clean_title = re.sub(r'\s+', ' ', clean_title).strip()
      if not clean_title:
        clean_title = 'Obra Identificada'

      lang_detected = 'Dublado' if ('dublado' in raw_title.lower() or 'dublado' in url.lower()) else 'Legendado'

      slug_match = re.search(r'/animes/([^/?#]+)', resp.url)
      base_slug = slug_match.group(1).replace('-todos-os-episodios', '') if slug_match else ''

      episodes_found = {}
      for a in soup.find_all('a', href=True):
        href = a['href'].strip()
        if href.startswith('/'):
          href = 'https://animefire.io' + href
        if base_slug and f'/animes/{base_slug}' in href:
          match = re.search(r'/animes/[^/?#]+/(\d+)(?:/)?$', href)
          if match:
            ep_num = int(match.group(1))
            key = (1, ep_num)
            episodes_found[key] = {
                'type': 'episode',
                'series_title': clean_title,
                'season': 1,
                'episode': ep_num,
                'title': f'Episódio {ep_num}',
                'url': href,
                'display_text': (
                    f'Temporada 01 - Ep {ep_num:02d} ({clean_title[:30]} -'
                    f' {lang_detected})'
                ),
                'site': 'animefire',
                'lang': lang_detected,
            }

      if len(episodes_found) > 0:
        sorted_keys = sorted(episodes_found.keys())
        ep_list = [episodes_found[k] for k in sorted_keys]

        return {
            'type': 'series',
            'title': clean_title,
            'seasons': [1],
            'total_episodes': len(ep_list),
            'items': ep_list,
            'site': 'animefire',
        }
      else:
        return {
            'type': 'movie',
            'title': clean_title,
            'items': [{
                'type': 'movie',
                'title': clean_title,
                'url': resp.url,
                'display_text': f'🎬 Filme: {clean_title} ({lang_detected})',
                'site': 'animefire',
                'lang': lang_detected,
            }],
            'site': 'animefire',
        }
    except Exception as e:
      return {'error': f'Erro ao processar catálogo do AnimeFire na rede: {e}'}

