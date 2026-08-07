import os
import sys
import queue
import re
import threading
import time
import subprocess
import webbrowser
from tkinter import filedialog, messagebox
import customtkinter as ctk
from PIL import Image, ImageTk
from src.auth import AuthManager
from src.catalog_parser import CatalogParser
from src.config_manager import ConfigManager
from src.downloader_engine import DownloaderEngine
import src.updater as updater
import src.ffmpeg_engine as ffmpeg_engine


class MuyoDownloadApp(ctk.CTk):

  def __init__(self):
    super().__init__()

    # Configuração de Tema Muyo Download (Modern Dark & Premium Vibrant Orange)
    ctk.set_appearance_mode('Dark')

    self.title(f'{updater.APP_NAME} v{updater.APP_VERSION}')
    # Janela compacta com largura perfeitamente dimensionada para 1 linha
    self.geometry('550x580')
    self.minsize(500, 500)

    # Paleta de Cores Muyo (Orange & Deep Obsidian)
    self.c_bg_root = '#0B0B0C'       # Preto profundo
    self.c_bg_panel = '#161618'      # Painel carvão elegante
    self.c_bg_input = '#222225'      # Inputs modernos e suaves
    self.c_border = '#2A2A2E'        # Borda fina discreta
    self.c_border_in = '#36363B'
    self.c_orange_main = '#F97316'   # Laranja vibrante principal
    self.c_orange_hover = '#FB923C'  # Laranja brilhante em hover
    self.c_orange_active = '#EA580C' # Laranja intenso no clique
    self.c_blue_main = self.c_orange_main   # Alias de segurança para compatibilidade
    self.c_blue_hover = self.c_orange_hover # Alias de segurança
    self.c_green = '#10B981'         # Verde esmeralda
    self.c_green_hover = '#059669'

    self.configure(fg_color=self.c_bg_root)

    # Configuração do Ícone Oficial da Aplicação (Muyo Download)
    if getattr(sys, 'frozen', False):
      base_dir = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
    else:
      base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    self.assets_dir = os.path.join(base_dir, 'assets')

    ico_path = os.path.join(self.assets_dir, 'MuyoLogo.ico')
    png_path = os.path.join(self.assets_dir, 'MuyoLogo.png')
    if os.path.exists(ico_path):
      try:
        self.iconbitmap(ico_path)
      except Exception:
        pass
    if os.path.exists(png_path):
      try:
        tk_img = ImageTk.PhotoImage(Image.open(png_path))
        self.iconphoto(True, tk_img)
      except Exception:
        pass

    # Gerenciadores e Credenciais Salvas
    self.config_mgr = ConfigManager()
    self.auth = AuthManager(
        email=self.config_mgr.get('email', ''),
        password=self.config_mgr.get('password', ''),
    )
    self.parser = CatalogParser(self.auth)
    self.downloader = None

    # Estado Interno & Concorrência Paralela
    self.items_list = []
    self.checkbox_widgets = {}
    self.all_selected = True
    self.is_downloading = False
    self.work_queue = queue.Queue()
    self.active_downloads = {}
    self.total_batch_items = 0
    self.completed_batch_items = 0

    # Layout Principal Vertical
    self.grid_columnconfigure(0, weight=1)
    self.grid_rowconfigure(0, weight=0) # Navbar fixa
    self.grid_rowconfigure(1, weight=1) # Conteúdo principal expansível

    self._build_top_navbar()
    self._build_baixador_frame()
    self._build_configuracoes_frame()
    self._build_ffmpeg_frame()

    self.select_tab('baixador')
    self.after(500, self._auto_connect_in_background)
    self.after(2000, lambda: threading.Thread(target=self._startup_update_check, daemon=True).start())

  def _get_logo_ctk_image(self, size_tuple=(26, 26)):
    png_path = os.path.join(getattr(self, 'assets_dir', ''), 'MuyoLogo.png')
    if os.path.exists(png_path):
      try:
        img = Image.open(png_path)
        return ctk.CTkImage(light_image=img, dark_image=img, size=size_tuple)
      except Exception:
        return None
    return None

  def _get_icon(self, name, size_tuple=(18, 18)):
    if not hasattr(self, '_icon_cache'):
        self._icon_cache = {}
    if name in self._icon_cache:
        return self._icon_cache[name]
    png_path = os.path.join(getattr(self, 'assets_dir', ''), 'icons', f'{name}.png')
    if os.path.exists(png_path):
      try:
        img = Image.open(png_path)
        icon = ctk.CTkImage(light_image=img, dark_image=img, size=size_tuple)
        self._icon_cache[name] = icon
        return icon
      except Exception:
        pass
    return None

  # -------------------------------------------------------------------------
  # NAVBAR SUPERIOR (MENUS ACIMA E COMPACTOS)
  # -------------------------------------------------------------------------
  def _build_top_navbar(self):
    self.navbar_frame = ctk.CTkFrame(
        self,
        height=48,
        corner_radius=0,
        fg_color=self.c_bg_panel,
        border_width=1,
        border_color=self.c_border,
    )
    self.navbar_frame.grid(row=0, column=0, sticky='ew')
    self.navbar_frame.grid_columnconfigure(1, weight=1)

    self.btn_tab_baixador = ctk.CTkButton(
        self.navbar_frame,
        text=' Baixador',
        image=self._get_icon('download'),
        compound='left',
        font=ctk.CTkFont('Segoe UI', size=12, weight='bold'),
        height=28,
        width=105,
        corner_radius=6,
        fg_color=self.c_orange_main,
        hover_color=self.c_orange_hover,
        command=lambda: self.select_tab('baixador'),
    )
    self.btn_tab_baixador.grid(row=0, column=2, padx=4, pady=10, sticky='e')

    self.btn_tab_config = ctk.CTkButton(
        self.navbar_frame,
        text=' Configurações',
        image=self._get_icon('settings'),
        compound='left',
        font=ctk.CTkFont('Segoe UI', size=12, weight='bold'),
        height=28,
        width=120,
        corner_radius=6,
        fg_color='transparent',
        hover_color='#242424',
        border_width=1,
        border_color='#444444',
        command=lambda: self.select_tab('config'),
    )
    self.btn_tab_config.grid(row=0, column=3, padx=4, pady=10, sticky='e')

    self.btn_tab_ffmpeg = ctk.CTkButton(
        self.navbar_frame,
        text=' Ferramentas',
        image=self._get_icon('tool'),
        compound='left',
        font=ctk.CTkFont('Segoe UI', size=12, weight='bold'),
        height=28,
        width=115,
        corner_radius=6,
        fg_color='transparent',
        hover_color='#242424',
        border_width=1,
        border_color='#444444',
        command=lambda: self.select_tab('ffmpeg'),
    )
    self.btn_tab_ffmpeg.grid(row=0, column=4, padx=(4, 14), pady=10, sticky='e')

  def select_tab(self, tab_name):
    if tab_name == 'baixador':
      self.btn_tab_baixador.configure(
          fg_color=self.c_orange_main, text_color='white', border_width=0
      )
      self.btn_tab_config.configure(
          fg_color='transparent', border_width=1, text_color='#CCCCCC'
      )
      self.btn_tab_ffmpeg.configure(
          fg_color='transparent', border_width=1, text_color='#CCCCCC'
      )
      self.frame_config.grid_remove()
      self.frame_ffmpeg.grid_remove()
      self.frame_baixador.grid(row=1, column=0, sticky='nsew', padx=10, pady=10)
    elif tab_name == 'config':
      self.btn_tab_config.configure(
          fg_color=self.c_orange_main, text_color='white', border_width=0
      )
      self.btn_tab_baixador.configure(
          fg_color='transparent', border_width=1, text_color='#CCCCCC'
      )
      self.btn_tab_ffmpeg.configure(
          fg_color='transparent', border_width=1, text_color='#CCCCCC'
      )
      self.frame_baixador.grid_remove()
      self.frame_ffmpeg.grid_remove()
      self.frame_config.grid(row=1, column=0, sticky='nsew', padx=10, pady=10)
    elif tab_name == 'ffmpeg':
      self.btn_tab_ffmpeg.configure(
          fg_color=self.c_orange_main, text_color='white', border_width=0
      )
      self.btn_tab_baixador.configure(
          fg_color='transparent', border_width=1, text_color='#CCCCCC'
      )
      self.btn_tab_config.configure(
          fg_color='transparent', border_width=1, text_color='#CCCCCC'
      )
      self.frame_baixador.grid_remove()
      self.frame_config.grid_remove()
      self.frame_ffmpeg.grid(row=1, column=0, sticky='nsew', padx=10, pady=10)

  # -------------------------------------------------------------------------
  # TELA 1: ABA BAIXADOR (CONTROLES EM 1 LINHA E BOTÃO INTEGRADO)
  # -------------------------------------------------------------------------
  def _build_baixador_frame(self):
    self.frame_baixador = ctk.CTkFrame(
        self, fg_color='transparent', corner_radius=0
    )
    self.frame_baixador.grid_columnconfigure(0, weight=1)
    self.frame_baixador.grid_rowconfigure(1, weight=1)

    top_search_frame = ctk.CTkFrame(
        self.frame_baixador,
        fg_color=self.c_bg_panel,
        corner_radius=8,
        border_width=1,
        border_color=self.c_border,
    )
    top_search_frame.grid(row=0, column=0, sticky='ew', pady=(0, 8))
    top_search_frame.grid_columnconfigure(1, weight=1)

    lbl_url = ctk.CTkLabel(
        top_search_frame,
        text='Link:',
        font=ctk.CTkFont('Segoe UI', size=12, weight='bold'),
        text_color='#FFFFFF',
    )
    lbl_url.grid(row=0, column=0, padx=(10, 6), pady=10, sticky='w')

    self.entry_url = ctk.CTkEntry(
        top_search_frame,
        placeholder_text='Cole o link da série ou filme aqui...',
        height=28,
        fg_color=self.c_bg_input,
        border_color=self.c_border_in,
        font=ctk.CTkFont('Segoe UI', size=12),
    )
    self.entry_url.grid(row=0, column=1, padx=4, pady=10, sticky='ew')
    self.entry_url.bind('<Return>', lambda e: self.fetch_catalog())

    self.btn_search = ctk.CTkButton(
        top_search_frame,
        text=' Buscar',
        image=self._get_icon('search', size_tuple=(16, 16)),
        compound='left',
        width=85,
        height=28,
        font=ctk.CTkFont('Segoe UI', size=12, weight='bold'),
        fg_color=self.c_orange_main,
        hover_color=self.c_orange_hover,
        command=self.fetch_catalog,
    )
    self.btn_search.grid(row=0, column=2, padx=10, pady=10, sticky='e')

    center_list_frame = ctk.CTkFrame(
        self.frame_baixador,
        fg_color=self.c_bg_panel,
        corner_radius=8,
        border_width=1,
        border_color=self.c_border,
    )
    center_list_frame.grid(row=1, column=0, sticky='nsew', pady=(0, 8))
    center_list_frame.grid_columnconfigure(0, weight=1)
    center_list_frame.grid_rowconfigure(1, weight=1)

    # -----------------------------------------------------------------------
    # TOOLBAR EM UMA LINHA COM BOTÃO DE SELEÇÃO INTEGRADO/ALTERNÁVEL
    # -----------------------------------------------------------------------
    selection_toolbar = ctk.CTkFrame(
        center_list_frame,
        fg_color='#121214',
        corner_radius=6,
        border_width=1,
        border_color='#222225',
    )
    selection_toolbar.grid(row=0, column=0, sticky='ew', padx=8, pady=8)

    self.btn_toggle_sel = ctk.CTkButton(
        selection_toolbar,
        text='✕ Desmarcar',
        width=95,
        height=26,
        font=ctk.CTkFont('Segoe UI', size=11, weight='bold'),
        fg_color='#2E2E34',
        hover_color='#3E3E46',
        command=self.toggle_select_all,
    )
    self.btn_toggle_sel.pack(side='left', padx=(8, 4), pady=6)

    lbl_s_filter = ctk.CTkLabel(
        selection_toolbar,
        text='|  Temp:',
        font=ctk.CTkFont('Segoe UI', size=11, weight='bold'),
        text_color='#999999',
    )
    lbl_s_filter.pack(side='left', padx=(4, 4))

    self.combo_seasons = ctk.CTkOptionMenu(
        selection_toolbar,
        values=['Todas as Temporadas'],
        width=135,
        height=26,
        font=ctk.CTkFont('Segoe UI', size=11),
        fg_color=self.c_bg_input,
        button_color=self.c_orange_main,
        button_hover_color=self.c_orange_hover,
        command=self.filter_by_season,
    )
    self.combo_seasons.pack(side='left', padx=2)

    lbl_range = ctk.CTkLabel(
        selection_toolbar,
        text='|  Ep:',
        font=ctk.CTkFont('Segoe UI', size=11, weight='bold'),
        text_color='#999999',
    )
    lbl_range.pack(side='left', padx=(6, 4))

    self.entry_ep_from = ctk.CTkEntry(
        selection_toolbar,
        width=34,
        height=26,
        placeholder_text='1',
        font=ctk.CTkFont('Segoe UI', size=11, weight='bold'),
        justify='center',
        fg_color=self.c_bg_input,
        border_color=self.c_border_in,
    )
    self.entry_ep_from.pack(side='left', padx=2)

    lbl_range_to = ctk.CTkLabel(
        selection_toolbar,
        text='a',
        font=ctk.CTkFont('Segoe UI', size=11),
        text_color='#888888',
    )
    lbl_range_to.pack(side='left', padx=2)

    self.entry_ep_to = ctk.CTkEntry(
        selection_toolbar,
        width=34,
        height=26,
        placeholder_text='24',
        font=ctk.CTkFont('Segoe UI', size=11, weight='bold'),
        justify='center',
        fg_color=self.c_bg_input,
        border_color=self.c_border_in,
    )
    self.entry_ep_to.pack(side='left', padx=2)

    btn_apply_range = ctk.CTkButton(
        selection_toolbar,
        text='Filtrar',
        width=68,
        height=26,
        font=ctk.CTkFont('Segoe UI', size=11, weight='bold'),
        fg_color='#D97706',
        hover_color='#B45309',
        command=self.select_by_range,
    )
    btn_apply_range.pack(side='left', padx=(4, 8), pady=6)

    # -----------------------------------------------------------------------
    # LISTA COM ROLAGEM DOS EPISÓDIOS
    # -----------------------------------------------------------------------
    self.scroll_list = ctk.CTkScrollableFrame(
        center_list_frame,
        fg_color='#111113',
        corner_radius=6,
        border_width=1,
        border_color='#1E1E22',
    )
    self.scroll_list.grid_columnconfigure(0, weight=1)
    self.scroll_list.grid(row=1, column=0, sticky='nsew', padx=8, pady=(0, 8))

    self.lbl_list_status = ctk.CTkLabel(
        self.scroll_list,
        text=(
            'Nenhuma obra listada ainda.\nCole o link na barra superior e aperte'
            ' em Buscar.'
        ),
        font=ctk.CTkFont('Segoe UI', size=12, slant='italic'),
        text_color='#777777',
    )
    self.lbl_list_status.grid(row=0, column=0, pady=45)

    # -----------------------------------------------------------------------
    # CONTROLES INFERIORES E MOTOR COM TURBO
    # -----------------------------------------------------------------------
    bottom_control_frame = ctk.CTkFrame(
        self.frame_baixador,
        fg_color=self.c_bg_panel,
        corner_radius=8,
        border_width=1,
        border_color=self.c_border,
    )
    bottom_control_frame.grid(row=2, column=0, sticky='ew', pady=0)
    bottom_control_frame.grid_columnconfigure(1, weight=1)
    bottom_control_frame.grid_columnconfigure(2, weight=1)

    lbl_lang = ctk.CTkLabel(
        bottom_control_frame,
        text='Áudio:',
        font=ctk.CTkFont('Segoe UI', size=11, weight='bold'),
        text_color='#FFFFFF',
    )
    lbl_lang.grid(row=0, column=0, padx=(10, 4), pady=8, sticky='w')

    self.combo_lang = ctk.CTkOptionMenu(
        bottom_control_frame,
        values=['Dublado', 'Legendado', 'Ambos (Dub + Leg)'],
        width=140,
        height=26,
        font=ctk.CTkFont('Segoe UI', size=11),
        fg_color=self.c_bg_input,
        button_color=self.c_orange_main,
        button_hover_color=self.c_orange_hover,
    )
    self.combo_lang.set(self.config_mgr.get('default_lang', 'Dublado'))
    self.combo_lang.grid(row=0, column=1, padx=2, pady=8, sticky='w')

    curr_folder = self.config_mgr.get('default_folder', 'Muyo Download')
    folder_disp = os.path.basename(curr_folder) or curr_folder
    if len(folder_disp) > 16:
      folder_disp = folder_disp[:14] + '..'
    self.lbl_target_folder = ctk.CTkLabel(
        bottom_control_frame,
        text=f'Pasta: {folder_disp}',
        font=ctk.CTkFont('Segoe UI', size=11, weight='bold'),
        text_color='#DDDDDD',
        anchor='e',
    )
    self.lbl_target_folder.grid(
        row=0, column=2, padx=(4, 6), pady=8, sticky='e'
    )

    btn_browse = ctk.CTkButton(
        bottom_control_frame,
        text='Pasta...',
        width=70,
        height=24,
        font=ctk.CTkFont('Segoe UI', size=11),
        fg_color='#2E2E34',
        hover_color='#3E3E46',
        command=self.browse_output_folder,
    )
    btn_browse.grid(row=0, column=3, padx=(0, 10), pady=8, sticky='e')

    execution_box = ctk.CTkFrame(
        bottom_control_frame,
        fg_color='#111113',
        corner_radius=6,
        border_width=1,
        border_color='#222225',
    )
    execution_box.grid(
        row=1, column=0, columnspan=4, sticky='ew', padx=8, pady=(0, 8)
    )
    execution_box.grid_columnconfigure(0, weight=1)

    self.btn_start_dl = ctk.CTkButton(
        execution_box,
        text=' INICIAR DOWNLOAD (0)',
        image=self._get_icon('download', size_tuple=(20, 20)),
        compound='left',
        height=34,
        font=ctk.CTkFont('Segoe UI', size=12, weight='bold'),
        fg_color=self.c_orange_main,
        hover_color=self.c_orange_hover,
        command=self.start_or_add_download,
    )
    self.btn_start_dl.grid(
        row=0, column=0, padx=(8, 6), pady=(10, 4), sticky='ew'
    )

    self.btn_cancel_dl = ctk.CTkButton(
        execution_box,
        text=' Cancelar',
        image=self._get_icon('stop', size_tuple=(18, 18)),
        compound='left',
        width=95,
        height=34,
        font=ctk.CTkFont('Segoe UI', size=12, weight='bold'),
        fg_color='#DC2626',
        hover_color='#B91C1C',
        command=self.cancel_download_process,
        state='disabled',
    )
    self.btn_cancel_dl.grid(
        row=0, column=1, padx=(0, 8), pady=(10, 4), sticky='e'
    )

    self.progress_bar = ctk.CTkProgressBar(
        execution_box, height=10, corner_radius=4, progress_color=self.c_green
    )
    self.progress_bar.grid(
        row=1, column=0, columnspan=2, padx=8, pady=(4, 4), sticky='ew'
    )
    self.progress_bar.set(0.0)

    self.lbl_progress_info = ctk.CTkLabel(
        execution_box,
        text='Aguardando acionamento da fila...',
        font=ctk.CTkFont('Segoe UI', size=11, weight='bold'),
        text_color='#888888',
    )
    self.lbl_progress_info.grid(
        row=2, column=0, columnspan=2, padx=8, pady=(0, 8), sticky='w'
    )

  # -------------------------------------------------------------------------
  # TELA 2: ABA CONFIGURAÇÕES (RESPONSIVO & SEÇÃO DE ATUALIZAÇÃO)
  # -------------------------------------------------------------------------
  def _build_configuracoes_frame(self):
    self.frame_config = ctk.CTkFrame(
        self, fg_color='transparent', corner_radius=0
    )
    self.frame_config.grid_columnconfigure(0, weight=1)

    panel_config = ctk.CTkFrame(
        self.frame_config,
        fg_color=self.c_bg_panel,
        corner_radius=8,
        border_width=1,
        border_color=self.c_border,
    )
    panel_config.pack(fill='both', expand=True, padx=8, pady=8)

    # Título Principal da Aba
    cfg_logo_img = self._get_logo_ctk_image(size_tuple=(22, 22))
    title_lbl = ctk.CTkLabel(
        panel_config,
        text=' Preferências e Credenciais',
        image=cfg_logo_img if cfg_logo_img else None,
        compound='left' if cfg_logo_img else 'center',
        font=ctk.CTkFont('Segoe UI', size=16, weight='bold'),
        text_color=self.c_orange_main,
    )
    title_lbl.pack(pady=(16, 10), padx=18, anchor='w')

    # Tabela em Grade: Coluna 0 = Info (Título + Subtítulo Pequeno), Coluna 1 = Controles à direita
    table = ctk.CTkFrame(panel_config, fg_color='transparent')
    table.pack(fill='x', padx=18, pady=(0, 10))
    table.grid_columnconfigure(0, weight=1)
    table.grid_columnconfigure(1, weight=0)

    # --- ITEM 1: E-MAIL DE ACESSO ---
    info_email = ctk.CTkFrame(table, fg_color='transparent')
    info_email.grid(row=0, column=0, sticky='w', pady=(4, 12))
    ctk.CTkLabel(
        info_email,
        text='E-mail do Usuário',
        font=ctk.CTkFont('Segoe UI', size=13, weight='bold'),
        text_color='#EEEEEE',
    ).pack(anchor='w')
    ctk.CTkLabel(
        info_email,
        text='Necessário apenas em sites com conta VIP',
        font=ctk.CTkFont('Segoe UI', size=11),
        text_color='#888888',
    ).pack(anchor='w')

    self.cfg_email = ctk.CTkEntry(
        table,
        placeholder_text='Seu e-mail cadastrado...',
        width=250,
        height=32,
        font=ctk.CTkFont('Segoe UI', size=12),
        fg_color=self.c_bg_input,
        border_color=self.c_border_in,
    )
    self.cfg_email.insert(0, self.config_mgr.get('email', ''))
    self.cfg_email.grid(row=0, column=1, sticky='e', pady=(4, 12))

    # --- ITEM 2: SENHA DE LOGIN ---
    info_pwd = ctk.CTkFrame(table, fg_color='transparent')
    info_pwd.grid(row=1, column=0, sticky='w', pady=(0, 12))
    ctk.CTkLabel(
        info_pwd,
        text='Senha de Acesso',
        font=ctk.CTkFont('Segoe UI', size=13, weight='bold'),
        text_color='#EEEEEE',
    ).pack(anchor='w')
    ctk.CTkLabel(
        info_pwd,
        text='Sua senha do site para autenticação',
        font=ctk.CTkFont('Segoe UI', size=11),
        text_color='#888888',
    ).pack(anchor='w')

    self.cfg_pwd = ctk.CTkEntry(
        table,
        placeholder_text='Sua senha secreta...',
        width=250,
        height=32,
        font=ctk.CTkFont('Segoe UI', size=12),
        fg_color=self.c_bg_input,
        border_color=self.c_border_in,
        show='•',
    )
    self.cfg_pwd.insert(0, self.config_mgr.get('password', ''))
    self.cfg_pwd.grid(row=1, column=1, sticky='e', pady=(0, 12))

    # --- ITEM 3: IDIOMA PADRÃO ---
    info_lang = ctk.CTkFrame(table, fg_color='transparent')
    info_lang.grid(row=2, column=0, sticky='w', pady=(0, 12))
    ctk.CTkLabel(
        info_lang,
        text='Idioma Padrão',
        font=ctk.CTkFont('Segoe UI', size=13, weight='bold'),
        text_color='#EEEEEE',
    ).pack(anchor='w')
    ctk.CTkLabel(
        info_lang,
        text='Áudio prioritário nas novas pesquisas',
        font=ctk.CTkFont('Segoe UI', size=11),
        text_color='#888888',
    ).pack(anchor='w')

    self.cfg_combo_lang = ctk.CTkOptionMenu(
        table,
        values=['Dublado', 'Legendado', 'Ambos (Dub + Leg)'],
        width=250,
        height=32,
        font=ctk.CTkFont('Segoe UI', size=12),
        fg_color=self.c_bg_input,
        button_color=self.c_orange_main,
        button_hover_color=self.c_orange_hover,
    )
    self.cfg_combo_lang.set(self.config_mgr.get('default_lang', 'Dublado'))
    self.cfg_combo_lang.grid(row=2, column=1, sticky='e', pady=(0, 12))

    # --- ITEM 4: PASTA DE DOWNLOADS ---
    info_dir = ctk.CTkFrame(table, fg_color='transparent')
    info_dir.grid(row=3, column=0, sticky='w', pady=(0, 12))
    ctk.CTkLabel(
        info_dir,
        text='Pasta de Downloads',
        font=ctk.CTkFont('Segoe UI', size=13, weight='bold'),
        text_color='#EEEEEE',
    ).pack(anchor='w')
    ctk.CTkLabel(
        info_dir,
        text='Local onde os vídeos são salvos',
        font=ctk.CTkFont('Segoe UI', size=11),
        text_color='#888888',
    ).pack(anchor='w')

    dir_box = ctk.CTkFrame(table, width=250, fg_color='transparent')
    dir_box.grid(row=3, column=1, sticky='e', pady=(0, 12))

    self.cfg_dir_entry = ctk.CTkEntry(
        dir_box,
        width=168,
        height=32,
        font=ctk.CTkFont('Segoe UI', size=11),
        fg_color=self.c_bg_input,
        border_color=self.c_border_in,
    )
    self.cfg_dir_entry.insert(0, self.config_mgr.get('default_folder', ''))
    self.cfg_dir_entry.pack(side='left', padx=(0, 6))

    btn_cfg_browse = ctk.CTkButton(
        dir_box,
        text='Procurar',
        height=32,
        width=76,
        font=ctk.CTkFont('Segoe UI', size=11, weight='bold'),
        fg_color='#2E2E34',
        hover_color='#3E3E46',
        command=self._cfg_browse_folder,
    )
    btn_cfg_browse.pack(side='left')

    # --- BOTÃO SALVAR ---
    action_box = ctk.CTkFrame(panel_config, fg_color='transparent')
    action_box.pack(fill='x', padx=18, pady=(4, 16))

    btn_save = ctk.CTkButton(
        action_box,
        text=' Salvar Alterações',
        image=self._get_icon('save', size_tuple=(20, 20)),
        compound='left',
        font=ctk.CTkFont('Segoe UI', size=13, weight='bold'),
        height=34,
        width=180,
        fg_color=self.c_orange_main,
        hover_color=self.c_orange_hover,
        command=self.save_settings,
    )
    btn_save.pack(side='left', padx=(0, 12))

    self.lbl_cfg_feedback = ctk.CTkLabel(
        action_box, text='', font=ctk.CTkFont('Segoe UI', size=12, weight='bold')
    )
    self.lbl_cfg_feedback.pack(side='left', pady=4)

    # --- SEÇÃO INFERIOR: ATUALIZAÇÃO DO SISTEMA ---
    sep = ctk.CTkFrame(panel_config, height=1, fg_color=self.c_border)
    sep.pack(fill='x', padx=18, pady=(4, 10))

    upd_table = ctk.CTkFrame(panel_config, fg_color='transparent')
    upd_table.pack(fill='x', padx=18, pady=(0, 10))
    upd_table.grid_columnconfigure(0, weight=1)

  # -------------------------------------------------------------------------
  # TELA 3: ABA FERRAMENTAS FFMPEG
  # -------------------------------------------------------------------------
  def _build_ffmpeg_frame(self):
    self.frame_ffmpeg = ctk.CTkFrame(self, fg_color='transparent', corner_radius=0)
    self.frame_ffmpeg.grid_columnconfigure(0, weight=1)
    self.frame_ffmpeg.grid_rowconfigure(2, weight=1) # Faz o terminal expandir

    # HEADER
    header_frame = ctk.CTkFrame(self.frame_ffmpeg, fg_color='transparent')
    header_frame.grid(row=0, column=0, sticky='ew', padx=20, pady=(10, 5))
    lbl_title = ctk.CTkLabel(
        header_frame,
        text='Central de Conversão FFmpeg',
        font=ctk.CTkFont('Segoe UI', size=20, weight='bold'),
        text_color='white'
    )
    lbl_title.pack(anchor='w')
    lbl_subtitle = ctk.CTkLabel(
        header_frame,
        text='Converta vídeos, separe áudios ou extraia músicas com alta velocidade.',
        font=ctk.CTkFont('Segoe UI', size=13),
        text_color='#AAAAAA'
    )
    lbl_subtitle.pack(anchor='w')

    # PANEL CONTROLS
    panel = ctk.CTkFrame(
        self.frame_ffmpeg,
        fg_color=self.c_bg_panel,
        corner_radius=8,
        border_width=1,
        border_color=self.c_border
    )
    panel.grid(row=1, column=0, sticky='ew', padx=20, pady=10)
    panel.grid_columnconfigure(1, weight=1)

    # 1. Input File
    lbl_file = ctk.CTkLabel(panel, text='Arquivo de Entrada:', font=ctk.CTkFont(weight='bold'))
    lbl_file.grid(row=0, column=0, padx=15, pady=(15, 10), sticky='w')

    self.entry_ff_file = ctk.CTkEntry(
        panel,
        placeholder_text='Selecione um arquivo de vídeo ou áudio...',
        height=32,
        fg_color='#1E1E24',
        border_color='#333333'
    )
    self.entry_ff_file.grid(row=0, column=1, padx=(0, 10), pady=(15, 10), sticky='ew')

    def _browse_ff_file():
      path = filedialog.askopenfilename(
          title='Selecione o arquivo multimídia',
          filetypes=[("Mídia", "*.mkv *.mp4 *.avi *.webm *.ts *.mp3 *.wav"), ("Todos", "*.*")]
      )
      if path:
        self.entry_ff_file.delete(0, 'end')
        self.entry_ff_file.insert(0, path)

    btn_browse = ctk.CTkButton(
        panel, text='Procurar...', width=90, height=32,
        fg_color=self.c_orange_main, hover_color=self.c_orange_hover,
        command=_browse_ff_file
    )
    btn_browse.grid(row=0, column=2, padx=(0, 15), pady=(15, 10), sticky='e')

    # 2. Action
    lbl_action = ctk.CTkLabel(panel, text='Ferramenta/Ação:', font=ctk.CTkFont(weight='bold'))
    lbl_action.grid(row=1, column=0, padx=15, pady=(0, 15), sticky='w')

    self.ff_action_var = ctk.StringVar(value='Converter para MP4 (Padrão)')
    actions = [
        'Converter para MP4 (Padrão)',
        'Separar Idiomas (Dual Áudio para MP4s isolados)',
        'Extrair Áudio (MP3)',
        'Extrair Áudio (WAV)'
    ]
    self.combo_ff_action = ctk.CTkComboBox(
        panel,
        values=actions,
        variable=self.ff_action_var,
        height=32,
        dropdown_font=ctk.CTkFont('Segoe UI', size=13),
        fg_color='#1E1E24',
        border_color='#333333',
        button_color=self.c_orange_main,
        button_hover_color=self.c_orange_hover,
        dropdown_hover_color=self.c_orange_hover
    )
    self.combo_ff_action.grid(row=1, column=1, columnspan=2, padx=(0, 15), pady=(0, 15), sticky='ew')

    # TERMINAL PANEL
    term_panel = ctk.CTkFrame(
        self.frame_ffmpeg,
        fg_color='#111115',
        corner_radius=8,
        border_width=1,
        border_color='#333333'
    )
    term_panel.grid(row=2, column=0, sticky='nsew', padx=20, pady=(0, 10))
    term_panel.grid_rowconfigure(1, weight=1)
    term_panel.grid_columnconfigure(0, weight=1)

    term_header = ctk.CTkLabel(
        term_panel, text='Terminal de Processamento', 
        font=ctk.CTkFont('Consolas', size=12, weight='bold'), text_color='#555555'
    )
    term_header.grid(row=0, column=0, sticky='w', padx=10, pady=(5, 0))

    self.ff_terminal = ctk.CTkTextbox(
        term_panel, 
        font=ctk.CTkFont('Consolas', size=13),
        fg_color='transparent',
        text_color='#00FF00',
        wrap='word'
    )
    self.ff_terminal.grid(row=1, column=0, sticky='nsew', padx=5, pady=5)
    self.ff_terminal.insert('end', 'Aguardando comandos...\n')
    self.ff_terminal.configure(state='disabled')

    # BOTTOM BUTTON
    btn_frame = ctk.CTkFrame(self.frame_ffmpeg, fg_color='transparent')
    btn_frame.grid(row=3, column=0, sticky='ew', padx=20, pady=(0, 15))
    
    self.btn_ff_start = ctk.CTkButton(
        btn_frame,
        text=' INICIAR PROCESSAMENTO',
        image=self._get_icon('play', size_tuple=(20, 20)),
        compound='left',
        font=ctk.CTkFont('Segoe UI', size=14, weight='bold'),
        height=42,
        fg_color=self.c_orange_main,
        hover_color=self.c_orange_hover,
        command=self._start_ffmpeg_process
    )
    self.btn_ff_start.pack(fill='x')

  def _ff_log(self, msg):
    self.ff_terminal.configure(state='normal')
    self.ff_terminal.insert('end', f"> {msg}\n")
    self.ff_terminal.see('end')
    self.ff_terminal.configure(state='disabled')

  def _start_ffmpeg_process(self):
    input_file = self.entry_ff_file.get().strip()
    if not input_file or not os.path.exists(input_file):
        self.show_notification('Erro', 'Selecione um arquivo de entrada válido.', type='warning')
        return

    action = self.ff_action_var.get()
    self.btn_ff_start.configure(state='disabled', text='⏳ PROCESSANDO...')
    
    self.ff_terminal.configure(state='normal')
    self.ff_terminal.delete('1.0', 'end')
    self.ff_terminal.configure(state='disabled')
    self._ff_log("Inicializando motor FFmpeg...")
    
    def cb(msg):
        self.after(0, lambda: self._ff_log(msg))
        
    threading.Thread(target=self._run_ffmpeg_task, args=(input_file, action, cb), daemon=True).start()

  def _run_ffmpeg_task(self, input_file, action, cb):
    try:
        base, ext = os.path.splitext(input_file)
        success = False
        if 'Converter para MP4' in action:
            out_file = base + '_Convertido.mp4'
            success = ffmpeg_engine.convert_to_mp4(input_file, out_file, status_cb=cb)
        elif 'Separar Idiomas' in action:
            out_dir = base + '_Separados'
            success = ffmpeg_engine.split_dual_audio_video(input_file, out_dir, status_cb=cb)
        elif 'Extrair Áudio' in action:
            fmt = 'mp3' if 'MP3' in action else 'wav'
            out_file = base + f'_Audio.{fmt}'
            success = ffmpeg_engine.extract_audio(input_file, out_file, format=fmt, status_cb=cb)
            
        if success:
            cb("✔️ OPERAÇÃO CONCLUÍDA COM SUCESSO!")
            self.after(0, lambda: self.show_notification('Sucesso!', 'Processamento concluído.', type='success'))
        else:
            cb("❌ FALHA NO PROCESSAMENTO!")
            self.after(0, lambda: self.show_notification('Aviso', 'Processamento falhou ou ocorreu algum erro.', type='warning'))
    except Exception as e:
        cb(f"Erro fatal na thread FFmpeg: {e}")
    finally:
        self.after(0, lambda: self.btn_ff_start.configure(state='normal', text='INICIAR PROCESSAMENTO'))

    info_upd = ctk.CTkFrame(upd_table, fg_color='transparent')
    info_upd.grid(row=0, column=0, sticky='w')
    ctk.CTkLabel(
        info_upd,
        text='Atualização do Sistema',
        font=ctk.CTkFont('Segoe UI', size=13, weight='bold'),
        text_color=self.c_orange_main,
    ).pack(anchor='w')
    self.lbl_upd_status = ctk.CTkLabel(
        info_upd,
        text=f'Versão Atual: v{updater.APP_VERSION}',
        font=ctk.CTkFont('Segoe UI', size=11),
        text_color='#888888',
    )
    self.lbl_upd_status.pack(anchor='w')

    self.btn_check_upd = ctk.CTkButton(
        upd_table,
        text='🔄 Buscar Atualização',
        font=ctk.CTkFont('Segoe UI', size=12, weight='bold'),
        height=32,
        width=160,
        fg_color='#2A2A2E',
        hover_color='#36363B',
        text_color='#DDDDDD',
        command=lambda: threading.Thread(target=self._manual_update_check, daemon=True).start(),
    )
    self.btn_check_upd.grid(row=0, column=1, sticky='e')

  def _cfg_browse_folder(self):
    chosen = filedialog.askdirectory(title='Selecione a Pasta Raiz Padrão')
    if chosen:
      self.cfg_dir_entry.delete(0, 'end')
      self.cfg_dir_entry.insert(0, chosen)

  def save_settings(self):
    new_data = {
        'email': self.cfg_email.get().strip(),
        'password': self.cfg_pwd.get().strip(),
        'default_lang': self.cfg_combo_lang.get(),
        'default_folder': self.cfg_dir_entry.get().strip(),
    }
    ok = self.config_mgr.save_config(new_data)
    if ok:
      self.auth.email = new_data['email']
      self.auth.password = new_data['password']
      self.combo_lang.set(new_data['default_lang'])
      folder_disp = os.path.basename(new_data['default_folder']) or new_data['default_folder']
      if len(folder_disp) > 16:
        folder_disp = folder_disp[:14] + '..'
      self.lbl_target_folder.configure(text=f'📁 {folder_disp}')
      self.lbl_cfg_feedback.configure(
          text='✔️ Salvo com sucesso!', text_color=self.c_green
      )
      self.after(4000, lambda: self.lbl_cfg_feedback.configure(text=''))
      self.after(200, self._auto_connect_in_background)
    else:
      self.show_notification('Erro', 'Falha ao gravar arquivo de configuração.', type='error')

  # -------------------------------------------------------------------------
  # SISTEMA AVANÇADO DE ATUALIZAÇÕES VIA GITHUB
  # -------------------------------------------------------------------------
  def _startup_update_check(self):
    self._check_for_updates(silent_if_latest=True, auto_update=True)

  def _manual_update_check(self):
    self.btn_check_upd.configure(text='⏳ Consultando...', state='disabled')
    self.lbl_upd_status.configure(text='Buscando novas versões...', text_color=self.c_orange_main)
    self._check_for_updates(silent_if_latest=False, auto_update=True)
    self.btn_check_upd.configure(text='🔄 Buscar Atualização', state='normal')

  def _check_for_updates(self, silent_if_latest: bool = False, auto_update: bool = False):
    # 1. Modo Desenvolvimento: Atualização Direta no Git se rodar por script python na pasta com .git
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    git_dir = os.path.join(root_dir, '.git')
    if not updater.is_frozen() and os.path.isdir(git_dir):
      try:
        flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        subprocess.check_call(["git", "fetch"], cwd=root_dir, timeout=10, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=flags)
        local_hash = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root_dir, text=True, creationflags=flags).strip()
        upstream_hash = subprocess.check_output(["git", "rev-parse", "@{u}"], cwd=root_dir, text=True, creationflags=flags).strip()
        if local_hash != upstream_hash:
          if auto_update:
            self.show_notification("Atualizando Git", "Baixando nova versão do código...", type='info')
            subprocess.check_call(["git", "reset", "--hard", "HEAD"], cwd=root_dir, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=flags)
            subprocess.check_call(["git", "pull"], cwd=root_dir, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=flags)
            os.execv(sys.executable, [sys.executable] + sys.argv)
          else:
            self.show_notification("Atualização Disponível", "Nova versão disponível no Git. Use o botão Buscar Atualização.", type='info')
          return
        else:
          if not silent_if_latest:
            self.lbl_upd_status.configure(text='✔️ Código Git na versão mais recente!', text_color=self.c_green)
            self.show_notification("Tudo Atualizado!", f"Você já está na versão mais recente do Git (v{updater.APP_VERSION}).", type='success')
          return
      except Exception as e:
        print("Aviso na checagem Git:", e)
        # Se falhou checagem git, continua para checagem da release via API

    # 2. Checagem Oficial via API do GitHub (para o .exe ou fallback)
    try:
      release_data = updater.fetch_latest_release()
    except Exception as exc:
      if not silent_if_latest:
        self.lbl_upd_status.configure(text='❌ Erro na consulta ao GitHub.', text_color='#EF4444')
        self.show_notification("Sem Conexão", "Não foi possível contatar a API do GitHub.", type='error')
      return

    latest_tag = str(release_data.get("tag_name") or "").strip()
    latest_name = str(release_data.get("name") or latest_tag or "Última Versão")
    latest_url = str(release_data.get("html_url") or updater.GITHUB_RELEASES_URL)

    if updater.version_tuple(latest_tag) > updater.version_tuple(updater.APP_VERSION):
      if auto_update:
        if updater.is_frozen():
          self.lbl_upd_status.configure(text='Baixando atualização autônoma...', text_color=self.c_orange_main)
          self.show_notification("Nova Versão!", f"Baixando Muyo Download {latest_tag}...\nO programa vai reiniciar sozinho.", type='info', duration_ms=6000)
          def _upd_progress(rc, tot, msg_str):
            self.after(0, lambda: self.lbl_upd_status.configure(text=msg_str, text_color='#FDBA74'))

          ok, msg = updater.self_update_from_release(release_data, progress_cb=_upd_progress)
          if ok:
            self.destroy()
            os._exit(0)
          else:
            self.show_notification("Erro na Atualização", f"Falha ao aplicar update:\n{msg[:50]}...", type='error', duration_ms=6000)
            webbrowser.open(latest_url, new=2)
        else:
          self.show_notification("Nova Versão Disponível", f"Abra o link oficial para baixar a versão {latest_tag}.", type='warning')
          webbrowser.open(latest_url, new=2)
      else:
        self.show_notification("Nova Versão Disponível", f"A versão {latest_tag} está disponível no GitHub.", type='info')
    else:
      if not silent_if_latest:
        self.lbl_upd_status.configure(text=f'✔️ App atualizado (v{updater.APP_VERSION})!', text_color=self.c_green)
        self.show_notification("App Atualizado!", f"Você já executa a versão mais recente (v{updater.APP_VERSION}).", type='success')


  # -------------------------------------------------------------------------
  # CONEXÃO INTERNET SILENCIOSA & PESQUISA DE OBRAS
  # -------------------------------------------------------------------------
  def _auto_connect_in_background(self):
    if self.auth.email and self.auth.password:
      threading.Thread(target=self._do_auth, daemon=True).start()

  def _do_auth(self):
    self.auth.login()

  def browse_output_folder(self):
    cur_dir = self.config_mgr.get(
        'default_folder', os.path.expanduser('~')
    )
    folder = filedialog.askdirectory(
        initialdir=cur_dir, title='Escolha onde salvar os vídeos'
    )
    if folder:
      self.config_mgr.set('default_folder', folder)
      folder_disp = os.path.basename(folder) or folder
      if len(folder_disp) > 16:
        folder_disp = folder_disp[:14] + '..'
      self.lbl_target_folder.configure(text=f'📁 {folder_disp}')

  def fetch_catalog(self):
    url = self.entry_url.get().strip()
    if not url:
      self.show_notification(
          'Aviso',
          'Por favor, cole o link do filme ou série na barra de pesquisa!',
          type='warning'
      )
      return

    if 'encontrei.info' in url.lower() and (not self.auth.email or not self.auth.password):
      self.show_notification(
          'Login Necessário',
          'O site Encontrei.info é exclusivo para membros e exige login.\n\nAcesse a aba "Configurações", preencha seu E-mail/Senha e clique em "Salvar"!',
          type='warning',
          duration_ms=6000
      )
      self.select_tab('config')
      self.cfg_email.focus_set()
      return

    if not self.auth.is_authenticated and self.auth.email and self.auth.password:
      self._auto_connect_in_background()

    self.btn_search.configure(
        text='⏳ Lendo...', state='disabled', fg_color='#444444'
    )
    self.lbl_list_status.configure(
        text='🔍 Extraindo episódios do catálogo...',
        text_color=self.c_orange_main,
    )
    self.lbl_list_status.grid(row=0, column=0, pady=45)
    for w in list(self.checkbox_widgets.values()):
      w.destroy()
    self.checkbox_widgets.clear()
    self.items_list.clear()

    threading.Thread(
        target=self._async_parse_catalog, args=(url,), daemon=True
    ).start()

  def _async_parse_catalog(self, url):
    result = self.parser.parse_url(url)
    self.after(0, self._render_catalog_items, result)

  def _render_catalog_items(self, result):
    self.btn_search.configure(
        text='🔍 Buscar', state='normal', fg_color=self.c_orange_main
    )

    if 'error' in result:
      self.lbl_list_status.configure(
          text=f"❌ Erro na leitura:\n{result['error']}", text_color='#EF4444'
      )
      self.lbl_list_status.grid(row=0, column=0, pady=45)
      return

    items = result.get('items', [])
    if len(items) == 0:
      self.lbl_list_status.configure(
          text='⚠️ Nenhum vídeo ou episódio encontrado nessa URL.',
          text_color='#FBBF24',
      )
      self.lbl_list_status.grid(row=0, column=0, pady=45)
      return

    self.lbl_list_status.grid_forget()
    self.items_list = items
    
    # Atualiza o combobox de áudio automaticamente se o site já fornecer o idioma (ex: AnimeFire)
    first_item_lang = items[0].get('lang')
    if first_item_lang and first_item_lang in ['Dublado', 'Legendado', 'Ambos (Dub + Leg)']:
      self.combo_lang.set(first_item_lang)

    if result.get('type') == 'series':
      seasons = result.get('seasons', [1])
      combo_vals = ['Todas as Temporadas'] + [
          f'Temporada {s:02d}' for s in seasons
      ]
      self.combo_seasons.configure(values=combo_vals)
      self.combo_seasons.set('Todas as Temporadas')
    else:
      self.combo_seasons.configure(values=['Filme Único'])
      self.combo_seasons.set('Filme Único')

    for i, item in enumerate(items):
      var = ctk.BooleanVar(value=True)
      chk = ctk.CTkCheckBox(
          self.scroll_list,
          text=item.get('display_text', f'Item {i}'),
          font=ctk.CTkFont('Segoe UI', size=11),
          variable=var,
          onvalue=True,
          offvalue=False,
          fg_color=self.c_orange_main,
          hover_color=self.c_orange_hover,
          border_color='#555555',
          checkbox_width=17,
          checkbox_height=17,
      )
      chk.grid(row=i, column=0, padx=10, pady=4, sticky='w')
      chk.item_data = item
      chk.check_var = var
      chk.check_var.trace_add(
          'write', lambda *args: self._update_btn_start_text()
      )
      self.checkbox_widgets[i] = chk

    self.all_selected = True
    if hasattr(self, 'btn_toggle_sel'):
      self.btn_toggle_sel.configure(
          text='✕ Desmarcar',
          fg_color='#2E2E34',
          hover_color='#3E3E46',
      )
    self._update_btn_start_text()

  def _update_btn_start_text(self):
    sel_count = sum(
        1 for chk in self.checkbox_widgets.values() if chk.check_var.get()
    )
    total_count = len(self.checkbox_widgets)
    if total_count > 0 and hasattr(self, 'btn_toggle_sel'):
      if sel_count == total_count:
        self.all_selected = True
        self.btn_toggle_sel.configure(
            text='✕ Desmarcar', fg_color='#2E2E34', hover_color='#3E3E46'
        )
      else:
        self.all_selected = False
        self.btn_toggle_sel.configure(
            text='✓ Todos', fg_color=self.c_orange_main, hover_color=self.c_orange_hover
        )

    if self.is_downloading:
      self.btn_start_dl.configure(
          text=(
              f'➕ ADICIONAR EM SEQUÊNCIA ({sel_count})'
          ),
          fg_color='#10B981',
      )
    else:
      self.btn_start_dl.configure(
          text=f'🚀 INICIAR DOWNLOAD ({sel_count})',
          fg_color=self.c_orange_main,
      )

  def toggle_select_all(self):
    if not getattr(self, 'all_selected', False):
      self.select_all_items()
    else:
      self.deselect_all_items()

  def select_all_items(self):
    self.all_selected = True
    for chk in self.checkbox_widgets.values():
      chk.check_var.set(True)
    if hasattr(self, 'btn_toggle_sel'):
      self.btn_toggle_sel.configure(
          text='✕ Desmarcar',
          fg_color='#2E2E34',
          hover_color='#3E3E46',
      )

  def deselect_all_items(self):
    self.all_selected = False
    for chk in self.checkbox_widgets.values():
      chk.check_var.set(False)
    if hasattr(self, 'btn_toggle_sel'):
      self.btn_toggle_sel.configure(
          text='✓ Todos',
          fg_color=self.c_orange_main,
          hover_color=self.c_orange_hover,
      )

  def filter_by_season(self, season_choice: str):
    if 'Todas' in season_choice or 'Filme' in season_choice:
      self.select_all_items()
      return
    try:
      target_season = int(re.sub(r'\D', '', season_choice))
      for chk in self.checkbox_widgets.values():
        item = chk.item_data
        if item.get('season') == target_season:
          chk.check_var.set(True)
        else:
          chk.check_var.set(False)
    except Exception as e:
      print('Erro no filtro:', e)

  def select_by_range(self):
    try:
      ep_from = int(self.entry_ep_from.get().strip() or '1')
      ep_to = int(self.entry_ep_to.get().strip() or '999')
      for chk in self.checkbox_widgets.values():
        item = chk.item_data
        ep = item.get('episode', 0)
        if ep_from <= ep <= ep_to:
          chk.check_var.set(True)
        else:
          chk.check_var.set(False)
    except ValueError:
      self.show_notification(
          'Formato Inválido',
          'Digite números de episódios inteiros para filtrar (Ex: de 1 a 10).',
          type='warning'
      )

  # -------------------------------------------------------------------------
  # MOTOR SEQUENCIAL CONTÍNUO
  # -------------------------------------------------------------------------
  def start_or_add_download(self):
    selected = [
        chk.item_data
        for chk in self.checkbox_widgets.values()
        if chk.check_var.get()
    ]
    if len(selected) == 0:
      self.show_notification(
          'Nenhum item selecionado',
          'Selecione ao menos 1 episódio ou filme na lista antes de acionar!',
          type='warning'
      )
      return

    if not self.downloader:
      self.downloader = DownloaderEngine(
          auth_manager=self.auth,
          status_cb=lambda msg: self.after(0, self._update_status_label, msg),
          progress_cb=lambda title, pct, sp, dl, tot: self.after(
              0, self._update_progress_bar_multi, title, pct, sp, dl, tot
          ),
          complete_cb=lambda filepath, ok, err: self.after(
              0, self._on_item_finished, filepath, ok, err
          ),
      )

    for item in selected:
      self.work_queue.put(item)
    self.total_batch_items += len(selected)

    if self.is_downloading:
      msg_added = (
          f'➕ {len(selected)} novos vídeos anexados à sequência!'
      )
      self._update_status_label(msg_added)
      self.show_notification(
          'Fila Expandida!',
          f'Mais {len(selected)} itens foram anexados à fila!\nO programa continuará baixando tudo de forma sequencial, 1 a 1 sem travar o servidor!',
          type='success',
          duration_ms=5000
      )
      self._update_btn_start_text()
      return

    self.is_downloading = True
    self.completed_batch_items = 0
    self.active_downloads.clear()

    self.btn_cancel_dl.configure(state='normal')
    self.progress_bar.set(0.0)
    self._update_btn_start_text()
    self._update_status_label(
        '🚀 Ligando turbinas! Disparando motor de download sequencial contínuo...'
    )

    max_workers = int(self.config_mgr.get('max_concurrent_downloads', 1))
    for i in range(max_workers):
      threading.Thread(
          target=self._worker_thread_func, args=(i + 1,), daemon=True
      ).start()

    threading.Thread(target=self._monitor_batch_completion, daemon=True).start()

  def _worker_thread_func(self, worker_id: int):
    while self.is_downloading:
      try:
        item = self.work_queue.get(block=False)
      except queue.Empty:
        break

      folder_base = self.config_mgr.get('default_folder', 'Muyo Download')
      lang_pref = self.combo_lang.get()
      title_key = item.get('display_text', 'Vídeo')

      self.active_downloads[title_key] = {
          'percent': 0.0,
          'speed': 0.0,
          'dl_mb': 0.0,
          'tot_mb': 0.0,
      }

      try:
        if (
            'ambos' in lang_pref.lower()
            or 'both' in lang_pref.lower()
            or '+' in lang_pref
        ):
          self._report_status(
              f'🗣️ [Operário #{worker_id}] Baixando DUBLADO: {title_key}'
          )
          self.downloader.download_item(
              item, base_folder=folder_base, preferred_lang='Dublado'
          )
          if not self.is_downloading:
            self.work_queue.task_done()
            break
          self._report_status(
              f'🗣️ [Operário #{worker_id}] Baixando LEGENDADO: {title_key}'
          )
          self.downloader.download_item(
              item, base_folder=folder_base, preferred_lang='Legendado'
          )
        else:
          self.downloader.download_item(
              item, base_folder=folder_base, preferred_lang=lang_pref
          )
      finally:
        if title_key in self.active_downloads:
          del self.active_downloads[title_key]
        self.work_queue.task_done()
        if self.is_downloading and not self.work_queue.empty():
          self._report_status("⏸️ Intervalo de segurança (3s) antes do próximo vídeo para evitar bloqueios na CDN...")
          time.sleep(3)

  def _monitor_batch_completion(self):
    self.work_queue.join()
    if self.is_downloading:
      self.after(0, self._finish_all_batch)

  def _report_status(self, msg):
    self.after(0, self._update_status_label, msg)

  def _update_status_label(self, msg):
    self.lbl_progress_info.configure(text=msg, text_color='#FDBA74')

  def _update_progress_bar_multi(self, title, percent, speed, dl_mb, tot_mb):
    self.active_downloads[title] = {
        'percent': percent,
        'speed': speed,
        'dl_mb': dl_mb,
        'tot_mb': tot_mb,
    }

    total_speed = sum(
        d.get('speed', 0) for d in self.active_downloads.values()
    )
    total_active_dl = sum(
        d.get('dl_mb', 0) for d in self.active_downloads.values()
    )
    total_active_tot = sum(
        d.get('tot_mb', 0) for d in self.active_downloads.values()
    )

    active_names = []
    for t, data in list(self.active_downloads.items())[:3]:
      s_name = t if len(t) < 16 else t[:14] + '..'
      active_names.append(f"{s_name}: {data['percent']:.0f}%")

    str_active = ' | '.join(active_names) if active_names else "Processando fila..."
    msg = (
        f'⏬ [SEQUÊNCIA] {str_active} -> {total_active_dl:.0f}/'
        f'{total_active_tot:.0f}MB à {total_speed:.1f} MB/s'
    )

    fraction = (
        (
            self.completed_batch_items
            + sum(
                d.get('percent', 0) / 100.0
                for d in self.active_downloads.values()
            )
        )
        / self.total_batch_items
        if self.total_batch_items > 0
        else 0
    )
    self.progress_bar.set(min(1.0, fraction))
    self.lbl_progress_info.configure(text=msg, text_color=self.c_green)

  def _on_item_finished(self, filepath, success, error_msg):
    self.completed_batch_items += 1
    pct_total = (
        (self.completed_batch_items / self.total_batch_items) * 100
        if self.total_batch_items > 0
        else 0
    )
    if success:
      msg_done = (
          f'✔️ Salvo [{self.completed_batch_items}/{self.total_batch_items}]'
          f' ({pct_total:.0f}%) -> {os.path.basename(filepath)[:30]}'
      )
      self._update_status_label(msg_done)
    else:
      msg_err = f'⚠️ Falha [{os.path.basename(filepath)[:20]}]: {error_msg}'
      self._update_status_label(msg_err)

  def _finish_all_batch(self):
    self.is_downloading = False
    self.active_downloads.clear()
    self._update_btn_start_text()
    self.btn_cancel_dl.configure(state='disabled')
    self.progress_bar.set(1.0)
    self._update_status_label('🏆 TODOS OS DOWNLOADS CONCLUÍDOS COM SUCESSO!')
    self.show_notification(
        'Lote Concluído!',
        f"Todos os vídeos foram processados e salvos em:\n{self.config_mgr.get('default_folder')}",
        type='success',
        duration_ms=7000
    )

  def cancel_download_process(self):
    if self.is_downloading and self.downloader:
      self.is_downloading = False
      while not self.work_queue.empty():
        try:
          self.work_queue.get(block=False)
          self.work_queue.task_done()
        except queue.Empty:
          break
      self.active_downloads.clear()
      self.downloader.cancel_download()
      self._update_status_label('🛑 Downloads cancelados pelo usuário.')
      self.btn_cancel_dl.configure(state='disabled')
      self._update_btn_start_text()

  def show_notification(self, title, message, type='info', duration_ms=4500):
    """Exibe um Toast Notification in-app estilo cartão."""
    color_map = {
        'info': self.c_orange_main,
        'success': '#10B981',
        'warning': '#F59E0B',
        'error': '#EF4444'
    }
    accent_color = color_map.get(type, self.c_orange_main)
    
    notif_frame = ctk.CTkFrame(
        self, 
        fg_color=self.c_bg_panel,
        border_width=2,
        border_color=accent_color,
        corner_radius=8,
        width=400
    )
    notif_frame.place(relx=0.5, rely=0.92, anchor='s')
    
    lbl_title = ctk.CTkLabel(
        notif_frame, 
        text=title, 
        font=ctk.CTkFont('Segoe UI', size=14, weight='bold'),
        text_color=accent_color
    )
    lbl_title.pack(pady=(12, 4), padx=16, anchor='w')
    
    lbl_msg = ctk.CTkLabel(
        notif_frame,
        text=message,
        font=ctk.CTkFont('Segoe UI', size=12),
        text_color='#E5E5E5',
        justify='left',
        wraplength=360
    )
    lbl_msg.pack(pady=(0, 12), padx=16, anchor='w')

    self.after(duration_ms, notif_frame.destroy)
