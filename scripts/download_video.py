import os
import re
import yt_dlp
import sys
import subprocess
from i18n.i18n import I18nAuto
i18n = I18nAuto()

def sanitize_filename(name):
    """Remove caracteres inválidos e emojis para evitar erro de encoding no Windows."""
    # Remove caracteres reservados do sistema de arquivos
    cleaned = re.sub(r'[\\/*?:"<>|]', "", name)
    
    # Remove emojis e caracteres não suportados pelo console Windows (CP1252)
    # Isso mantém acentos (á, ç, é) mas remove 😱, etc.
    try:
        cleaned = cleaned.encode('cp1252', 'ignore').decode('cp1252')
    except:
        # Fallback se não tiver CP1252: remove tudo não-ascii (remove acentos)
        cleaned = cleaned.encode('ascii', 'ignore').decode('ascii')
        
    cleaned = cleaned.strip()
    return cleaned

def time_to_seconds(t_str):
    if not t_str: return 0
    t_str = str(t_str).strip()
    
    # Handle direct HH:MM:SS formats or MM:SS
    if ':' in t_str:
        parts = t_str.split(':')
        try:
            if len(parts) == 3: # HH:MM:SS
                return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2].replace(',', '.'))
            elif len(parts) == 2: # MM:SS
                return int(parts[0]) * 60 + float(parts[1].replace(',', '.'))
        except ValueError:
            return 0
            
    # Handle pure seconds or invalid strings
    try:
        return float(t_str.replace(',', '.'))
    except ValueError:
        return 0

def format_srt_time(seconds):
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    return f"{h:02d}:{m:02d}:{s:06.3f}".replace('.', ',')

def trim_video_and_subs(video_path, project_folder, start_time, end_time):
    start_sec = time_to_seconds(start_time)
    end_sec = time_to_seconds(end_time) if end_time else None
    
    if start_sec <= 0 and not end_sec:
        return # nothing to do
        
    print(i18n("Trimming video to specified interval..."))
    
    # 1. Trim video
    temp_video = os.path.join(project_folder, "input_full_temp.mp4")
    try:
        os.rename(video_path, temp_video)
    except Exception as e:
        print(i18n("Failed to rename video for trimming: {}").format(e))
        return
    
    cmd = ["ffmpeg", "-y", "-i", temp_video]
    if start_sec > 0:
        cmd.extend(["-ss", str(start_sec)])
    if end_sec:
        cmd.extend(["-to", str(end_sec)])
    
    cmd.extend(["-c:v", "copy", "-c:a", "aac", video_path])
    
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        os.remove(temp_video)
    except Exception as e:
        print(i18n("Failed to trim video: {}").format(e))
        if os.path.exists(temp_video):
            os.replace(temp_video, video_path)
            
    # 2. Trim SRT
    srt_path = os.path.join(project_folder, "input.srt")
    if os.path.exists(srt_path):
        print(i18n("Trimming original subtitles..."))
        try:
            with open(srt_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                
            new_lines = []
            i = 0
            counter = 1
            while i < len(lines):
                line = lines[i].strip()
                if line.isdigit():
                    i += 1
                    if i < len(lines) and "-->" in lines[i]:
                        time_line = lines[i]
                        start_str, end_str = time_line.split("-->")
                        start_str = start_str.strip()
                        end_str = end_str.strip()
                        
                        sub_start_sec = time_to_seconds(start_str.replace(',', '.'))
                        sub_end_sec = time_to_seconds(end_str.replace(',', '.'))
                        
                        if sub_end_sec > start_sec and (not end_sec or sub_start_sec < end_sec):
                            new_start = max(0, sub_start_sec - start_sec)
                            new_end = sub_end_sec - start_sec
                            if end_sec:
                                new_end = min(new_end, end_sec - start_sec)
                            
                            new_time_line = f"{format_srt_time(new_start)} --> {format_srt_time(new_end)}\n"
                            
                            text_lines = []
                            i += 1
                            while i < len(lines) and lines[i].strip():
                                text_lines.append(lines[i])
                                i += 1
                                
                            new_lines.append(f"{counter}\n")
                            new_lines.append(new_time_line)
                            new_lines.extend(text_lines)
                            new_lines.append("\n")
                            counter += 1
                        else:
                            i += 1
                            while i < len(lines) and lines[i].strip():
                                i += 1
                    else:
                        i += 1
                elif not line:
                    i += 1
                else:
                    i += 1
                    
            with open(srt_path, 'w', encoding='utf-8') as f:
                f.writelines(new_lines)
        except Exception as e:
            print(i18n("Failed to trim subtitles: {}").format(e))

def progress_hook(d):
    if d['status'] == 'downloading':
        try:
            p = d.get('_percent_str', '').replace('%','')
            print(f"[download] {p}% - {d.get('_eta_str', 'N/A')} remaining", flush=True)
        except:
            pass
    elif d['status'] == 'finished':
        print(f"[download] Download concluído: {d['filename']}", flush=True)

def download(url, base_root="VIRALS", download_subs=True, quality="best", start_time=None, end_time=None):
    # 1. Extrair informações do vídeo para pegar o título
    # 1. Extrair informações do vídeo para pegar o título
    print(i18n("Extracting video information..."))
    title = None
    
    # ... (Keep existing title extraction logic) ...
    # Instead of repeating it effectively, I will rely on the diff to keep it or re-write it if I have to replace the whole block.
    # Since replace_file_content works on line ranges, I should be careful.
    # Let's assume I'm replacing the whole function body or significant parts.
    
    # Tentativa 1: Com cookies
    try:
        with yt_dlp.YoutubeDL({'quiet': True, 'no_warnings': True, 'cookiesfrombrowser': ('chrome',)}) as ydl:
            info = ydl.extract_info(url, download=False)
            title = info.get('title')
    except Exception as e:
        try:
            print(i18n("Warning: Failed to extract info with cookies: {}").format(e))
        except UnicodeEncodeError:
            print(i18n("Warning: Failed to extract info with cookies: [Encoding Error in Message]"))

    # Tentativa 2: Sem cookies
    if not title:
        try:
             with yt_dlp.YoutubeDL({'quiet': True, 'no_warnings': True}) as ydl:
                info = ydl.extract_info(url, download=False)
                title = info.get('title')
        except Exception as e:
            try:
                print(i18n("Error getting video info (without cookies): {}").format(e))
            except UnicodeEncodeError:
                print(i18n("Error getting video info (without cookies): [Encoding Error in Message]"))

    # Fallback final
    if title:
        safe_title = sanitize_filename(title)
        try:
            print(i18n("Detected title: {}").format(title))
        except UnicodeEncodeError:
            # Fallback for Windows consoles that choke on Emojis
            clean_title = title.encode('ascii', 'replace').decode('ascii')
            print(i18n("Detected title: {}").format(clean_title))
    else:
        print(i18n("WARNING: Title could not be obtained. Using 'Unknown_Video'."))
        safe_title = i18n("Unknown_Video")

    # 2. Criar estrutura de pastas
    project_folder = os.path.join(base_root, safe_title)
    os.makedirs(project_folder, exist_ok=True)
    
    # Caminho final do vídeo
    output_filename = 'input' 
    output_path_base = os.path.join(project_folder, output_filename)
    final_video_path = f"{output_path_base}.mp4"

    # Verificação inteligente
    if os.path.exists(final_video_path):
        if os.path.getsize(final_video_path) > 1024: 
            try:
                print(i18n("Video already exists at: {}").format(final_video_path))
            except UnicodeEncodeError:
                print(i18n("Video already exists at: {}").format(final_video_path.encode('ascii', 'replace').decode('ascii')))
            print(i18n("Skipping download and reusing local file."))
            return final_video_path, project_folder
        else:
            print(i18n("Existing file found but seems corrupted/empty. Downloading again..."))
            try:
                os.remove(final_video_path)
            except:
                pass

    # Limpeza de temp
    temp_path = f"{output_path_base}.temp.mp4"
    if os.path.exists(temp_path):
        try:
            os.remove(temp_path)
        except:
            pass

    # Mapeamento de Qualidade
    quality_map = {
        "best": 'bestvideo+bestaudio/best',
        "1080p": 'bestvideo[height<=1080]+bestaudio/best[height<=1080]',
        "720p": 'bestvideo[height<=720]+bestaudio/best[height<=720]',
        "480p": 'bestvideo[height<=480]+bestaudio/best[height<=480]'
    }
    selected_format = quality_map.get(quality, 'bestvideo+bestaudio/best')
    print(i18n("Configuring download quality: {} -> {}").format(quality, selected_format))

    ydl_opts = {
        'format': selected_format,
        'overwrites': True,
        'outtmpl': output_path_base, 
        'postprocessor_args': [
            '-movflags', 'faststart'
        ],
        'merge_output_format': 'mp4',
        'progress_hooks': [progress_hook],
        # Opções de Legenda
        'writesubtitles': download_subs,
        'writeautomaticsub': download_subs,
        'subtitleslangs': ['pt.*', 'en.*', 'sp.*'], # Prioritize generic PT, EN, SP
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        },
        'skip_download': False,
        'quiet': False,
        'no_warnings': False,
        'force_ipv4': True,
    }
    

    
    if download_subs:
        ydl_opts['postprocessors'] = [{
            'key': 'FFmpegSubtitlesConvertor',
            'format': 'srt',
        }]

    try:
        print(i18n("Downloading video to: {}...").format(project_folder))
    except UnicodeEncodeError:
        print(i18n("Downloading video to: {}...").format(project_folder.encode('ascii', 'replace').decode('ascii')))
    
    # Tentativa 1: Com configuração original
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
    except yt_dlp.utils.DownloadError as e:
        error_str = str(e)
        if "No address associated with hostname" in error_str or "Failed to resolve" in error_str:
            print(i18n("\n[CRITICAL ERROR] Connection Failure: Could not access YouTube."))
            print(i18n("Check your internet connection or if there is any DNS block."))
            print(i18n("Details: {}").format(e))
            sys.exit(1)
        
        elif download_subs and ("Unable to download video subtitles" in error_str or "429" in error_str):
            print(i18n("\nWarning: Error downloading subtitles ({}).").format(e))
            print(i18n("Retrying ONLY the video (without subtitles)..."))
            
            ydl_opts['writesubtitles'] = False
            ydl_opts['writeautomaticsub'] = False
            ydl_opts['postprocessors'] = [p for p in ydl_opts.get('postprocessors', []) if 'Subtitle' not in p.get('key', '')]
            
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])
            except Exception as e2:
                print(i18n("Fatal error on second attempt: {}").format(e2))
                raise
        elif "is not a valid URL" in error_str:
             print(i18n("Error: the entered link is not valid."))
             raise 
        else:
            print(i18n("Download error: {}").format(e))
            raise
    except Exception as e:
        print(i18n("Unexpected error: {}").format(e))
        raise

    # RENOMEAR LEGENDA PARA PADRÃO (input.vtt ou input.srt)
    # Se for VTT, converte para SRT para garantir compatibilidade.
    try:
        import glob
        # Pega a primeira que encontrar
        potential_subs = glob.glob(os.path.join(project_folder, "input.*.vtt")) + glob.glob(os.path.join(project_folder, "input.*.srt"))
        
        if potential_subs:
            best_sub = potential_subs[0]
            ext = os.path.splitext(best_sub)[1]
            new_name = os.path.join(project_folder, "input.srt") # Vamos padronizar tudo para .srt
            
            if ext.lower() == '.vtt':
                try:
                    print(i18n("Formatting complex VTT subtitle ({}) to clean SRT...").format(os.path.basename(best_sub)))
                except UnicodeEncodeError:
                    print(i18n("Formatting complex VTT subtitle ({}) to clean SRT...").format(os.path.basename(best_sub).encode('ascii', 'replace').decode('ascii')))
                try:
                    with open(best_sub, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                    
                    srt_content = []
                    counter = 1
                    
                    seen_texts = set()
                    last_text = ""
                    
                    for line in lines:
                        clean_line = line.strip()
                        # Ignora Headers e Metadados do VTT/Youtube
                        if clean_line.startswith("WEBVTT") or \
                           clean_line.startswith("X-TIMESTAMP") or \
                           clean_line.startswith("NOTE") or \
                           clean_line.startswith("Kind:") or \
                           clean_line.startswith("Language:"):
                            continue
                        
                        if "-->" in clean_line:
                            # Parse Timestamp
                            parts = clean_line.split("-->")
                            start = parts[0].strip()
                            # Remove tags de posicionamento "align:start position:0%"
                            end = parts[1].strip().split(' ')[0] 
                            
                            def fix_time(t):
                                t = t.replace('.', ',')
                                if t.count(':') == 1: 
                                    t = "00:" + t
                                return t
                            
                            current_start = fix_time(start)
                            current_end = fix_time(end)
                            
                        elif clean_line:
                             # Texto: remover tags complexas <00:00:00.560><c> etc
                             # O YouTube usa formato karaoke. Ex: "Quanto<...> custa<...>"
                             # Precisamos do texto limpo.
                             text = re.sub(r'<[^>]+>', '', clean_line).strip()
                             
                             if not text: continue
                             
                             # Lógica para remover duplicatas do estilo "Roll-up" ou "Karaoke"
                             # O YouTube repete a linha anterior às vezes.
                             # Ex:
                             # 1: "Quanto custa"
                             # 2: "Quanto custa\nQuantos quilos"
                             
                             # Vamos pegar apenas a ULTIMA linha se tiver quebras
                             lines_in_text = text.split('\n')
                             final_line = lines_in_text[-1].strip()
                             
                             if not final_line: continue

                             # Filtro de duplicidade consecutivo
                             if final_line == last_text:
                                 continue
                             
                             # Evita blocos ultra curtos (glitch de 10ms) que repetem texto
                             # Mas aqui estamos processando texto.
                             
                             srt_content.append(f"{counter}\n")
                             srt_content.append(f"{current_start} --> {current_end}\n")
                             srt_content.append(f"{final_line}\n\n")
                             
                             last_text = final_line
                             counter += 1
                    
                    with open(new_name, 'w', encoding='utf-8') as f_out:
                        f_out.writelines(srt_content)
                    
                    try:
                        print(i18n("Subtitle converted and cleaned: {}").format(new_name))
                    except UnicodeEncodeError:
                        print(i18n("Subtitle converted and cleaned: {}").format(new_name.encode('ascii', 'replace').decode('ascii')))
                    try: os.remove(best_sub) 
                    except: pass
                    
                except Exception as e_conv:
                    print(i18n("Failed to convert VTT: {}. Keeping original.").format(e_conv))
                    # Fallback: rename apenas
                    new_name_fallback = os.path.join(project_folder, "input.vtt")
                    if os.path.exists(new_name_fallback) and new_name_fallback != best_sub:
                        try: os.remove(new_name_fallback)
                        except: pass
                    os.rename(best_sub, new_name_fallback)

            else:
                # Já é SRT, só renomeia
                if os.path.exists(new_name) and new_name != best_sub:
                    try: os.remove(new_name)
                    except: pass
                os.rename(best_sub, new_name)
                try:
                    print(i18n("SRT subtitle renamed to: {}").format(new_name))
                except UnicodeEncodeError:
                    print(i18n("SRT subtitle renamed to: {}").format(new_name.encode('ascii', 'replace').decode('ascii')))
            
            # Limpa sobras
            for extra in potential_subs[1:]:
                try: os.remove(extra)
                except: pass

    except Exception as e_ren:
        print(i18n("Error processing subtitles: {}").format(e_ren))

    if start_time or end_time:
        trim_video_and_subs(final_video_path, project_folder, start_time, end_time)

    return final_video_path, project_folder