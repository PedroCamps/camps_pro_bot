from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
import os
import json
from processing.pdf_processor import process_pdf

# Inicialização do Router
router = APIRouter()

# Diretórios
UPLOAD_DIR = "uploads"
PDF_DIR = os.path.join(UPLOAD_DIR, "pdfs")
IMAGES_DIR = os.path.join(UPLOAD_DIR, "extracted_images")
JSON_DIR = os.path.join(UPLOAD_DIR, "jsons")

# Garantir que os diretórios existam
os.makedirs(PDF_DIR, exist_ok=True)
os.makedirs(IMAGES_DIR, exist_ok=True)
os.makedirs(JSON_DIR, exist_ok=True)



@router.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    print("Upload endpoint foi acessado")
    """
    Faz o upload de um arquivo PDF.
    """
    # Verifica se o arquivo é um PDF
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Apenas arquivos PDF são permitidos.")

    file_path = os.path.join(PDF_DIR, file.filename)

    # Salva o arquivo no diretório de PDFs
    with open(file_path, "wb") as f:
        f.write(await file.read())

    return {"filename": file.filename, "message": "Upload concluído com sucesso!"}





@router.get("/pdfs/")
def list_pdfs():
    """
    Lista os arquivos PDFs disponíveis
    """
    pdfs = [f for f in os.listdir(PDF_DIR) if f.endswith(".pdf")]
    if not pdfs:
        raise HTTPException(status_code=404, detail="Nenhum arquivo PDF encontrado")
    return {"pdfs": pdfs}

@router.get("/pdfs/{pdf_name}")
def get_pdf_content(pdf_name: str):
    """
    Retorna o conteúdo (texto e imagens) de um PDF processado.
    """
    pdf_path = os.path.join(PDF_DIR, pdf_name)
    if not os.path.exists(pdf_path):
        raise HTTPException(status_code=404, detail=f"O PDF '{pdf_name}' não foi encontrado.")

    # Nome do arquivo JSON baseado no nome do PDF
    json_filename = f"{os.path.splitext(pdf_name)[0]}.json"
    json_path = os.path.join(JSON_DIR, json_filename)

    # Processar o PDF se o JSON não existir
    if not os.path.exists(json_path):
        # Subpasta específica para imagens deste PDF
        pdf_image_dir = os.path.join(IMAGES_DIR, os.path.splitext(pdf_name)[0])
        pdf_data = process_pdf(pdf_path, pdf_image_dir)

        # Salvar o conteúdo processado no JSON
        with open(json_path, "w", encoding="utf-8") as file:
            json.dump(pdf_data, file, ensure_ascii=False, indent=4)
    else:
        # Carregar conteúdo existente
        with open(json_path, "r", encoding="utf-8") as file:
            pdf_data = json.load(file)

    return pdf_data

