
import sys
sys.path.insert(0, '.')
from src.tushare_duckdb.config import API_CONFIG
from src.tushare_duckdb.utils import get_connection

stock_db = API_CONFIG.get('stock', {}).get('db_path', '')

def find_ghost_codes():
    print("正在查找幽灵代码 (存在于数据表但不在 stock_basic)...")
    
    with get_connection(stock_db, read_only=True) as conn:
        # 1. 基准: stock_basic
        basic_codes = set(r[0] for r in conn.execute("SELECT DISTINCT ts_code FROM stock_basic").fetchall())
        print(f"Stock Basic Count: {len(basic_codes)}")
        
        # 2. 数据表
        tables = ['daily', 'daily_basic', 'bak_daily', 'bak_basic']
        ghost_map = {}
        
        for table in tables:
            print(f"Scanning {table}...")
            try:
                codes = set(r[0] for r in conn.execute(f"SELECT DISTINCT ts_code FROM {table}").fetchall())
                ghosts = codes - basic_codes
                for g in ghosts:
                    if g not in ghost_map:
                        ghost_map[g] = []
                    ghost_map[g].append(table)
            except Exception as e:
                print(f"Error scanning {table}: {e}")

    import pandas as pd
    
    # 3. 输出及保存
    print("\n" + "="*60)
    print("  幽灵代码统计")
    print("="*60)
    print(f"总数: {len(ghost_map)}")
    
    if not ghost_map:
        print("未发现幽灵代码。")
        return

    data = []
    for code, sources in ghost_map.items():
        data.append({'ts_code': code, 'sources': ", ".join(sources)})
    
    df = pd.DataFrame(data)
    csv_path = './tmp/ghost_codes.csv'
    df.to_csv(csv_path, index=False)
    print(f"完整清单已保存至: {csv_path}")
    
    # 打印前 20 个示例
    print(df.head(20).to_string(index=False))

if __name__ == "__main__":
    find_ghost_codes()
