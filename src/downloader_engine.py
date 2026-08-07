import html
import json
import os
import re
import sys
import time
from bs4 import BeautifulSoup
import yt_dlp
from playwright.sync_api import sync_playwright
import requests
from src.file_namer import FileNamer


class DownloaderEngine:
  """Motor robótico e algorítmico com retomada automática de conexão (HTTP

  Range) e suporte para transferências paralelas em ultra-velocidade no
  encontrei.info.
  """

  def __init__(
      self,
      auth_manager,
      status_cb=None,
      progress_cb=None,
      complete_cb=None,
  ):
    self.auth = auth_manager
    self.session = auth_manager.get_session()
    self.status_cb = (
        status_cb
        if status_cb
        else lambda msg: print(
            f"[Status] {str(msg).encode('ascii', 'ignore').decode('ascii')}"
        )
    )
    # A nova progress_cb aceita: (item_title, percent, speed_mb, dl_mb, tot_mb)
    self.progress_cb = progress_cb if progress_cb else lambda *args: None
    self.complete_cb = complete_cb if complete_cb else lambda *args: None
    self.namer = FileNamer()
    self._is_cancelled = False

  def cancel_download(self):
    self._is_cancelled = True
    self.status_cb("🛑 Comando de cancelamento recebido...")

  def _get_mixdrop_url_via_api(self, ep_url: str, preferred_lang="Dublado"):
    try:
      ep_id = None
      match = re.search(r"-(\d+)(?:/)?$", ep_url.strip())
      if match:
        ep_id = match.group(1)
      else:
        res_html = self.session.get(ep_url, timeout=10)
        m_html = re.search(r'data-video-id=["\']?(\d+)["\']?', res_html.text)
        if m_html:
          ep_id = m_html.group(1)

      if not ep_id:
        return None

      api_url = (
          "https://encontrei.info/index.php?app=videobox&module=video&controller=view&do=playerData&id="
          + ep_id
      )
      headers = {
          "X-Requested-With": "XMLHttpRequest",
          "Accept": "application/json",
      }

      resp = self.session.get(api_url, headers=headers, timeout=12)
      if resp.status_code != 200:
        return None

      data = resp.json()
      mix_base = "https://mixdrop.top/e/"
      for p in data.get("players", []):
        lbl = str(p.get("label", "")).lower()
        if "mix" in lbl:
          url_p = p.get("url", "").strip()
          if url_p:
            mix_base = url_p
            break

      lang_str = str(preferred_lang).lower()
      target_server_str = ""
      fallback_server_str = ""

      s_dub = (
          data.get("servers_dub", "").replace("&amp;", "&").replace(";", "&")
      )
      s_leg = (
          data.get("servers_leg", "").replace("&amp;", "&").replace(";", "&")
      )

      if "leg" in lang_str and s_leg:
        target_server_str = s_leg
        fallback_server_str = s_dub
      else:
        target_server_str = s_dub if s_dub else s_leg
        fallback_server_str = s_leg

      def extract_mixdrop_code(srv_string):
        m_code = re.search(
            r"(?:^|&)mixdrop=([a-zA-Z0-9_-]+)", srv_string, re.IGNORECASE
        )
        return m_code.group(1) if m_code else None

      code = extract_mixdrop_code(target_server_str)
      if not code and fallback_server_str:
        code = extract_mixdrop_code(fallback_server_str)

      if code:
        final_url = (
            mix_base + code if mix_base.endswith("/") else f"{mix_base}/{code}"
        )
        return final_url
      else:
        for p in data.get("players", []):
          if "mixdrop" in str(p).lower() and "http" in str(p.get("url")):
            url_dir = p.get("url")
            if len(url_dir) > 25:
              return url_dir
    except Exception as e:
      print(f"Aviso API MixDrop: {e}")
    return None

  def _get_mixdrop_url_for_episode(self, ep_url: str, preferred_lang="Dublado"):
    url_api = self._get_mixdrop_url_via_api(ep_url, preferred_lang)
    if url_api:
      return url_api

    self.status_cb("🌐 Abrindo página de fallback para rastrear links...")
    res = self.session.get(ep_url, timeout=15)
    text = res.text

    matches = re.findall(
        r"https?://(?:www\.)?(?:mixdrop\.(?:top|co|to|sx|ag|ch|gl|pw)|mixdrp\.co)/(?:e|f)/[a-zA-Z0-9_-]+",
        text,
        re.IGNORECASE,
    )
    if matches:
      return matches[0]
    return None

  def _extract_mp4_native_unpacker(self, mixdrop_url: str, item_title: str):
    """Decodificador algorítmico super Rápido in-memory do padrão MixDrop (Dean

    Edwards). Elimina a necessidade de carregar navegadores Chromium pesados.
    """
    try:
      self.status_cb(f"⚡ [1s] Decodificando algoritmo para: {item_title}...")
      headers = {
          "User-Agent": (
              "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
              " (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
          )
      }
      resp = self.session.get(mixdrop_url, headers=headers, timeout=15)
      html = resp.text

      match = re.search(
          r"eval\(function\(p,a,c,k,e,d\).*?}\('(.*?)',(\d+),(\d+),'([^']*)'\.split\("
          r"'\|'\)",
          html,
          re.DOTALL,
      )
      if not match:
        return None

      p, a, c, k = match.groups()
      a = int(a)
      words = k.split("|")
      while len(words) < int(c):
        words.append("")

      def replace_word(m):
        w = m.group(0)
        try:
          idx = int(w, a) if a > 10 else int(w)
          if 0 <= idx < len(words) and words[idx]:
            return words[idx]
        except ValueError:
          pass
        return w

      unpacked = re.sub(r"\b\w+\b", replace_word, p)
      wurl_match = re.search(r'wurl\s*=\s*[\'"]([^\'"]+)[\'"]', unpacked)
      if wurl_match:
        wurl = wurl_match.group(1).strip()
        final_mp4 = "https:" + wurl if wurl.startswith("//") else wurl
        return final_mp4
    except Exception as e:
      print(f"Aviso: falha na decodificacao nativa do MixDrop: {e}")
    return None

  def _ensure_browser_installed(self):
    try:
      import subprocess
      flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
      subprocess.run(
          [sys.executable, "-m", "playwright", "install", "chromium"],
          check=False,
          capture_output=True,
          creationflags=flags
      )
    except Exception as e:
      print(f"Aviso ao verificar navegadores do Playwright: {e}")

  def download_item(
      self, item_data: dict, base_folder: str, preferred_lang="Dublado"
  ) -> bool:
    self._is_cancelled = False
    ep_url = item_data.get("url", "")
    item_title = item_data.get("display_text", "Vídeo")
    site = item_data.get("site", "")

    if "animefire" in str(site).lower() or "animefire" in str(ep_url).lower():
      return self._download_animefire_item(item_data, base_folder, preferred_lang)

    if "aniture" in str(site).lower() or "aniture" in str(ep_url).lower():
      return self._download_aniture_item(item_data, base_folder, preferred_lang)

    if "sushianimes" in str(site).lower() or "sushianimes" in str(ep_url).lower():
      return self._download_sushianimes_item(item_data, base_folder, preferred_lang)

    self.status_cb(
        f"🔍 Solicitando servidor de alta velocidade para: {item_title}"
        f" [{preferred_lang}]"
    )
    mixdrop_url = self._get_mixdrop_url_for_episode(ep_url, preferred_lang)

    if not mixdrop_url:
      err = f"Servidor MixDrop inexistente em [{item_title}]."
      self.status_cb(f"❌ {err}")
      self.complete_cb("", False, err)
      return False

    # 1. Tentativa Ultra-Rápida sem Navegador (Decodificação Matemática Nativa)
    final_mp4_url = self._extract_mp4_native_unpacker(mixdrop_url, item_title)

    # 2. Fallback Secundário via Chromium caso o MixDrop altere a compressão
    if not final_mp4_url:
      self.status_cb(
          f"🤖 [{item_title}] Acionando motor de seguranca em plano de"
          " fundo..."
      )
      try:
        self._ensure_browser_installed()
        with sync_playwright() as p:
          browser = p.chromium.launch(headless=True)
          context = browser.new_context(
              user_agent=(
                  "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                  " (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
              ),
              viewport={"width": 1280, "height": 720},
          )
          page = context.new_page()

          def handle_route(route):
            url = route.request.url
            if any(
                dom in url.lower()
                for dom in [
                    "doubleclick",
                    "googlesyndication",
                    "popads",
                    "adservice",
                    "bet",
                    "casino",
                ]
            ):
              route.abort()
            else:
              route.continue_()

          page.route("**/*", handle_route)
          page.goto(mixdrop_url, timeout=35000, wait_until="domcontentloaded")
          time.sleep(3)

          extracted = page.evaluate("""() => {
                        if (typeof MDCore !== 'undefined' && MDCore.wurl) {
                            return 'https:' + MDCore.wurl;
                        }
                        const video = document.querySelector('video');
                        if (video && video.src && !video.src.startsWith('blob:')) {
                            return video.src;
                        }
                        return null;
                    }""")
          if extracted:
            final_mp4_url = extracted
          browser.close()
      except Exception as e:
        self.status_cb(f"⚠️ Erro no robô secundario ({item_title}): {str(e)}")

    if not final_mp4_url:
      err = f"Não foi possível liberar o link MP4 para [{item_title}]."
      self.status_cb(f"❌ {err}")
      self.complete_cb("", False, err)
      return False

    series_title = item_data.get("series_title", item_data.get("title", "Obra"))
    season_num = item_data.get("season", 1)
    ep_num = item_data.get("episode", 1)

    if item_data.get("type") == "episode" or "series_title" in item_data:
      target_filepath = self.namer.get_series_filepath(
          base_folder=base_folder,
          series_title=series_title,
          season_num=season_num,
          episode_num=ep_num,
          episode_title=item_data.get("title", ""),
          language=preferred_lang,
      )
    else:
      target_filepath = self.namer.get_movie_filepath(
          base_folder=base_folder,
          movie_title=item_data.get("title", series_title),
          language=preferred_lang,
      )

    folder_dest = os.path.dirname(target_filepath)
    os.makedirs(folder_dest, exist_ok=True)

    self.status_cb(
        f"🚀 Conectado à CDN! Baixando 100% de [{item_title}] na sua pasta..."
    )
    success = self._stream_download_resumable(
        final_mp4_url, target_filepath, item_title, referer=mixdrop_url
    )

    if success:
      self.complete_cb(target_filepath, True, "")
      return True
    else:
      if self._is_cancelled:
        self.status_cb(f"🛑 Download de [{item_title}] foi cancelado.")
        self.complete_cb(
            target_filepath, False, "Download cancelado pelo usuario."
        )
      else:
        err_msg = f"A conexao da CDN caiu ao tentar transferir [{item_title}]."
        self.status_cb(f"❌ {err_msg}")
        self.complete_cb(target_filepath, False, err_msg)
      return False

  def _stream_download_resumable(
      self,
      url: str,
      target_filepath: str,
      item_title: str,
      referer="https://mixdrop.top/",
  ) -> bool:
    """Motor robusto que garante 100% de integridade do arquivo.

    Caso a conexão caia pela metade ou sofra micro-cortes, o algoritmo emenda via
    HTTP Range (bytes=) de onde parou sem perder o arquivo ou gravar episódios
    incompletos!
    """
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            " (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ),
        "Referer": referer,
        "Accept": "*/*",
    }

    try:
      # 1. Obter o peso exato e real do capítulo com retentativa contra limites temporários do MixDrop
      h_resp = None
      for attempt in range(5):
        if self._is_cancelled:
          return False
        try:
          h_resp = self.session.get(
              url, headers=headers, stream=True, timeout=20, allow_redirects=True
          )
          if h_resp.status_code in [200, 206]:
            break
          else:
            h_resp.close()
            self.status_cb(
                f"⏳ Servidor CDN em pausa de segurança (HTTP"
                f" {h_resp.status_code}). Aguardando conexão para"
                f" [{item_title}] ({attempt + 1}/5)..."
            )
            time.sleep(3)
        except Exception as err:
          self.status_cb(
              f"⏳ Instabilidade temporária no servidor ({attempt + 1}/5)..."
          )
          time.sleep(3)

      if not h_resp or h_resp.status_code not in [200, 206]:
        return False
      total_size = int(h_resp.headers.get("content-length", 0))
      total_mb = total_size / (1024 * 1024) if total_size > 0 else 0
      h_resp.close()

      downloaded = 0
      # Limpa arquivo abortado antigo caso exista
      if os.path.exists(target_filepath) and os.path.getsize(target_filepath) < total_size:
        os.remove(target_filepath)
      elif os.path.exists(target_filepath) and os.path.getsize(target_filepath) == total_size and total_size > 100:
        self.progress_cb(item_title, 100.0, 0.0, total_mb, total_mb)
        return True

      start_time = time.time()
      last_update_time = start_time
      max_retries = 10  # Permite até 10 reconexões na mesma transferência sem parar o usuário
      retries = 0

      while (downloaded < total_size or total_size == 0) and retries < max_retries:
        if self._is_cancelled:
          if os.path.exists(target_filepath):
            try:
              os.remove(target_filepath)
            except Exception:
              pass
          return False

        req_headers = headers.copy()
        if downloaded > 0:
          req_headers["Range"] = f"bytes={downloaded}-"
          mode = "ab"
        else:
          mode = "wb"

        try:
          resp = self.session.get(
              url,
              headers=req_headers,
              stream=True,
              timeout=30,
              allow_redirects=True,
          )
          if resp.status_code not in [200, 206, 416]:
            resp.close()
            retries += 1
            time.sleep(2)
            continue

          with open(target_filepath, mode) as f:
            for chunk in resp.iter_content(chunk_size=262144):  # Bloco de 256KB para máxima velocidade
              if self._is_cancelled:
                f.close()
                if os.path.exists(target_filepath):
                  try:
                    os.remove(target_filepath)
                  except Exception:
                    pass
                return False

              if chunk:
                f.write(chunk)
                downloaded += len(chunk)
                current_time = time.time()
                if current_time - last_update_time >= 0.4 or (
                    total_size > 0 and downloaded >= total_size
                ):
                  elapsed = current_time - start_time
                  speed_mb_s = (
                      (downloaded / (1024 * 1024)) / elapsed
                      if elapsed > 0
                      else 0
                  )
                  dl_mb = downloaded / (1024 * 1024)
                  percent = (
                      (downloaded / total_size) * 100 if total_size > 0 else 0
                  )
                  self.progress_cb(
                      item_title, percent, speed_mb_s, dl_mb, total_mb
                  )
                  last_update_time = current_time

          try:
            resp.close()
          except Exception:
            pass
          # Verificar se a conexão parou antes do final
          if total_size > 0 and downloaded < total_size:
            retries += 1
            self.status_cb(
                f"⚡ Conexão interrompida aos {downloaded/(1024*1024):.1f} MB"
                f" de {item_title}. Retomando de onde parou ({retries}/10)..."
            )
            time.sleep(1.5)
          elif total_size == 0 and downloaded > 10000:
            break

        except Exception as err:
          retries += 1
          print(f"Aviso - Erro de stream ({url[:50]}...): {err}", flush=True)
          self.status_cb(
              f"⏳ Instabilidade no servidor do vídeo [{item_title}]."
              f" Retentando conexão ({retries}/{max_retries})..."
          )
          time.sleep(2)

      # Checa veracidade final: o arquivo no disco condiz com os 100% de megabytes do servidor?
      if os.path.exists(target_filepath):
        final_size = os.path.getsize(target_filepath)
        if final_size >= total_size and final_size > 0:
          self.progress_cb(item_title, 100.0, 0.0, total_mb, total_mb)
          return True

      return False

    except Exception as e:
      print("Erro no stream com retomada de Range:", e)
      if os.path.exists(target_filepath):
        try:
          os.remove(target_filepath)
        except Exception:
          pass
      return False

  def _download_animefire_item(
      self, item_data: dict, base_folder: str, preferred_lang: str = "Dublado"
  ) -> bool:
    self._is_cancelled = False
    ep_url = item_data.get("url", "")
    item_title = item_data.get("display_text", "Vídeo")
    actual_lang = item_data.get("lang", preferred_lang)

    self.status_cb(
        f"🔍 [AnimeFire] Coletando stream em resolução máxima para: {item_title}"
        f" [{actual_lang}]"
    )

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            " (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ),
        "Referer": ep_url,
    }

    final_mp4_url = None
    try:
      resp = self.session.get(ep_url, headers=headers, timeout=15)
      if resp.status_code == 200:
        soup = BeautifulSoup(resp.text, "html.parser")
        video_el = soup.find("video")
        if video_el and video_el.get("data-video-src"):
          src_url = video_el.get("data-video-src")
          req_headers = {
              "User-Agent": headers["User-Agent"],
              "Referer": ep_url,
              "X-Requested-With": "XMLHttpRequest",
              "Accept": "*/*",
          }
          v_resp = self.session.get(src_url, headers=req_headers, timeout=15)
          if v_resp.status_code == 200:
            data_json = v_resp.json()
            sources = data_json.get("data", [])
            if sources:

              def get_res_val(s):
                m = re.search(r"(\d+)", str(s.get("label", "")))
                return int(m.group(1)) if m else 0

              best_source = max(sources, key=get_res_val)
              final_mp4_url = best_source.get("src")
              lbl = best_source.get("label", "Max")
              self.status_cb(
                  f"⚡ [AnimeFire] Qualidade {lbl} liberada! Preparando gravação..."
              )
    except Exception as e:
      print(f"Aviso na coleta direta do AnimeFire: {e}")

    if not final_mp4_url:
      self.status_cb(
          f"🤖 [AnimeFire: {item_title}] Acionando motor secundário (Chromium)..."
      )
      try:
        self._ensure_browser_installed()
        with sync_playwright() as p:
          browser = p.chromium.launch(headless=True)
          context = browser.new_context(
              user_agent=headers["User-Agent"],
              viewport={"width": 1280, "height": 720},
          )
          page = context.new_page()
          page.goto(ep_url, timeout=35000, wait_until="domcontentloaded")
          time.sleep(3)
          extracted = page.evaluate("""() => {
              const v = document.querySelector('video');
              if (v && v.src && !v.src.startsWith('blob:')) {
                  return v.src;
              }
              const sources = Array.from(document.querySelectorAll('video source'));
              if (sources.length > 0) {
                  return sources[sources.length - 1].src || sources[0].src;
              }
              return null;
          }""")
          if extracted:
            final_mp4_url = extracted
          browser.close()
      except Exception as err:
        self.status_cb(
            f"⚠️ Erro no robô secundario AnimeFire ({item_title}): {str(err)}"
        )

    if not final_mp4_url:
      err = f"Não foi possível extrair o vídeo MP4 para [{item_title}]."
      self.status_cb(f"❌ {err}")
      self.complete_cb("", False, err)
      return False

    series_title = item_data.get("series_title", item_data.get("title", "Obra"))
    season_num = item_data.get("season", 1)
    ep_num = item_data.get("episode", 1)

    if item_data.get("type") == "episode" or "series_title" in item_data:
      target_filepath = self.namer.get_series_filepath(
          base_folder=base_folder,
          series_title=series_title,
          season_num=season_num,
          episode_num=ep_num,
          episode_title=item_data.get("title", ""),
          language=actual_lang,
      )
    else:
      target_filepath = self.namer.get_movie_filepath(
          base_folder=base_folder,
          movie_title=item_data.get("title", series_title),
          language=actual_lang,
      )

    folder_dest = os.path.dirname(target_filepath)
    os.makedirs(folder_dest, exist_ok=True)

    self.status_cb(
        f"🚀 Conectado à CDN (LightSpeed)! Baixando 100% de [{item_title}] na"
        " sua pasta..."
    )
    success = self._stream_download_resumable(
        final_mp4_url, target_filepath, item_title, referer=ep_url
    )

    if success:
      self.complete_cb(target_filepath, True, "")
      return True
    else:
      if self._is_cancelled:
        self.status_cb(f"🛑 Download de [{item_title}] foi cancelado.")
        self.complete_cb(
            target_filepath, False, "Download cancelado pelo usuario."
        )
      else:
        err_msg = f"A conexao da CDN caiu ao tentar transferir [{item_title}]."
        self.status_cb(f"❌ {err_msg}")
        self.complete_cb(target_filepath, False, err_msg)
      return False

  def _download_aniture_item(
      self, item_data: dict, base_folder: str, preferred_lang: str = "Dublado"
  ) -> bool:
    self._is_cancelled = False
    ep_url = item_data.get("url", "")
    item_title = item_data.get("display_text", "Vídeo")
    actual_lang = item_data.get("lang", preferred_lang)

    self.status_cb(
        f"🔍 [Aniture] Consultando reprodutores e servidores para: {item_title}"
    )

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            " (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ),
        "Referer": ep_url,
    }

    embed_urls = []
    try:
      resp = self.session.get(ep_url, headers=headers, timeout=15)
      if resp.status_code == 200:
        soup = BeautifulSoup(resp.text, "html.parser")
        post_id = None
        for el in soup.find_all(lambda t: t.has_attr("data-post") and t.has_attr("data-nume")):
          if not post_id:
            post_id = el.get("data-post")
          nume = el.get("data-nume")
          p_type = el.get("data-type", "tv")
          if post_id and nume:
            api_url = f"https://aniture-pt.com.br/wp-json/dooplayer/v2/{post_id}/{p_type}/{nume}"
            try:
              api_res = self.session.get(api_url, headers=headers, timeout=10)
              if api_res.status_code == 200:
                e_url = api_res.json().get("embed_url")
                if e_url and e_url not in embed_urls:
                  embed_urls.append(e_url)
            except Exception:
              pass
    except Exception as e:
      print(f"Aviso ao consultar DooPlay no Aniture: {e}")

    if not embed_urls:
      embed_urls.append(ep_url)

    embed_urls.sort(key=lambda u: 0 if ("blogger.com" in u or "blogspot" in u) else 1)
    target_embed = embed_urls[0]
    self.status_cb(
        f"⚡ [Aniture] Servidor selecionado. Capturando fluxo de vídeo..."
    )

    final_mp4_url = None
    try:
      self._ensure_browser_installed()
      with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent=headers["User-Agent"],
            viewport={"width": 1280, "height": 720},
        )
        page = context.new_page()

        def on_req(req):
          nonlocal final_mp4_url
          u = req.url
          if "googlevideo.com/videoplayback" in u or ".mp4" in u or ".mkv" in u:
            if "pagead" not in u and "instream" not in u:
              final_mp4_url = u

        page.on("request", on_req)
        page.goto(target_embed, timeout=25000, wait_until="domcontentloaded")
        page.wait_for_timeout(2000)
        try:
          page.mouse.click(640, 360)
          page.wait_for_timeout(3000)
        except Exception:
          pass
        browser.close()
    except Exception as err:
      self.status_cb(f"⚠️ Erro ao capturar stream Aniture ({item_title}): {str(err)}")

    if not final_mp4_url:
      err = f"Não foi possível extrair o fluxo de vídeo para [{item_title}]."
      self.status_cb(f"❌ {err}")
      self.complete_cb("", False, err)
      return False

    series_title = item_data.get("series_title", item_data.get("title", "Obra"))
    season_num = item_data.get("season", 1)
    ep_num = item_data.get("episode", 1)

    if item_data.get("type") == "episode" or "series_title" in item_data:
      target_filepath = self.namer.get_series_filepath(
          base_folder=base_folder,
          series_title=series_title,
          season_num=season_num,
          episode_num=ep_num,
          episode_title=item_data.get("title", ""),
          language=actual_lang,
      )
    else:
      target_filepath = self.namer.get_movie_filepath(
          base_folder=base_folder,
          movie_title=item_data.get("title", series_title),
          language=actual_lang,
      )

    folder_dest = os.path.dirname(target_filepath)
    os.makedirs(folder_dest, exist_ok=True)

    self.status_cb(f"🚀 Iniciando download de [{item_title}] via servidor Google Video...")
    success = self._stream_download_resumable(
        final_mp4_url, target_filepath, item_title, referer="https://www.blogger.com/"
    )

    if success:
      self.complete_cb(target_filepath, True, "")
      return True
    else:
      if self._is_cancelled:
        self.status_cb(f"🛑 Download de [{item_title}] cancelado.")
        self.complete_cb(target_filepath, False, "Download cancelado.")
      else:
        err_msg = f"A conexão caiu ao tentar transferir [{item_title}]."
        self.status_cb(f"❌ {err_msg}")
        self.complete_cb(target_filepath, False, err_msg)
      return False

  def _download_sushianimes_item(
      self, item_data: dict, base_folder: str, preferred_lang: str = "Dublado"
  ) -> bool:
    self._is_cancelled = False
    ep_url = item_data.get("url", "")
    item_title = item_data.get("display_text", "Vídeo")
    actual_lang = item_data.get("lang", preferred_lang)

    self.status_cb(
        f"🔍 [SushiAnimes] Mapeando servidores (HLS/Blogger) para: {item_title}"
    )

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            " (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ),
        "Referer": ep_url,
    }

    m3u8_stream = None
    blogger_url = None
    fallback_embed = None

    try:
      resp = self.session.get(ep_url, headers=headers, timeout=15)
      if resp.status_code == 200:
        soup = BeautifulSoup(resp.text, "html.parser")
        token = ""
        meta = soup.find("meta", attrs={"name": "csrf-token"}) or soup.find(
            "meta", attrs={"name": "_token"}
        )
        if meta:
          token = meta.get("content", "")

        embed_ids = []
        for btn in soup.find_all(
            lambda t: t.has_attr("data-embed") or t.has_attr("data-id")
        ):
          eid = btn.get("data-embed") or btn.get("data-id")
          if (
              eid
              and str(eid).isdigit()
              and str(eid) not in [str(x) for x in embed_ids]
          ):
            embed_ids.append(str(eid))

        post_headers = headers.copy()
        post_headers.update({
            "X-Requested-With": "XMLHttpRequest",
            "X-CSRF-TOKEN": token,
            "Origin": "https://sushianimes.com.br",
        })

        for eid in embed_ids:
          try:
            api_res = self.session.post(
                "https://sushianimes.com.br/ajax/embed",
                data={"id": eid, "_token": token},
                headers=post_headers,
                timeout=10,
            )
            if api_res.status_code == 200:
              text_unescaped = html.unescape(api_res.text)
              if not m3u8_stream:
                m3u_matches = re.findall(
                    r"https?://[^\s\"\'<>]+\.m3u8[^\s\"\'<>]*", text_unescaped
                )
                if m3u_matches:
                  m3u8_stream = m3u_matches[0]

              if not blogger_url:
                blog_matches = re.findall(
                    r"https?://(?:www\.)?blogger\.com/video\.g\?token=[^\s\"\'<>&]+",
                    text_unescaped,
                    re.IGNORECASE,
                )
                if blog_matches:
                  blogger_url = blog_matches[0]

              if not fallback_embed and "src=" in api_res.text:
                ifr = BeautifulSoup(api_res.text, "html.parser").find("iframe")
                if ifr and ifr.get("src") and "http" in str(ifr.get("src")):
                  fallback_embed = ifr.get("src")
          except Exception:
            continue
    except Exception as e:
      print(f"Aviso ao consultar API do SushiAnimes: {e}")

    series_title = item_data.get("series_title", item_data.get("title", "Obra"))
    season_num = item_data.get("season", 1)
    ep_num = item_data.get("episode", 1)

    if item_data.get("type") == "episode" or "series_title" in item_data:
      target_filepath = self.namer.get_series_filepath(
          base_folder=base_folder,
          series_title=series_title,
          season_num=season_num,
          episode_num=ep_num,
          episode_title=item_data.get("title", ""),
          language=actual_lang,
      )
    else:
      target_filepath = self.namer.get_movie_filepath(
          base_folder=base_folder,
          movie_title=item_data.get("title", series_title),
          language=actual_lang,
      )

    folder_dest = os.path.dirname(target_filepath)
    os.makedirs(folder_dest, exist_ok=True)

    if m3u8_stream:
      self.status_cb(
          f"🚀 [SushiAnimes] Baixando fluxo FullHD HLS de [{item_title}] via"
          " yt-dlp..."
      )

      def ytdl_hook(d):
        if self._is_cancelled:
          raise Exception("Download cancelado pelo usuário.")
        if d.get("status") == "downloading":
          p_str = (
              d.get("_percent_str", "0%")
              .replace("\x1b[0;94m", "")
              .replace("\x1b[0m", "")
              .strip()
          )
          spd = (
              d.get("_speed_str", "N/A")
              .replace("\x1b[0;92m", "")
              .replace("\x1b[0m", "")
              .strip()
          )
          self.status_cb(f"📥 [HLS] {item_title}: {p_str} (Velocidade: {spd})")
        elif d.get("status") == "finished":
          self.status_cb(f"⚙️ Processando arquivo final de [{item_title}]...")

      ydl_opts = {
          "outtmpl": target_filepath,
          "quiet": True,
          "no_warnings": True,
          "nocheckcertificate": True,
          "progress_hooks": [ytdl_hook],
      }
      try:
        if os.path.exists(target_filepath):
          os.remove(target_filepath)
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
          ydl.download([m3u8_stream])
        if os.path.exists(target_filepath) and os.path.getsize(target_filepath) > 0:
          self.complete_cb(target_filepath, True, "")
          return True
      except Exception as err_yt:
        print(f"Erro no yt-dlp HLS: {err_yt}")
        try:
          import glob
          for p_file in glob.glob(target_filepath + ".part*"):
            os.remove(p_file)
        except Exception as e_clean:
          print(f"Erro ao limpar arquivos temporarios do yt-dlp: {e_clean}")

    if blogger_url or fallback_embed:
      target_embed = blogger_url if blogger_url else fallback_embed
      self.status_cb(
          f"⚡ [SushiAnimes] Conectando ao reprodutor auxiliar para extrair"
          " stream..."
      )
      final_mp4_url = None
      try:
        self._ensure_browser_installed()
        with sync_playwright() as p:
          browser = p.chromium.launch(headless=True)
          context = browser.new_context(
              user_agent=headers["User-Agent"],
              viewport={"width": 1280, "height": 720},
          )
          page = context.new_page()

          def on_req(req):
            nonlocal final_mp4_url
            u = req.url
            if (
                "googlevideo.com/videoplayback" in u
                or ".mp4" in u
                or ".mkv" in u
            ):
              if "pagead" not in u and "instream" not in u:
                final_mp4_url = u

          page.on("request", on_req)
          page.goto(target_embed, timeout=25000, wait_until="domcontentloaded")
          page.wait_for_timeout(2000)
          try:
            page.mouse.click(640, 360)
            page.wait_for_timeout(3000)
          except Exception:
            pass
          browser.close()
      except Exception as err_pw:
        print(f"Erro na extração de fallback SushiAnimes: {err_pw}")

      if final_mp4_url:
        self.status_cb(
            f"🚀 Iniciando download de [{item_title}] via servidor Google"
            " Video/CDN..."
        )
        success = self._stream_download_resumable(
            final_mp4_url,
            target_filepath,
            item_title,
            referer="https://www.blogger.com/",
        )
        if success:
          self.complete_cb(target_filepath, True, "")
          return True

    err = f"Não foi possível extrair fluxo compatível para [{item_title}]."
    self.status_cb(f"❌ {err}")
    self.complete_cb(target_filepath, False, err)
    return False
