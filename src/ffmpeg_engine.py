import os
import shutil
import urllib.request
import zipfile
import subprocess
import json
from io import BytesIO

def _get_app_dir():
    return os.path.join(os.getenv('LOCALAPPDATA', os.path.expanduser('~')), 'MuyoDownload')

def get_ffmpeg_path():
    system_ffmpeg = shutil.which("ffmpeg")
    if system_ffmpeg:
        return system_ffmpeg
    return os.path.join(_get_app_dir(), 'ffmpeg', 'ffmpeg.exe')

def get_ffprobe_path():
    system_ffprobe = shutil.which("ffprobe")
    if system_ffprobe:
        return system_ffprobe
    return os.path.join(_get_app_dir(), 'ffmpeg', 'ffprobe.exe')

def ensure_ffmpeg_installed(status_cb=None):
    if not status_cb:
        status_cb = lambda msg: print(msg)

    ffmpeg_exe = get_ffmpeg_path()
    if os.path.exists(ffmpeg_exe):
        return True

    status_cb("Baixando FFmpeg (Motor de Conversão), por favor aguarde...")
    url = "https://github.com/yt-dlp/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as resp:
            zip_data = resp.read()

        status_cb("Extraindo FFmpeg...")
        with zipfile.ZipFile(BytesIO(zip_data)) as zf:
            dest_dir = os.path.join(_get_app_dir(), 'ffmpeg')
            os.makedirs(dest_dir, exist_ok=True)
            for file_info in zf.infolist():
                if file_info.filename.endswith('ffmpeg.exe') or file_info.filename.endswith('ffprobe.exe'):
                    file_info.filename = os.path.basename(file_info.filename)
                    zf.extract(file_info, dest_dir)
        return True
    except Exception as e:
        status_cb(f"Erro ao baixar FFmpeg: {e}")
        return False

def convert_to_mp4(input_path: str, output_path: str, status_cb=None) -> bool:
    if not ensure_ffmpeg_installed(status_cb):
        return False
    if not status_cb:
        status_cb = lambda msg: print(msg)

    status_cb(f"Iniciando conversão para MP4: {os.path.basename(input_path)}")
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    
    cmd = [
        get_ffmpeg_path(), '-y', '-i', input_path,
        '-c:v', 'copy', '-c:a', 'aac',
        output_path
    ]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, creationflags=flags)
        if res.returncode == 0:
            status_cb("Conversão para MP4 concluída com sucesso!")
            return True
        else:
            status_cb(f"Erro na conversão: {res.stderr}")
            return False
    except Exception as e:
        status_cb(f"Falha ao executar FFmpeg: {e}")
        return False

def extract_audio(input_path: str, output_path: str, format="mp3", status_cb=None) -> bool:
    if not ensure_ffmpeg_installed(status_cb):
        return False
    if not status_cb:
        status_cb = lambda msg: print(msg)
        
    status_cb(f"Extraindo áudio ({format.upper()}): {os.path.basename(input_path)}")
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    
    codec = "libmp3lame" if format.lower() == "mp3" else "pcm_s16le"
    cmd = [
        get_ffmpeg_path(), '-y', '-i', input_path,
        '-vn', '-acodec', codec,
        output_path
    ]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, creationflags=flags)
        if res.returncode == 0:
            status_cb(f"Áudio extraído com sucesso para {format.upper()}!")
            return True
        else:
            status_cb(f"Erro na extração de áudio: {res.stderr}")
            return False
    except Exception as e:
        status_cb(f"Falha ao executar FFmpeg: {e}")
        return False

def split_dual_audio_video(input_path: str, output_folder: str, status_cb=None) -> bool:
    if not ensure_ffmpeg_installed(status_cb):
        return False
    if not status_cb:
        status_cb = lambda msg: print(msg)

    status_cb(f"Analisando faixas de áudio em: {os.path.basename(input_path)}")
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    
    probe_cmd = [
        get_ffprobe_path(), '-v', 'quiet', '-print_format', 'json', '-show_streams', input_path
    ]
    try:
        res = subprocess.run(probe_cmd, capture_output=True, text=True, creationflags=flags)
        if res.returncode != 0:
            status_cb("Erro ao ler as faixas de áudio (FFprobe falhou).")
            return False
            
        data = json.loads(res.stdout)
        audio_streams = [s for s in data.get('streams', []) if s.get('codec_type') == 'audio']
        
        if len(audio_streams) < 2:
            status_cb(f"Foram encontrados apenas {len(audio_streams)} áudios. É necessário mais de um áudio para separar.")
            return False
            
        base_name = os.path.splitext(os.path.basename(input_path))[0]
        os.makedirs(output_folder, exist_ok=True)
        
        status_cb(f"Encontrados {len(audio_streams)} idiomas. Separando vídeos, aguarde...")
        
        all_success = True
        
        for idx, stream in enumerate(audio_streams):
            lang = stream.get('tags', {}).get('language', f'Trilha{idx+1}')
            stream_index = stream.get('index')
            out_file = os.path.join(output_folder, f"{base_name} ({lang.upper()}).mp4")
            
            cmd = [
                get_ffmpeg_path(), '-y', '-i', input_path,
                '-map', '0:v:0', '-map', f'0:{stream_index}',
                '-c:v', 'copy', '-c:a', 'aac',
                out_file
            ]
            
            res_ff = subprocess.run(cmd, capture_output=True, text=True, creationflags=flags)
            if res_ff.returncode != 0:
                all_success = False
                status_cb(f"Erro ao gerar versão {lang.upper()}: {res_ff.stderr[:100]}...")
            
        if all_success:
            status_cb("Separação de idiomas concluída com sucesso! (Vídeos criados)")
            return True
        else:
            return False

    except Exception as e:
        status_cb(f"Falha ao executar a separação: {e}")
        return False
