# 文件：/Users/robert/Developer/ProjectQuant/tushare/tushare_2_duckdb/Droid_tushare/interactive_finance_update.py
import pandas as pd
import calendar
import time
from datetime import datetime
from dateutil.relativedelta import relativedelta
from ts_duckdb_config_1026 import PRO_API, API_CONFIG
from ts_duckdb_engine_1210 import generic_store_data
from ts_duckdb_utils_1109 import get_connection, table_exists, init_table
from ts_duckdb_metadata import init_metadata, update_metadata
from ts_duckdb_schema import TABLE_SCHEMAS
from tabulate import tabulate

pro = PRO_API
DB_PATH = API_CONFIG['finance']['db_path']

# 自定义报表显示顺序（业务逻辑优先级）
TABLE_DISPLAY_ORDER = [
    'income',         # 利润表 - 最核心
    'balance',        # 资产负债表
    'cashflow',       # 现金流量表
    'forecast',       # 业绩预告
    'express',        # 快报
    'dividend',       # 分红 - 投资者最关心
    'fina_indicator', # 财务指标
    'fina_audit',     # 审计意见
    'fina_mainbz',    # 主营业务构成（你最重视的多版本表）
    'disclosure_date' # 披露日历
]

# 替换所有 fix_table_schema 函数
def fix_table_schema_force_rebuild(table_name):
    """终极方案：重建表，彻底解决 NOT NULL + 依赖问题"""
    with get_connection(DB_PATH, read_only=False) as conn:
        if not conn:
            return
        try:
            # 1. 检查是否已修复（看是否有默认值）
            result = conn.execute(f"PRAGMA table_info(\"{table_name}\")").fetchall()
            col_info = [r for r in result if r[1] == 'update_flag']
            if not col_info:
                print(f"{table_name}: 无 update_flag 字段，跳过")
                return
            if col_info[0][4] == "'0'":  # 默认值已为 '0'
                print(f"{table_name}: 已修复（有默认值），跳过重建")
                return

            print(f"{table_name}: 检测到 NOT NULL 约束，正在重建表（数据100%保留）...")

            # 2. 获取原表结构
            create_sql = conn.execute(f"SHOW CREATE TABLE \"{table_name}\"").fetchone()[0]
            # 3. 复制数据到临时表
            conn.execute(f"CREATE TABLE \"{table_name}_backup\" AS SELECT * FROM \"{table_name}\"")
            # 4. 删除原表
            conn.execute(f"DROP TABLE \"{table_name}\"")
            # 5. 重建表：替换 NOT NULL 为 DEFAULT '0'
            new_sql = create_sql.replace(
                "update_flag VARCHAR NOT NULL",
                "update_flag VARCHAR DEFAULT '0'"
            ).replace(
                "update_flag VARCHAR,",
                "update_flag VARCHAR DEFAULT '0',"
            )
            conn.execute(new_sql)
            # 6. 数据回写
            conn.execute(f"""
                INSERT INTO \"{table_name}\" 
                SELECT *, COALESCE(update_flag, '0') as update_flag 
                FROM \"{table_name}_backup\"
            """)
            # 7. 删除备份
            conn.execute(f"DROP TABLE \"{table_name}_backup\"")

            print(f"{table_name} 重建完成！update_flag 已设置为 DEFAULT '0'")

        except Exception as e:
            print(f"{table_name} 重建失败：{e}（可能已最新或权限问题）")


def fix_table_schema_force_rebuild(table_name):
    """终极重建方案，100% 解决 NOT NULL + 依赖问题"""
    with get_connection(DB_PATH, read_only=False) as conn:
        if not conn:
            return
        try:
            result = conn.execute(f"PRAGMA table_info(\"{table_name}\")").fetchall()
            col_info = [r for r in result if r[1] == 'update_flag']
            if not col_info:
                return
            if col_info[0][4] == "'0'":
                return

            print(f"{table_name}: 正在重建表（数据100%保留）...")
            conn.execute(f"CREATE TABLE \"{table_name}_tmp\" AS SELECT * FROM \"{table_name}\"")
            conn.execute(f"DROP TABLE \"{table_name}\"")

            create_sql = conn.execute(f"SHOW CREATE TABLE \"{table_name}_tmp\"").fetchone()[0]
            new_sql = create_sql.replace(
                "update_flag VARCHAR NOT NULL",
                "update_flag VARCHAR DEFAULT '0'"
            ).replace(
                "update_flag VARCHAR,",
                "update_flag VARCHAR DEFAULT '0',"
            )
            conn.execute(new_sql)
            conn.execute(f"""
                INSERT INTO \"{table_name}\" 
                SELECT *, COALESCE(update_flag, '0') FROM \"{table_name}_tmp\"
            """)
            conn.execute(f"DROP TABLE \"{table_name}_tmp\"")
            print(f"{table_name} 重建成功！")
        except Exception as e:
            print(f"{table_name} 重建失败：{e}")

def fix_dividend_schema():
    with get_connection(DB_PATH, read_only=False) as conn:
        if not conn:
            return
        try:
            # 检查是否已经修复过
            r = conn.execute("SELECT 1 FROM pragma_table_info('dividend') "
                             "WHERE name='update_flag' AND notnull=0").fetchone()
            if r:
                return  # 已经修复
            conn.execute('ALTER TABLE dividend ALTER COLUMN update_flag DROP NOT NULL')
            conn.execute("UPDATE dividend SET update_flag = '0' WHERE update_flag IS NULL")
            conn.execute("ALTER TABLE dividend ALTER COLUMN update_flag SET DEFAULT '0'")
            print("dividend 表结构已修复：update_flag 不再强制 NOT NULL")
        except Exception as e:
            print(f"修复 dividend 表结构时出错（可能已经是最新的）：{e}")

def fix_fina_mainbz_schema():
    with get_connection(DB_PATH, read_only=False) as conn:
        if not conn:
            return
        try:
            # 检查是否已修复
            r = conn.execute("SELECT 1 FROM pragma_table_info('fina_mainbz') "
                             "WHERE name='update_flag' AND notnull=0").fetchone()
            if r:
                return

            conn.execute('ALTER TABLE fina_mainbz ALTER COLUMN update_flag DROP NOT NULL')
            conn.execute("UPDATE fina_mainbz SET update_flag = '0' WHERE update_flag IS NULL")
            conn.execute("ALTER TABLE fina_mainbz ALTER COLUMN update_flag SET DEFAULT '0'")
            print("fina_mainbz 表结构已修复：update_flag 可为空 + 默认0")
        except Exception as e:
            print(f"fina_mainbz 表结构修复跳过（可能已完成）：{e}")

def ensure_db_ready():
    """确保数据库和所有表都存在（支持重建）"""
    print(f"\n检查数据库: {DB_PATH}")
    with get_connection(DB_PATH, read_only=False) as conn:
        if not conn:
            print("无法连接数据库，程序终止")
            return False

        init_metadata(conn, 'finance')
        # 在 ensure_db_ready() 中调用
        # fix_table_schema_force_rebuild('dividend')
        # fix_table_schema_force_rebuild('fina_mainbz')

        # fix_dividend_schema()  # <--- 新增
        # fix_fina_mainbz_schema()  # 新增
        for table_name in API_CONFIG['finance']['tables'].keys():
            if not table_exists(conn, table_name):
                init_table(conn, table_name)
                print(f"自动创建表: {table_name}")
        print("数据库就绪！")
        return True

def input_date(prompt, default):
    while True:
        val = input(f"{prompt} (YYYYMMDD, 建议季度末如20230331, 默认 {default}): ").strip()
        if not val:
            return default
        if len(val) == 8 and val.isdigit():
            try:
                datetime.strptime(val, '%Y%m%d')
                return val
            except:
                pass
        print("格式错误！请重新输入")

def generate_quarters(start, end):
    """生成标准财务季度末日期"""
    quarters = []
    current = datetime.strptime(start, '%Y%m%d')
    end_dt = datetime.strptime(end, '%Y%m%d')
    while current <= end_dt:
        month = current.month
        if month <= 3:
            q_month = 3
        elif month <= 6:
            q_month = 6
        elif month <= 9:
            q_month = 9
        else:
            q_month = 12
            current = current.replace(year=current.year + 1, month=1)  # 跳到下一年
            continue
        q_year = current.year
        _, last_day = calendar.monthrange(q_year, q_month)
        q_end_dt = datetime(q_year, q_month, last_day)
        if q_end_dt >= current and q_end_dt <= end_dt:
            quarters.append(q_end_dt.strftime('%Y%m%d'))
        # 移到下一个季度起始
        current = q_end_dt + relativedelta(days=1)
    return quarters

def is_valid_period(date_str):
    """严格校验是否为标准财务报告期末"""
    month_day = date_str[4:]
    return month_day in ['0331', '0630', '0930', '1231']

def pagenation_vip(api, period, limit, param, retries=3):
    offset = 0
    data = []
    while True:
        for attempt in range(retries):
            try:
                params = {param: period, 'limit': limit, 'offset': offset}
                df = pro.query(api, **params)
                print(f"API调用: {api}, period={period}, offset={offset}, 返回行: {len(df)}")
                if df.empty:
                    return pd.concat(data, ignore_index=True) if data else pd.DataFrame()
                data.append(df)
                offset += len(df)
                break
            except Exception as e:
                print(f"API错误 (尝试{attempt+1}): {e}")
                time.sleep(5 * (attempt + 1))
        else:
            raise RuntimeError(f"API调用失败: {api}, period={period}")
        if len(df) < limit:
            break
    return pd.concat(data, ignore_index=True) if data else pd.DataFrame()

def validate_before_update(conn, table_name, quarters):
    """更新前校验：显示每个季度的现有数据量"""
    print(f"\n更新前校验 [{table_name}]")
    config = API_CONFIG['finance']['tables'][table_name]
    date_col = config.get('date_column', 'end_date')

    rows = []
    total_existing = 0
    for q in quarters:
        cnt = conn.execute(f"SELECT COUNT(*) FROM \"{table_name}\" WHERE \"{date_col}\" = ?", (q,)).fetchone()[0]
        total_existing += cnt
        rows.append([q, cnt])
    rows.append(["合计", total_existing])

    print(tabulate(rows, headers=["报告期", "现有记录数"], tablefmt="grid"))
    return total_existing

# clean_finance_df 完整替换为以下版本
def clean_finance_df(df, table_name, unique_keys):
    if df.empty:
        return df, 0, 0, 0

    print(f"  原始数据 {len(df):,} 行")
    df.columns = [col.strip().lower() for col in df.columns]

    # === 1. ann_date 三层填充（保持）===
    ann_date_filled = 0
    if 'ann_date' in df.columns:
        if 'f_ann_date' in df.columns:
            mask = df['ann_date'].isna() | (df['ann_date'] == '')
            valid = df['f_ann_date'].notna() & (df['f_ann_date'] != '')
            filled = mask & valid
            df.loc[filled, 'ann_date'] = df.loc[filled, 'f_ann_date']
            ann_date_filled += filled.sum()

        mask = df['ann_date'].isna() | (df['ann_date'] == '')
        if 'end_date' in df.columns:
            valid = df['end_date'].notna() & (df['end_date'] != '')
            filled = mask & valid
            df.loc[filled, 'ann_date'] = df.loc[filled, 'end_date']
            ann_date_filled += filled.sum()

        mask = df['ann_date'].isna() | (df['ann_date'] == '')
        if mask.any():
            df.loc[mask, 'ann_date'] = df.loc[mask, 'end_date'] if 'end_date' in df.columns else '20990101'
            ann_date_filled += mask.sum()

        print(f"  ann_date 填充完成，共填充 {ann_date_filled} 条")

    # === 2. 字段过滤（保持）===
    config = API_CONFIG['finance']['tables'][table_name]
    fields = config.get('fields', [])
    if fields:
        fields_lower = [f.lower() for f in fields]
        preserve = {'ts_code', 'end_date', 'ann_date', 'f_ann_date', 'update_flag', 'last_updated'}
        keep_cols = [c for c in df.columns if c in fields_lower or c in preserve]
        df = df[keep_cols]

    # === 3. 关键：fina_mainbz 生成递增 update_flag ===
    if table_name == 'fina_mainbz':
        biz_keys = ['ts_code', 'end_date', 'bz_item', 'bz_code']
        if all(k in df.columns for k in biz_keys):
            # 优先按 ann_date 排序（最新公告在前）
            if 'ann_date' in df.columns:
                df = df.sort_values(['ts_code', 'end_date', 'bz_item', 'bz_code', 'ann_date'],
                                  ascending=[True, True, True, True, False])
            # 生成版本号
            df['update_flag'] = df.groupby(biz_keys).cumcount().astype(str)
            print(f"  fina_mainbz: 生成了 {df['update_flag'].nunique()} 个版本 (update_flag 0~{df['update_flag'].max()})")
        else:
            df['update_flag'] = '0'

    # === 4. dividend 也补全 ===
    elif table_name == 'dividend':
        if 'update_flag' not in df.columns:
            df['update_flag'] = '0'
        else:
            df['update_flag'] = df['update_flag'].fillna('0').astype(str)
        print("  dividend: 强制填充 update_flag = '0'")

    # === 5. 日期格式化 ===
    for col in ['end_date', 'ann_date', 'f_ann_date']:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], format='%Y%m%d', errors='coerce').dt.strftime('%Y%m%d')

    # === 6. 最终 NULL 检查 ===
    if 'ann_date' in df.columns:
        nulls = df['ann_date'].isna().sum()
        if nulls:
            print(f"  警告：仍有 {nulls} 条 ann_date 为 NULL，已丢弃")
            df = df.dropna(subset=['ann_date'])

    print(f"  清洗后准备插入 {len(df):,} 条")
    return df, ann_date_filled, 0, len(df)

def show_validation_time_travel(conn):
    print("\n" + "=" * 110)
    print("财务数据报告期（end_date）任意区间查询神器")
    print("=" * 110)

    # === 交互式输入年份区间 ===
    while True:
        try:
            start_year = input("\n请输入起始年份（例如 2018，四位数，留空默认 2015）: ").strip()
            start_year = int(start_year) if start_year else 2015
            if start_year < 1990 or start_year > 2030:
                print("年份范围 1990~2030")
                continue
            break
        except:
            print("请输入有效年份！")

    while True:
        try:
            end_year = input("请输入结束年份（例如 2025，留空默认今年）: ").strip()
            end_year = int(end_year) if end_year else datetime.now().year
            if end_year < start_year or end_year > 2030:
                print(f"结束年份必须 ≥ {start_year}")
                continue
            break
        except:
            print("请输入有效年份！")

    start_date = f"{start_year}0101"
    end_date = f"{end_year}1231"

    print(f"\n正在查询 {start_year} ~ {end_year} 年之间的季度数据...")
    print(f"时间范围：{start_date} ~ {end_date}")

    # === 生成该区间所有季度末 ===
    quarters = []
    current = datetime(start_year, 1, 1)
    while current.year <= end_year:
        for month in [3, 6, 9, 12]:
            q_end = datetime(current.year, month, 1) + relativedelta(months=1, days=-1)
            if start_year <= q_end.year <= end_year:
                quarters.append(q_end.strftime('%Y%m%d'))
        current = current.replace(year=current.year + 1)
    quarters = [q for q in quarters if start_date <= q <= end_date]
    quarters = sorted(quarters, reverse=True)

    # 在 show_validation_time_travel() 中替换绘表部分
    quarters = sorted(quarters)

    # === 按顺序统计每一张表 ===
    data = {}
    for table_name in TABLE_DISPLAY_ORDER:
        if table_name not in API_CONFIG['finance']['tables']:
            continue
        config = API_CONFIG['finance']['tables'][table_name]
        date_col = config.get('date_column', 'end_date')

        row = []
        total = 0
        for q in quarters:
            try:
                cnt = conn.execute(f"SELECT COUNT(*) FROM \"{table_name}\" WHERE \"{date_col}\" = ?", (q,)).fetchone()[
                    0]
            except:
                cnt = 0
            row.append(f"{cnt:,}")
            total += cnt
        row.append(f"{total:,}")
        data[table_name] = row

    # === 构建完美 DataFrame：行=报表，列=季度+总计 ===
    columns = quarters + ['总计']
    df_display = pd.DataFrame(data, index=columns).T
    df_display = df_display.loc[TABLE_DISPLAY_ORDER]
    df_display = df_display.T # 强制行顺序

    # === 美化输出：千位分隔 + 右对齐 ===
    print("\n" + tabulate(
        df_display,
        headers='keys',
        tablefmt='simple',
        stralign='right',
        numalign='right'
    ))
    print(f"\n查询完成！您已成功穿越至 {start_year} ~ {end_year} 年")

def interactive_update():
    if not ensure_db_ready():
        return

    print("\n" + "=" * 80)
    print("Tushare 财务数据交互式更新工具（支持插入/覆盖模式）")
    print("=" * 80)

    tables = list(API_CONFIG['finance']['tables'].keys())
    while True:
        print("\n可用财务表：")
        for i, t in enumerate(tables, 1):
            print(f"  [{i}] {t}")
        print(f"  [{len(tables) + 1}] 数据校验")
        print("  [q] 退出")

        choice = input("\n选择: ").strip()
        if choice == 'q':
            break
        if choice.isdigit() and int(choice) == len(tables) + 1:
            with get_connection(DB_PATH) as conn:
                if conn:
                    show_validation_time_travel(conn)
            continue
        if not choice.isdigit() or int(choice) not in range(1, len(tables) + 1):
            print("无效选择")
            continue

        idx = int(choice) - 1
        table_name = tables[idx]
        config = API_CONFIG['finance']['tables'][table_name]
        api = config['api_table']
        limit = config['limit']
        param = config['param_name']
        date_col = config.get('date_column', 'end_date')
        start = input_date("开始季度", '20200101')
        end = input_date("结束季度", datetime.now().strftime('%Y%m%d'))
        quarters = generate_quarters(start, end)
        print(f"将更新以下季度：{quarters}")

        with get_connection(DB_PATH, read_only=False) as conn:
            if not conn:
                continue

            # 1. 更新前校验
            existing_count = validate_before_update(conn, table_name, quarters)

            # 2. 选择存储模式
            print("\n存储模式：")
            print("  1. 插入新数据（推荐，保留历史）")
            print("  2. 覆盖指定季度（删除后重新插入）")
            mode = input("请选择模式 (1/2): ").strip()
            overwrite = (mode == '2')

            if overwrite:
                confirm = input(f"警告：将删除 {quarters} 的所有数据，确定？(yes/NO): ")
                if confirm.lower() != 'yes':
                    print("已取消")
                    continue

            # 自动推导主键（带容错）
            try:
                sql = TABLE_SCHEMAS[table_name].upper()
                pk_start = sql.find('PRIMARY KEY (') + 13
                if pk_start == 12:  # 未找到复合主键
                    pk_start = sql.find('PRIMARY KEY') + len('PRIMARY KEY')
                    pk_end = sql.find(')', pk_start)
                    if pk_end == -1:
                        pk_end = len(sql)
                else:
                    pk_end = sql.find(')', pk_start)
                pk_str = sql[pk_start:pk_end]
                unique_keys = [c.strip().strip('"').strip("'") for c in pk_str.split(',')]
                print(f"  使用主键去重: {unique_keys}")
            except Exception as e:
                print(f"  警告：无法解析 {table_name} 的主键，使用默认去重键")
                unique_keys = ['ts_code', 'end_date', 'ann_date', 'update_flag']
                unique_keys = [k for k in unique_keys if k in API_CONFIG['finance']['tables'][table_name].get('fields', []) or k in ['ts_code', 'end_date']]

            new_total = 0

            valid_quarters = [q for q in quarters if is_valid_period(q)]
            if len(valid_quarters) < len(quarters):
                print(f"警告：{len(quarters) - len(valid_quarters)} 个无效报告期，已过滤")
            quarters = valid_quarters

            for q in quarters:
                print(f"\n拉取报告期: {q}")
                df = pagenation_vip(api, q, limit, param)
                if df.empty:
                    print("  无数据（可能是未来季度或已最新）")
                    continue

                df_clean, filled_cnt, removed_cnt, final_cnt = clean_finance_df(df, table_name, unique_keys)

                if df_clean.empty:
                    print("  清洗后无数据，跳过")
                    continue

                # 存储（stored 是真实插入数）
                stored = generic_store_data(
                    table_name, df_clean, conn, unique_keys,
                    date_column=date_col,
                    storage_mode='replace' if overwrite else 'insert_new',
                    overwrite_start_date=q if overwrite else None,
                    overwrite_end_date=q if overwrite else None
                )

                if stored > 0:
                    new_total += stored
                    print(f"  本季度实际插入 {stored:,} 条（公告填充 {filled_cnt}）")
                else:
                    print(f"  本季度无新数据插入（stored={stored}）")

            # 更新元数据
            update_metadata(conn, table_name, date_col)

            # 更新后校验
            print(f"\n更新后校验 [{table_name}]")
            validate_before_update(conn, table_name, quarters)

            # 最终总结（不再使用未定义的 stored）
            print(f"\n{table_name} 更新完成！")
            if overwrite:
                print(f"  覆盖模式：重新写入 {new_total:,} 条")
            else:
                print(f"  插入模式：实际新增 {new_total:,} 条（原 {existing_count:,} → 现 {existing_count + new_total:,}）")

if __name__ == "__main__":
    interactive_update()