from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks, APIRouter
from pydantic import BaseModel
from typing import Optional
import os
import shutil
import json
from urllib.parse import urlparse
from fastapi.responses import JSONResponse

# Importar processadores existentes
from processing.excel_processor import process_excel_with_output
from processing.pdf_processor import process_pdf
from processing.youtube_processor import youtube_url_to_text
from processing.link_processor import crawl_single_page, crawl_documentation

# Configuração da aplicação
router = APIRouter()

# Diretórios de upload e saída
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)
EXCEL_DIR = os.path.join(UPLOAD_DIR, "excel")
PDF_DIR = os.path.join(UPLOAD_DIR, "pdfs")
YOUTUBE_DIR = os.path.join(UPLOAD_DIR, "youtube")
WAV_DIR = os.path.join(YOUTUBE_DIR, ".wav")
TXT_DIR = os.path.join(YOUTUBE_DIR, ".txt")
JSON_FILE = os.path.join(YOUTUBE_DIR, "youtube_processes.json")
MD_DIR = os.path.join(UPLOAD_DIR, "MD_links")
for directory in [EXCEL_DIR, PDF_DIR, YOUTUBE_DIR, MD_DIR]:
    os.makedirs(directory, exist_ok=True)

# Rotas
@router.post("/pdf/upload")
async def upload_pdf(file: UploadFile = File(...)):
    """Upload de PDF e retorno como JSON."""
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Apenas arquivos PDF são permitidos.")
    file_path = os.path.join(PDF_DIR, file.filename)
    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    json_path = os.path.splitext(file_path)[0] + ".json"
    pdf_data = process_pdf(file_path, PDF_DIR)
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(pdf_data, f, ensure_ascii=False, indent=4)
    return {"message": "PDF processado com sucesso!", "json_data": pdf_data}

@router.post("/excel/upload")
async def upload_excel(file: UploadFile = File(...)):
    """Upload de Excel e retorno como JSON."""
    if not file.filename.endswith(('.xls', '.xlsx')):
        raise HTTPException(status_code=400, detail="Arquivo inválido. Envie um Excel válido.")
    file_path = os.path.join(EXCEL_DIR, file.filename)
    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    result = process_excel_with_output(file_path)
    return {"message": "Excel processado com sucesso!", "data": result["data"]}

@router.post("/youtube/process")
async def process_youtube(url: str, title: str, language: str = "en"):
    """Processa link do YouTube, salva e organiza os arquivos gerados."""
    try:
        # Processa o vídeo e gera os arquivos
        transcription = youtube_url_to_text(url, title, language)

        # Caminhos dos arquivos esperados
        audio_file = f"./{title}.wav"
        transcription_file = f"./{title}.txt"

        # Verificar se os arquivos foram criados
        if not os.path.exists(audio_file) or not os.path.exists(transcription_file):
            raise FileNotFoundError("Os arquivos gerados pelo processamento não foram encontrados.")

        # Mover arquivos para suas respectivas subpastas
        new_audio_path = os.path.join(WAV_DIR, f"{title}.wav")
        new_transcription_path = os.path.join(TXT_DIR, f"{title}.txt")
        os.makedirs(os.path.dirname(new_audio_path), exist_ok=True)
        os.makedirs(os.path.dirname(new_transcription_path), exist_ok=True)
        shutil.move(audio_file, new_audio_path)
        shutil.move(transcription_file, new_transcription_path)

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
            "content": transcription
        }

    except FileNotFoundError as e:
        raise HTTPException(status_code=500, detail=f"Erro ao encontrar arquivos: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao processar vídeo: {str(e)}")


@router.post("/web/crawl")
async def crawl_web(url: str, mode: str):
    MAX_DEPTH = 1
    MAX_CONCURRENT = 10
    """
    Processa uma página ou múltiplas páginas e retorna o conteúdo Markdown imediatamente.
    """
    try:
        # Validação do modo
        if mode == "single":
            # Chama o processo de página única
            success = await crawl_single_page(url, UPLOAD_DIR)
            if not success:
                raise HTTPException(status_code=500, detail="Falha ao processar a URL fornecida.")
        elif mode == "multi":
            # Chama o processo de múltiplas páginas com as configurações fixas
            await crawl_documentation(
                url,
                UPLOAD_DIR,
                max_depth=MAX_DEPTH,
                max_concurrent=MAX_CONCURRENT,
            )
        else:
            raise HTTPException(status_code=400, detail="Modo inválido. Use 'single' ou 'multi'.")

        # Gera o caminho do arquivo Markdown
        md_file_path = os.path.join(MD_DIR, urlparse(url).netloc, f"{urlparse(url).netloc}.md")
        
        # Verifica se o arquivo existe e retorna seu conteúdo
        if os.path.exists(md_file_path):
            with open(md_file_path, "r", encoding="utf-8") as f:
                content = f.read()
            return JSONResponse(content={"content": content})
        else:
            raise HTTPException(status_code=404, detail="Arquivo Markdown não encontrado.")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
