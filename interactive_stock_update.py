# 文件：/Users/robert/Developer/ProjectQuant/tushare/tushare_2_duckdb/Droid_tushare/interactive_stock_update.py
import os
import pandas as pd
from datetime import datetime
from dateutil.relativedelta import relativedelta
from ts_duckdb_config_1026 import PRO_API, BASIC_DB_PATH, API_CONFIG
from ts_duckdb_engine_1210 import generic_store_data
from ts_duckdb_utils_1109 import get_connection, table_exists, init_table, build_api_params, generate_param_grid
from ts_duckdb_metadata import init_metadata, update_metadata
from ts_duckdb_schema import TABLE_SCHEMAS
from tabulate import tabulate

pro = PRO_API

# === 配置 ===
MAX_OFFSET = 100_000
LIMIT_PER_PAGE = 4000
BATCH_SIZE_STK_REWARDS = 20

# === 工具函数 ===
def input_choice(prompt, options, default=None):
    while True:
        print(prompt)
        for i, opt in enumerate(options, 1):
            print(f"  [{i}] {opt}")
        if default:
            print(f"  [Enter] 默认: {default}")
        choice = input("请选择: ").strip()
        if not choice and default:
            return default
        if choice.isdigit() and 1 <= int(choice) <= len(options):
            return options[int(choice) - 1]
        print("输入无效，请重试\n")

def input_date(prompt, default=None):
    while True:
        val = input(f"{prompt} (YYYYMMDD, 默认 {default}): ").strip()
        if not val:
            return default
        if len(val) == 8 and val.isdigit():
            try:
                datetime.strptime(val, '%Y%m%d')
                return val
            except:
                pass
        print("日期格式错误，请输入 YYYYMMDD\n")

def generate_quarters(start_year, end_date=None):
    if end_date is None:
        end_date = datetime.now().strftime('%Y%m%d')
    end_dt = datetime.strptime(end_date, '%Y%m%d')
    quarters = []
    current = datetime(start_year, 1, 1)
    while current <= end_dt:
        q_end = current + relativedelta(months=3, days=-1)
        if q_end > end_dt:
            q_end = end_dt
        quarters.append((current.strftime('%Y%m%d'), q_end.strftime('%Y%m%d')))
        current += relativedelta(months=3)
    return quarters

def pagenation_quarter(api_name, start_date, end_date, limit=LIMIT_PER_PAGE):
    offset = 0
    all_data = []
    while True:
        params = {'begin_date': start_date, 'end_date': end_date, 'limit': limit, 'offset': offset}
        df = pro.query(api_name, **params)
        if df.empty:
            break
        all_data.append(df)
        if len(df) < limit:
            break
        offset += len(df)
        if offset >= MAX_OFFSET:
            print(f"  警告：offset={offset} 达到上限")
            break
    return pd.concat(all_data, ignore_index=True) if all_data else pd.DataFrame()

def show_validation_report(conn):
    print("\n" + "="*60)
    print("数据校验报告")
    print("="*60)

    tables_to_check = ['stock_basic', 'stk_managers', 'stk_rewards', 'trade_cal', 'hs_const']
    for table in tables_to_check:
        if not table_exists(conn, table):
            continue
        print(f"\n=== {table} 校验 ===")
        count = conn.execute(f"SELECT COUNT(*) FROM \"{table}\"").fetchone()[0]
        print(f"记录数: {count:,}")

        if table == 'stock_basic':
            status = conn.execute("SELECT list_status, COUNT(*) FROM stock_basic GROUP BY list_status").fetchall()
            print("上市状态分布:")
            for s, c in status:
                print(f"  {s}: {c:,}")
            latest = conn.execute("SELECT ts_code, name, list_date FROM stock_basic ORDER BY list_date DESC LIMIT 1").fetchone()
            print(f"最新上市: {latest[0]} ({latest[1]}) {latest[2]}")

        elif table == 'stk_managers':
            min_max = conn.execute("SELECT MIN(begin_date), MAX(begin_date) FROM stk_managers").fetchone()
            print(f"任职时间: {min_max[0]} ~ {min_max[1]}")
            top = conn.execute("SELECT ts_code, COUNT(*) FROM stk_managers GROUP BY ts_code ORDER BY COUNT(*) DESC LIMIT 3").fetchall()
            print("高管人数前3:")
            for code, c in top:
                name = conn.execute("SELECT name FROM stock_basic WHERE ts_code = ?", (code,)).fetchone()
                print(f"  {code} ({name[0] if name else '未知'}): {c:,}人")

        # elif table == 'trade_cal':
        #     min_max = conn.execute("SELECT MIN(cal_date), MAX(cal_date) FROM trade_cal").fetchone()
        #     print(f"交易日覆盖: {min_max[0]} ~ {min_max[1]}")
        #     y2025 = conn.execute("SELECT COUNT(*) FROM trade_cal WHERE cal_date LIKE '2025%' AND is_open = 1").fetchone()[0]
        #     print(f"2025年交易日: {y2025} 天")

        # 在 show_validation_report 函数中，替换 trade_cal 部分

        elif table == 'trade_cal':
            min_max = conn.execute("SELECT MIN(cal_date), MAX(cal_date) FROM trade_cal").fetchone()
            print(f"交易日覆盖: {min_max[0]} ~ {min_max[1]}")

            # 从配置获取交易所列表
            config_exchanges = API_CONFIG['stock_info']['tables']['trade_cal'].get('required_params', {}).get(
                'exchange', [])
            config_exchanges = list(set(config_exchanges))  # 去重

            print("各交易所交易日统计:")
            for exch in config_exchanges:
                count = \
                conn.execute("SELECT COUNT(*) FROM trade_cal WHERE exchange = ? AND is_open = 1", (exch,)).fetchone()[0]
                y2025 = conn.execute(
                    "SELECT COUNT(*) FROM trade_cal WHERE exchange = ? AND cal_date LIKE '2025%' AND is_open = 1",
                    (exch,)).fetchone()[0]
                print(f"  {exch:6}: {count:6,} 天 | 2025年: {y2025:3} 天")

        elif table == 'hs_const':
            count_sh = conn.execute("SELECT COUNT(*) FROM hs_const WHERE hs_type = 'SH'").fetchone()[0]
            count_sz = conn.execute("SELECT COUNT(*) FROM hs_const WHERE hs_type = 'SZ'").fetchone()[0]
            print(f"沪深300: {count_sh} 只, 深证100: {count_sz} 只")

    print("\n校验完成！")

# === 主交互函数 ===
def interactive_update():
    print("Tushare 数据交互式更新工具")
    print("=" * 50)

    with get_connection(BASIC_DB_PATH, read_only=False) as conn:
        if not conn:
            return
        init_metadata(conn, 'stock_info')

        # 获取可用表
        available_tables = {k: v for k, v in API_CONFIG['stock_info']['tables'].items() if k in TABLE_SCHEMAS}
        table_names = list(available_tables.keys())

        while True:
            print("\n可用接口：")
            for i, name in enumerate(table_names, 1):
                desc = available_tables[name].get('desc', name)
                print(f"  [{i}] {name} - {desc}")
            print(f"  [{len(table_names) + 1}] 数据校验报告")  # 新增

            choice = input("\n选择要更新的接口 (q 退出): ").strip()
            if choice == 'q':
                break
            if not choice.isdigit() or int(choice) not in range(1, len(table_names)+1):
                # print("无效选择")
                show_validation_report(conn)
                continue

            table_name = table_names[int(choice) - 1]
            config = available_tables[table_name]
            print(f"\n正在更新: {table_name}")

            if not table_exists(conn, table_name):
                print("表不存在，创建中...")
                init_table(conn, table_name)

            unique_keys = config.get('unique_keys', [])
            date_column = config.get('date_column')
            api_table = config.get('api_table', table_name)

            # === stk_managers: 季度模式 ===
            if table_name == 'stk_managers':
                print("\nstk_managers 季度更新模式")
                max_date = '20141231'
                if table_exists(conn, 'metadata'):
                    meta = conn.execute("SELECT max_date FROM metadata WHERE table_name = 'stk_managers'").fetchone()
                    if meta and meta[0] and meta[0] != 'None':
                        max_date = meta[0]
                try:
                    start_year = int(max_date[:4])
                except:
                    start_year = 2015

                quarters = generate_quarters(start_year=start_year)
                print(f"从 {max_date} 起，共 {len(quarters)} 个季度")

                new_count = 0
                for start_date, end_date in quarters:
                    print(f"\n拉取 {start_date} ~ {end_date}")
                    df = pagenation_quarter(api_table, start_date, end_date)
                    if not df.empty:
                        for col in ['begin_date', 'ann_date']:
                            if col in df.columns:
                                df[col] = pd.to_datetime(df[col], format='%Y%m%d', errors='coerce').dt.strftime('%Y%m%d')
                        stored = generic_store_data(table_name, df, conn, unique_keys, date_column, 'insert_new')
                        new_count += stored
                        print(f"  插入 {stored:,} 条")
                update_metadata(conn, table_name, date_column)
                print(f"stk_managers 更新完成，新增 {new_count:,} 条")

            # === stk_rewards: 批量 ts_code ===
            elif table_name == 'stk_rewards':
                print("\nstk_rewards 批量股票模式")
                ts_codes = [row[0] for row in conn.execute("SELECT ts_code FROM stock_basic").fetchall()]
                batch_size = BATCH_SIZE_STK_REWARDS

                new_count = 0
                for i in range(0, len(ts_codes), batch_size):
                    batch = ts_codes[i:i+batch_size]
                    batch_str = ','.join(batch)
                    print(f"\n批次 {i//batch_size + 1}: {len(batch)} 支")

                    api_params = build_api_params(table_name, '19900101', '19900101', None, {'ts_code': batch_str})
                    df = pro.query(api_table, **api_params)
                    if not df.empty:
                        if 'end_date' in df.columns:
                            df['end_date'] = pd.to_datetime(df['end_date'], format='%Y%m%d', errors='coerce').dt.strftime('%Y%m%d')
                        stored = generic_store_data(table_name, df, conn, unique_keys, date_column, 'insert_new')
                        new_count += stored
                        print(f"  插入 {stored:,} 条")
                update_metadata(conn, table_name, date_column)
                print(f"stk_rewards 更新完成，新增 {new_count:,} 条")

            # === 其他表：通用模式 ===
            else:
                print(f"\n{table_name} 通用更新")
                required_params_config = config.get('required_params', {})

                # 构建参数网格
                param_grid = []
                if required_params_config:
                    # 让用户选择是否使用配置
                    use_config = input(f"是否使用配置参数 {required_params_config}? (y/n, 默认 y): ").strip().lower()
                    if use_config in ['', 'y', 'yes']:
                        param_grid = generate_param_grid(required_params_config)
                        print(f"自动生成 {len(param_grid)} 组参数")
                    else:
                        # 手动输入
                        params = {}
                        for param, values in required_params_config.items():
                            val = input(f"输入 {param} (多个用逗号分隔): ").strip()
                            if val:
                                params[param] = [x.strip() for x in val.split(',')]
                            else:
                                params[param] = values  # 默认使用配置
                        param_grid = [params]
                else:
                    # 无 required_params，直接拉取
                    param_grid = [{}]

                new_count = 0
                for extra_params in param_grid:
                    print(f"\n拉取参数: {extra_params}")
                    api_params = build_api_params(table_name, '19900101', '19900101', None, extra_params)
                    if table_name == 'trade_cal':
                        api_params = {'start_year': 1990}

                    df = pro.query(api_table, **api_params)
                    if not df.empty:
                        if date_column and date_column in df.columns:
                            df[date_column] = pd.to_datetime(df[date_column], format='%Y%m%d',
                                                             errors='coerce').dt.strftime('%Y%m%d')
                        stored = generic_store_data(table_name, df, conn, unique_keys, date_column, 'insert_new')
                        new_count += stored
                        print(f"插入 {stored:,} 条")
                    else:
                        print("本组无数据")

                update_metadata(conn, table_name, date_column)
                print(f"{table_name} 更新完成，新增 {new_count:,} 条")



    print("\n所有操作完成！")

if __name__ == "__main__":
    interactive_update()