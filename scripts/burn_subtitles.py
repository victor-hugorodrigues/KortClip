import os
import subprocess
import sys
from scripts.edit_video import get_best_encoder

# sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def burn_video_file(video_path, subtitle_path, output_path):
    """
    Burns subtitles into a single video file.
    """
    # Ajuste no caminho da legenda para FFmpeg (Forward Slash e escape de :)
    # No Windows, "C:/foo" funciona se estiver entre aspas simples dentro do filtro.
    # Para garantir, usamos replace e forward slashes.
    subtitle_file_ffmpeg = subtitle_path.replace('\\', '/').replace(':', '\\:')

    # Setup explicit typography directory
    fonts_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "fonts")
    os.makedirs(fonts_dir, exist_ok=True)
    fonts_dir_escaped = fonts_dir.replace('\\', '/').replace(':', '\\:')
    
    def run_ffmpeg(encoder, preset, additional_args=[]):
        cmd = [
            "ffmpeg", "-y", "-loglevel", "error", "-hide_banner",
            '-i', video_path,
            '-vf', f"subtitles='{subtitle_file_ffmpeg}':fontsdir='{fonts_dir_escaped}'",
            '-c:v', encoder,
            '-preset', preset,
            '-b:v', '5M',
            '-pix_fmt', 'yuv420p',
            '-c:a', 'copy',
            output_path
        ] + additional_args
        subprocess.run(cmd, check=True, capture_output=True)

    encoder, preset = get_best_encoder()

    try:
        # print(f"Processing video ({encoder}): {os.path.basename(video_path)}")
        run_ffmpeg(encoder, preset)
        # print(f"Processed: {output_path}")
        return True, f"{encoder} Success"
    except subprocess.CalledProcessError as e:
         err_msg = f"FATAL ERROR burning subtitles in {os.path.basename(video_path)} with {encoder}: {e}"
         if e.stderr:
             err_msg += f" | FFmpeg Log: {e.stderr.decode('utf-8', errors='ignore')}"
         print(err_msg)
         return False, err_msg
    except Exception as e:
        return False, str(e)

def burn(project_folder="tmp"):
    # Converter para absoluto para não ter erro no filtro do ffmpeg
    if project_folder and not os.path.isabs(project_folder):
        project_folder_abs = os.path.abspath(project_folder)
    else:
        project_folder_abs = project_folder

    # Caminhos das pastas
    subs_folder = os.path.join(project_folder_abs, 'subs_ass')
    videos_folder = os.path.join(project_folder_abs, 'final')
    output_folder = os.path.join(project_folder_abs, 'burned_sub')  # Pasta para salvar os vídeos com legendas

    # Cria a pasta de saída se não existir
    os.makedirs(output_folder, exist_ok=True)
    
    if not os.path.exists(videos_folder):
        print(f"Pasta de vídeos finais não encontrada: {videos_folder}")
        return

    # Itera sobre os arquivos de vídeo na pasta final
    files = os.listdir(videos_folder)
    if not files:
        print("Nenhum arquivo encontrado em 'final' para queimar legendas.")
        return

    for video_file in files:
        if video_file.endswith(('.mp4', '.mkv', '.avi')):  # Formatos suportados
            # Se for temp file (ex: temp_video_no_audio), ignora se existir a versão final
            if "temp_video_no_audio" in video_file:
                continue

            # Extrai o nome base do vídeo (sem extensão)
            video_name = os.path.splitext(video_file)[0]
            
            # Define o caminho para a legenda correspondente
            subtitle_file = os.path.join(subs_folder, f"{video_name}.ass")
            
            # Tentar também com sufixo _processed caso a convenção seja diferente
            if not os.path.exists(subtitle_file):
                subtitle_file_processed = os.path.join(subs_folder, f"{video_name}_processed.ass")
                if os.path.exists(subtitle_file_processed):
                    subtitle_file = subtitle_file_processed
            
            # Verifica se a legenda existe
            if os.path.exists(subtitle_file):
                # Define o caminho de saída para o vídeo com legendas
                output_file = os.path.join(output_folder, f"{video_name}_subtitled.mp4")

                print(f"Burning: {video_name}...")
                success, msg = burn_video_file(os.path.join(videos_folder, video_file), subtitle_file, output_file)
                if success:
                    print(f"Done: {output_file}")
                else:
                    print(f"Fail: {msg}")
            else:
                print(f"Legenda não encontrada para: {video_name} em {subtitle_file}")
