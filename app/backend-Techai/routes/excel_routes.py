from fastapi import APIRouter, File, UploadFile, HTTPException
from processing.excel_processor import process_excel_with_output
import os
import shutil
import logging

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter()

# Diretório para armazenar arquivos Excel
EXCEL_DIR = "uploads/excel"
os.makedirs(EXCEL_DIR, exist_ok=True)

@router.post("/excel/")
async def upload_and_process_excel(file: UploadFile = File(...)):
    """
    Faz o upload de um arquivo Excel e gera arquivos .txt e .json com os dados processados.
    """
    try:
        # Verificar extensão do arquivo
        if not file.filename.endswith(('.xls', '.xlsx')):
            raise HTTPException(
                status_code=400,
                detail="Arquivo inválido. Por favor, envie um arquivo Excel (.xls ou .xlsx)"
            )

        # Salvar o arquivo no servidor
        file_path = os.path.join(EXCEL_DIR, file.filename)
        logger.info(f"Salvando arquivo: {file_path}")
        
        with open(file_path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        # Processar o arquivo Excel e gerar os arquivos
        result = process_excel_with_output(file_path)

        return {
            "message": "Arquivo processado com sucesso!",
            "txt_file": os.path.basename(result["txt_path"]),
            "json_file": os.path.basename(result["json_path"]),
            "data": result["data"]
        }
    except Exception as e:
        logger.error(f"Erro ao processar o arquivo: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Fechar o arquivo
        await file.close()