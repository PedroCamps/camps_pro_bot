import yt_dlp
import whisper
import os
import torch

def youtube_url_to_text(url: str, title: str, video_language: str) -> str:
    # Definir opções para o download de áudio diretamente no formato WAV
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'wav',
            'preferredquality': '192',
        }],
        'outtmpl': f'./{title}',
    }
    
    # Baixar o áudio do YouTube
    print(f"Baixando áudio de {url}...")
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    audio_file = f'./{title}.wav'
    if not os.path.exists(audio_file):
        raise FileNotFoundError(f"Erro: O arquivo de áudio {audio_file} não foi gerado.")
    
    # Configurar dispositivo para transcrição
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Usando o dispositivo: {device}")
    
    # Carregar modelo Whisper e transcrever áudio
    model = whisper.load_model("base", device=device)
    print("Transcrevendo áudio...")
    result = model.transcribe(audio_file, language=video_language)
    transcription = result['text']
    
    # Salvar transcrição em um arquivo .txt
    output_txt = f'./{title}.txt'
    with open(output_txt, 'w') as f:
        f.write(transcription)
    
    print(f"Transcrição salva em: {output_txt}")
    return transcription


