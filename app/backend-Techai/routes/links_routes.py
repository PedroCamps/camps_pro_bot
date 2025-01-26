import os
from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel
from processing.link_processor import crawl_documentation, crawl_single_page # Importa a função de processamento
import asyncio

router = APIRouter()

# Diretório de saída para os arquivos gerados
UPLOAD_DIR = "uploads"
MD_DIR = os.path.join(UPLOAD_DIR, "MD_links")

# Modelo para entrada de dados
class CrawlRequest(BaseModel):
    base_url: str
    mode: str = "single"
    max_depth: int = 1
    max_concurrent: int = 10

@router.post("/crawl/")
async def start_crawl(request: CrawlRequest, background_tasks: BackgroundTasks):
    """Inicia o processo de crawling."""
    try:
        if request.mode == "single":
            success = await crawl_single_page(request.base_url, UPLOAD_DIR)
            if not success:
                raise HTTPException(status_code=500, detail="Failed to crawl the provided URL.")
            return {"message": "Crawling for a single page completed successfully."}
        elif request.mode == "multi":
            background_tasks.add_task(
                crawl_documentation,
                request.base_url,
                UPLOAD_DIR,
                request.max_depth,
                request.max_concurrent
            )
            return {"message": "Crawling task for multiple pages started successfully."}
        else:
            raise HTTPException(status_code=400, detail="Invalid mode. Use 'single' or 'multi'.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@router.get("/list-md-files/")
async def list_md_files():
    """Lista os arquivos Markdown gerados."""
    try:
        files = [f for f in os.listdir(MD_DIR) if os.path.isfile(os.path.join(MD_DIR, f))]
        return {"files": files}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/download-md/{filename}")
async def download_md_file(filename: str):
    """Permite baixar um arquivo Markdown específico."""
    file_path = os.path.join(MD_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found.")
    return FileResponse(file_path, media_type="text/markdown", filename=filename)
