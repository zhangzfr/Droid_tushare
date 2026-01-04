import json

notebook_path = '/Users/robert/Developer/ProjectQuant/tushare/tushare_2_duckdb/Droid_tushare/utils/景气度.ipynb'

try:
    with open(notebook_path, 'r', encoding='utf-8') as f:
        nb = json.load(f)
    
    for cell in nb['cells']:
        if cell['cell_type'] == 'code':
            print("--- CELL ---")
            print(''.join(cell['source']))
            print("\n")
except Exception as e:
    print(f"Error reading notebook: {e}")
