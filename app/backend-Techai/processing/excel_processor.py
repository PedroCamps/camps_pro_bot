import pandas as pd
import os
import json
from typing import Dict, Any

def process_excel_with_output(file_path: str) -> Dict[str, Any]:
    """
    Process Excel file and output to JSON and TXT formats.
    """
    # Determine the appropriate engine based on file extension
    file_extension = os.path.splitext(file_path)[1].lower()
    if file_extension == '.xlsx':
        engine = 'openpyxl'
    elif file_extension == '.xls':
        engine = 'pyxlsb'  # Use pyxlsb for older .xls files
    else:
        raise ValueError(f"Unsupported file extension: {file_extension}")
    
    try:
        # Read the Excel file
        df = pd.read_excel(file_path, engine=engine)
        df = df.fillna('null')

        # Convert DataFrame to dictionary
        data_dict = df.to_dict(orient='records')
        
        # Save output files
        base_name = os.path.splitext(file_path)[0]
        json_path = f"{base_name}.json"
        txt_path = f"{base_name}.txt"
        
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data_dict, f, ensure_ascii=False, indent=4)

        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write('\t'.join(df.columns) + '\n')
            for _, row in df.iterrows():
                f.write('\t'.join(str(value) for value in row) + '\n')

        return {'data': data_dict, 'json_path': json_path, 'txt_path': txt_path}
    
    except Exception as e:
        raise Exception(f"Error processing Excel file: {str(e)}")
