import os
import json
from fastapi import APIRouter, HTTPException
from processing.youtube_processor import youtube_url_to_text

router = APIRouter()

# Diretórios principais
YOUTUBE_DIR = "uploads/youtube"
WAV_DIR = os.path.join(YOUTUBE_DIR, ".wav")
TXT_DIR = os.path.join(YOUTUBE_DIR, ".txt")
JSON_FILE = os.path.join(YOUTUBE_DIR, "youtube_processes.json")

# Garantir que os diretórios existam
os.makedirs(WAV_DIR, exist_ok=True)
os.makedirs(TXT_DIR, exist_ok=True)

# Criar o arquivo JSON se ele não existir
if not os.path.exists(JSON_FILE):
    with open(JSON_FILE, "w") as f:
        json.dump({"videos": []}, f, ensure_ascii=False, indent=4)


@router.post("/youtube/")
async def process_youtube_video(url: str, title: str, language: str = "en"):
    """
    Processa um vídeo do YouTube, transcreve o áudio e atualiza o arquivo JSON centralizado.
    """
    try:
        # Processa o vídeo e gera os arquivos
        transcription = youtube_url_to_text(url, title, language)

        # Caminhos dos arquivos gerados
        audio_file = f"./{title}.wav"
        transcription_file = f"./{title}.txt"

        # Mover arquivos para suas respectivas subpastas
        new_audio_path = os.path.join(WAV_DIR, f"{title}.wav")
        new_transcription_path = os.path.join(TXT_DIR, f"{title}.txt")
        os.rename(audio_file, new_audio_path)
        os.rename(transcription_file, new_transcription_path)

        # Atualizar o arquivo JSON centralizado
        with open(JSON_FILE, "r") as f:
            data = json.load(f)

        video_entry = {
            "title": title,
            "language": language,
            "url": url,
            "audio_path": new_audio_path,
            "text_path": new_transcription_path,
        }

        data["videos"].append(video_entry)

        with open(JSON_FILE, "w") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

        return {
            "message": "Transcrição concluída e arquivos organizados com sucesso!",
            "metadata": video_entry,
        }

    except FileNotFoundError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao processar vídeo: {str(e)}")

@router.get("/youtube/docs")
async def get_all_youtube_videos():
    """
    Retorna todos os vídeos processados.
    """
    try:
        # Ler o arquivo JSON centralizado
        with open(JSON_FILE, "r") as f:
            data = json.load(f)
        return {"videos": data["videos"]}
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Nenhum vídeo processado encontrado.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao ler os vídeos processados: {str(e)}")

@router.get("/youtube/{title}")
async def get_youtube_video_by_title(title: str):
    """
    Retorna os metadados de um vídeo específico pelo título.
    """
    try:
        # Ler o arquivo JSON centralizado
        with open(JSON_FILE, "r") as f:
            data = json.load(f)

        # Procurar o vídeo pelo título
        video = next((v for v in data["videos"] if v["title"].lower() == title.lower()), None)
        if not video:
            raise HTTPException(status_code=404, detail=f"Vídeo com título '{title}' não encontrado.")

        return video
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Nenhum vídeo processado encontrado.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar o vídeo: {str(e)}")

@router.get("/youtube/{title}/content")
async def get_youtube_text_content(title: str, full_content: bool = False):
    """
    Retorna o conteúdo de texto de um vídeo específico pelo título.
    """
    try:
        # Ler o arquivo JSON centralizado
        with open(JSON_FILE, "r") as f:
            data = json.load(f)

        # Procurar o vídeo pelo título
        video = next((v for v in data["videos"] if v["title"].lower() == title.lower()), None)
        if not video:
            raise HTTPException(status_code=404, detail=f"Vídeo com título '{title}' não encontrado.")

        # Verificar se o arquivo de texto existe
        text_path = video["text_path"]
        if not os.path.exists(text_path):
            raise HTTPException(status_code=404, detail=f"O arquivo de texto para o vídeo '{title}' não foi encontrado.")

        # Ler o conteúdo do arquivo de texto
        with open(text_path, "r") as f:
            content = f.read()

        # Retornar o conteúdo completo ou limitado
        if not full_content:
            content = content[:500] + "..." if len(content) > 500 else content

        return {"title": title, "content": content}
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Nenhum vídeo processado encontrado.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar o conteúdo do vídeo: {str(e)}")
