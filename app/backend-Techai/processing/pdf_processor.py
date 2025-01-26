import fitz  
import os
import json

def process_pdf(file_path, output_dir="uploads/extracted_images/"):
    """
    Processa um arquivo PDF, extraindo texto e imagens de cada página.

    Args:
        file_path (str): Caminho completo para o arquivo PDF.
        output_dir (str): Diretório onde as imagens extraídas serão salvas.

    Returns:
        dict: Estrutura contendo texto e informações de imagens por página.
    """
    # Nome da subpasta baseada no nome do PDF
    pdf_name = os.path.splitext(os.path.basename(file_path))[0]
    pdf_output_dir = os.path.join(output_dir, pdf_name)

    # Criar subpasta para o PDF
    os.makedirs(pdf_output_dir, exist_ok=True)

    pdf_data = {}
    pdf_document = fitz.open(file_path)

    for page_number in range(len(pdf_document)):
        page = pdf_document[page_number]
        page_text = page.get_text()
        images = page.get_images(full=True)

        image_list = []
        for img_index, img in enumerate(images):
            xref = img[0]
            base_image = pdf_document.extract_image(xref)
            image_bytes = base_image["image"]
            image_ext = base_image["ext"]

            # Nome da imagem: page_X_image_Y.ext
            image_filename = f"page_{page_number + 1}_image_{img_index + 1}.{image_ext}"
            image_path = os.path.join(pdf_output_dir, image_filename)

            # Salvar imagem no disco
            with open(image_path, "wb") as image_file:
                image_file.write(image_bytes)

            # Metadados da imagem
            image_metadata = {
                "path": image_path,
                "metadata": {
                    "xref": xref,
                    "width": base_image.get("width"),
                    "height": base_image.get("height"),
                },
            }
            image_list.append(image_metadata)

        # Armazenar texto e imagens da página
        pdf_data[f"page_{page_number + 1}"] = {
            "text": page_text,
            "images": image_list,
        }

    pdf_document.close()

    # Retornar a estrutura em JSON
    return pdf_data

