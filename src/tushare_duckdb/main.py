from datetime import datetime, timedelta
import calendar
from tabulate import tabulate
from .metadata import init_metadata, update_metadata
from .data_validation import get_database_status
from .config import PRO_API, BASIC_DB_PATH
from .config import API_CONFIG
from .processor import DataProcessor
from .utils import (
    init_tables_for_category, get_connection, get_trade_dates,
    init_tables_for_category, get_connection, get_trade_dates,
    get_all_dates, table_exists, show_table_statistics, get_quarterly_dates
)
from .logger import logger
import pandas as pd
from .db_explorer import run_explorer
try:
    from tabulate import tabulate
except ImportError:
    tabulate = None

pro = PRO_API

# ==================== 表初始化映射（自动从 API_CONFIG 获取所有类别和表）====================
INIT_TABLES_MAP = {
    cat: lambda conn, c=cat: init_tables_for_category(
        conn, 
        list(API_CONFIG.get(c, {}).get('tables', {}).keys()),
        API_CONFIG.get(c, {}).get('tables', {})
    )
    for cat in API_CONFIG.keys()
}

# ==================== 交互式输入工具函数 ====================
def get_input(prompt, allow_zero=False, default=None):
    while True:
        value = input(prompt).strip()
        if value == '0' and allow_zero:
            return None
        if not value and default is not None:
            return default
        if value:
            return value
        print("输入不能为空，请重新输入（或输入 0 返回上级菜单）")

# ==================== 主函数：数据下载与存储 ====================
def fetch_and_store_data(category, start_date=None, end_date=None, years=None, selected_tables=None,
                         ts_code=None, exchange='SSE', batch_size=50, force_fetch=False, overwrite=False,
                         frequency='daily', fetch_type='range'):
    if category not in API_CONFIG:
        raise ValueError(f"无效类别: {category}")

    config_group = API_CONFIG[category]
    db_path = config_group['db_path']
    all_tables = list(config_group['tables'].keys())
    selected_tables_list = [
        t.strip() for t in (selected_tables or 'all').split(',')
        if t.strip() in all_tables
    ] or all_tables

    logger.info(f"正在处理类别: {category.upper()} | 数据库: {db_path.split('/')[-1]}")
    logger.info(f"选择表: {', '.join(selected_tables_list)}")

    # pledge_detail 专用提醒：优先使用脚本
    if category == 'reference' and selected_tables_list == ['pledge_detail']:
        prompt = (
            "⚠️ pledge_detail 无日期过滤，主 CLI 会对所有股票全量拉取，耗时且易限频。\n"
            "建议改用脚本：python scripts/backfill_pledge_detail.py --smart\n"
            "仍要在 CLI 继续执行吗？(y/n，默认 n): "
        )
        go = input(prompt).strip().lower()
        if go not in ['y', 'yes', '1']:
            logger.info("已取消 pledge_detail 的 CLI 执行，请使用脚本更新。")
            return 0

    with get_connection(db_path, read_only=False) as conn:
        if not conn:
            return 0

        init_metadata(conn, category)
        total_stored = 0

        # 初始化表结构
        init_func = INIT_TABLES_MAP.get(category)
        if not init_func:
            raise ValueError(f"未定义 {category} 的表初始化函数")
        for table in selected_tables_list:
            if not table_exists(conn, table):
                logger.info(f"表 {table} 不存在，正在初始化...")
                init_func(conn)

        current_date = datetime.now().strftime('%Y%m%d')
        
        # 确定日期类型与获取函数
        sample_table = selected_tables_list[0]
        sample_config = config_group['tables'][sample_table]
        requires_date = sample_config.get('requires_date', True)
        date_type = sample_config.get('date_type', 'trade')
        api_date_format = sample_config.get('api_date_format', 'YYYYMMDD')

        # 逻辑：只有交易日类型数据强制限定到今日。自然日类型（如交易日历）允许拉取未来日期。
        if date_type == 'trade':
            end_date = min(end_date or current_date, current_date)
        else:
            end_date = end_date or current_date

        # 获取最早支持日期
        earliest_date = min(
            config_group['tables'][t].get('earliest_date', '19900101')
            for t in selected_tables_list
        )
        # 只对YYYYMMDD格式的earliest_date进行比较
        if len(str(earliest_date)) == 8 and len(start_date or '') == 8:
            start_date = max(start_date or earliest_date, earliest_date)

        # 根据api_date_format选择日期生成函数
        if category == 'finance':
            get_dates_func = get_quarterly_dates
            db_for_dates = None 
        elif api_date_format == 'YYYYQN':
            # 季频数据（如 cn_gdp）：直接使用传入的日期，不做转换
            # 日期列表只需要包含传入的 start/end 以供 processor 使用
            get_dates_func = lambda s, e: [s, e] if s != e else [s]
            db_for_dates = None
        elif api_date_format == 'YYYYMM':
            # 月频数据（如 cn_cpi, cn_ppi）：使用月度日期生成
            from .utils import get_monthly_dates
            get_dates_func = get_monthly_dates
            db_for_dates = None
        else:
            get_dates_func = get_all_dates if (date_type == 'natural' or not requires_date) else get_trade_dates
            db_for_dates = BASIC_DB_PATH if (date_type == 'trade' and requires_date) else db_path
        
        # 生成日期集合
        date_sets = {}
        if years:
            for year in years:
                y_start = f"{year}0101"
                y_end = f"{year}1231"
                if category == 'finance':
                     # 财务数据按年生成4个季度末
                     dates = get_dates_func(y_start, y_end)
                elif api_date_format in ['YYYYQN', 'YYYYMM']:
                     # 特殊格式跳过年份逻辑，直接用原始日期
                     dates = get_dates_func(start_date, end_date)
                elif date_type == 'trade' and requires_date:
                     dates = get_dates_func(db_for_dates, y_start, y_end, exchange, conn=(conn if db_for_dates == db_path else None))
                else:
                     dates = get_dates_func(y_start, y_end)
                
                if dates:
                    date_sets[year] = dates
        else:
            if category == 'finance':
                date_sets[None] = get_dates_func(start_date, end_date)
            elif api_date_format in ['YYYYQN', 'YYYYMM']:
                date_sets[None] = get_dates_func(start_date, end_date)
            elif date_type == 'trade' and requires_date:
                date_sets[None] = get_dates_func(db_for_dates, start_date, end_date, exchange, conn=(conn if db_for_dates == db_path else None))
            else:
                date_sets[None] = get_dates_func(start_date, end_date)
            
            dates = date_sets[None]
            if not dates:
                logger.warning(f"警告：{start_date} ~ {end_date} 无有效日期，已跳过")
                return 0

        logger.info(f"日期范围: {start_date} ~ {end_date}，共 {len(dates)} 个{'交易日' if date_type == 'trade' else '日期'}")

        # === 特殊处理：index_weight 从数据库动态提取 index_codes ===
        # 注意：category 是 'index_member'（类别名），表名是 'index_weight'
        if category == 'index_member' and table_exists(conn, 'index_weight'):
            db_index_codes = conn.execute(
                "SELECT DISTINCT index_code FROM index_weight ORDER BY index_code"
            ).fetchall()
            if db_index_codes:
                dynamic_codes = [row[0] for row in db_index_codes]
                logger.info(f"index_weight: 从数据库提取 {len(dynamic_codes)} 个 index_code")
                # 覆盖配置中的 required_params（使用深拷贝避免污染全局配置）
                import copy
                config_group = copy.deepcopy(config_group)
                for tbl in selected_tables_list:
                    config_group['tables'][tbl]['required_params'] = {'index_codes': dynamic_codes}

        # 开始处理每个表
        for table in selected_tables_list:
            table_config = config_group['tables'][table]
            logger.info(f"→ 正在更新表: {table}")

            # 初始化处理器
            processor = DataProcessor(conn, pro)
            stored = processor.process_dates(
                table_name=table,
                api_config_entry=table_config,
                unique_keys=table_config.get('unique_keys', ['ts_code', 'trade_date']),
                date_list=date_sets[None] if None in date_sets else list(date_sets.values())[0],
                batch_size=int(batch_size),
                date_column_in_db=table_config.get('date_column', 'trade_date'),
                force_fetch=force_fetch,
                overwrite=overwrite,
                ts_code=ts_code,
                fetch_type=fetch_type
            )
            total_stored += stored
            logger.info(f" → 本表完成，存储 {stored} 条")

        return total_stored

    # === 业务逻辑统计报告 ===
    # 移出 with 块之后，确保写锁已释放
    if not requires_date or total_stored > 0:
        for table in selected_tables_list:
            table_config = config_group['tables'][table]
            if 'statistics_queries' in table_config:
                show_table_statistics(db_path, table, table_config['statistics_queries'])

    return total_stored


# ==================== 主交互循环 ====================
def main():
    print("\n" + "=" * 80)
    print("       Tushare 日频数据交互式更新工具（1209 终极版）")
    print("       增量优先 | 强制覆盖 | 精准逐日 | 元数据同步")
    print("=" * 80)

    category_map = {
        '1': 'stock', '2': 'stock_events', '3': 'index', '4': 'index_member',
        '5': 'fund', '6': 'option', '7': 'future', '8': 'bond', '9': 'finance',
        '10': 'margin', '11': 'moneyflow', '12': 'reference', '13': 'macro', '14': 'fx',
        '15': 'commodity'
    }

    all_tables_dict = {k: list(v['tables'].keys()) for k, v in API_CONFIG.items() if k in category_map.values()}

    start_date_default = (datetime.now().replace(day=1) - timedelta(days=1)).replace(day=1).strftime('%Y%m%d')
    end_date_default = datetime.now().strftime('%Y%m%d')

    while True:
        print("\n" + "-" * 60)
        print("主菜单：")
        print(" [ 1] 股票数据         [ 2] 股票事件         [ 3] 指数数据")
        print(" [ 4] 指数权重         [ 5] 基金数据         [ 6] 期权数据")
        print(" [ 7] 期货数据         [ 8] 债券数据         [ 9] 财务数据")
        print(" [10] 融资融券         [11] 资金流向         [12] 参考数据")
        print(" [13] 宏观数据         [14] 外汇数据         [15] 商品数据")
        print(" [16] 查看数据         [17] 数据库管理       [ 0] 退出")
        choice = input("\n请选择操作: ").strip()

        if choice == '0':
            print("再见！数据已安全存储至本地 DuckDB")
            break

        elif choice == '16':
            print("\n" + "=" * 70)
            print("          数据库状态校验（支持数字快速选择）")
            print("=" * 70)

            # === 第一步：显示可选择的类别（与主菜单完全一致）===
            status_menu = {
                '1': 'stock', '2': 'stock_events', '3': 'index', '4': 'index_member',
                '5': 'fund', '6': 'option', '7': 'future', '8': 'bond',
                '9': 'finance', '10': 'margin', '11': 'moneyflow', '12': 'reference',
                '13': 'macro', '14': 'fx', '15': 'commodity', 'all': 'all'
            }

            print("可校验的类别（输入数字或 all）：")
            for num, cat in status_menu.items():
                if num != 'all':
                    desc = {
                        'stock': '股票数据', 'index': '指数数据',
                        'index_member': '指数成员/权重', 'fund': '基金数据',
                        'option': '期权数据', 'future': '期货数据', 'bond': '债券数据', 'finance': '财务数据',
                        'margin': '融资融券', 'moneyflow': '资金流向', 'reference': '参考数据', 'macro': '宏观数据',
                        'fx': '外汇数据', 'commodity': '商品数据(上金所)',
                        'stock_events': '股票事件'
                    }.get(cat, cat)
                    print(f"  [{num.rjust(2)}] {desc}")
            print("  [all] 所有类别")
            print()

            # === 第二步：接收用户输入（支持 1~15、all）===
            while True:
                user_input = input("请选择要校验的类别（输入数字或 all，直接回车默认 all）: ").strip()
                if not user_input:
                    user_input = 'all'
                if user_input in status_menu:
                    selected_key = user_input
                    break
                elif user_input in [str(i) for i in range(1, 16)]:
                    selected_key = user_input
                    break
                else:
                    print("输入无效，请输入 1~15 或 all")

            target_category = status_menu[selected_key] if selected_key != 'all' else 'all'
            print(f"您选择了：{target_category if target_category != 'all' else '所有类别'}")

            # === 第三步：日期范围与详情选项（保持您原习惯）===
            default_start = '20251101'
            default_end = datetime.now().strftime('%Y%m%d')
            
            if target_category == 'finance':
                # 财务数据默认不填日期，由校验函数自动取最近8期
                default_start = ''
                default_end = ''
                print("提示：财务数据默认回溯最近 8 个报告期，直接回车即可。")

            start = get_input(f"开始日期（YYYYMMDD{'，默认 ' + default_start if default_start else '，默认自动'}）: ", default=default_start)
            end = get_input(f"结束日期（YYYYMMDD{'，默认 ' + default_end if default_end else '，默认自动'}）: ", default=default_end)
            
            detailed_input = get_input("是否显示逐日数据量详情？(y/n，默认 y): ", default='y')
            detailed = detailed_input.lower() in ['y', 'yes', '1', '']

            # === 第四步：执行校验（逻辑完全不变）===
            categories_to_check = API_CONFIG.keys() if target_category == 'all' else [target_category]

            all_status = []
            all_daily = []

            for cat in categories_to_check:
                if cat not in API_CONFIG:
                    continue
                if cat not in category_map.values() and target_category != 'all':
                    print(f"跳过不支持的类别: {cat}")
                    continue

                config = API_CONFIG[cat]
                tables_list = [
                    (t, config['tables'][t].get('date_column'))
                    for t in config['tables']
                ]
                # 特殊逻辑：如果是财务校验且用户未输入日期，传递 None 给 validation 函数以触发默认8个季度逻辑
                # 但 validation 函数签名里 start_date/end_date 是必须的吗？get_database_status(..., start_date=start, end_date=end)
                # 我们传入的 start/end 是用户输入的值。
                # 如果用户输入了默认值（main.py里有默认值），我们需要区分。
                # Hack: 如果 cat == 'finance' 且 start/end 是默认值（或者我们修改 input 逻辑让 finance 默认空），
                # 这里简单起见，如果 frequency='quarterly'，我们在 data_validation 里已经处理了 "if not start or not end".
                # 问题是 main.py 在 lines 296-298 强制给了默认值。
                # 我们修改 lines 296-298 的逻辑？不，那样会影响其他。
                # 我们在这里做 override。
                
                val_start = start
                val_end = end
                # 如果是 finance，且用户使用了默认全范围（通常是 20251101-Now），这对于 finance 来说毫无意义（可能只有1个季度）
                # 我们定一个规则：如果用户在 Finance Check 模式下输入了默认日期（或者我们识别出它是 Finance），
                # 最好还是在 input 阶段就改。但 input 阶段是统一的。
                # 可以在 input 阶段判断 target_category。
                
                # Special validation logic for 'macro' to support mixed frequencies
                if cat == 'macro':
                    # Auto-detect tables by frequency from config
                    monthly_table_names = [
                        t for t, cfg in config['tables'].items()
                        if cfg.get('date_column') == 'month' or cfg.get('api_date_format') == 'YYYYMM'
                    ]
                    quarterly_table_names = [
                        t for t, cfg in config['tables'].items()
                        if cfg.get('date_column') == 'quarter' or cfg.get('api_date_format') == 'YYYYQN'
                    ]
                    daily_table_names = [t for t in config['tables'] if t not in monthly_table_names and t not in quarterly_table_names]
                    
                    # Prompt for sub-category
                    print("\n宏观数据包含不同频率的表：")
                    print(f"  1. 日频数据 ({len(daily_table_names)}个): {', '.join(daily_table_names[:3])}...")
                    print(f"  2. 月频数据 ({len(monthly_table_names)}个): {', '.join(monthly_table_names)}")
                    print(f"  3. 季频数据 ({len(quarterly_table_names)}个): {', '.join(quarterly_table_names)}")
                    print("  4. 全部（分开显示）")
                    sub_choice = get_input("请选择 [默认 4]: ", default='4')
                    
                    def run_macro_validation(table_names, freq, section_title):
                        """Helper to run validation and display results for a subset of tables."""
                        if not table_names:
                            return
                        t_list = [(t, config['tables'][t].get('date_column', 'trade_date')) for t in table_names]
                        s, d = get_database_status(
                            db_path=config['db_path'],
                            basic_db_path=BASIC_DB_PATH,
                            tables=t_list,
                            start_date=val_start,
                            end_date=val_end,
                            detailed=detailed,
                            exchange='SSE',
                            frequency=freq
                        )
                        print(f"\n{'=' * 80}")
                        print(f"=== {section_title} ===")
                        if s:
                            print(tabulate(s, headers='keys', tablefmt='psql', stralign='right'))
                        if detailed and d:
                            if freq == 'monthly':
                                date_label = '月'
                            elif freq == 'quarterly':
                                date_label = '季度'
                            else:
                                date_label = '日'
                            print(f"\n逐{date_label}数据量详情（共 {len(d)} {date_label}，完整展示）：")
                            print(tabulate(d, headers='keys', tablefmt='psql', stralign='right'))
                    
                    if sub_choice == '1':
                        run_macro_validation(daily_table_names, 'daily', '日频宏观数据')
                    elif sub_choice == '2':
                        run_macro_validation(monthly_table_names, 'monthly', '月频宏观数据')
                    elif sub_choice == '3':
                        run_macro_validation(quarterly_table_names, 'quarterly', '季频宏观数据')
                    else:  # '4' or default
                        run_macro_validation(daily_table_names, 'daily', '日频宏观数据')
                        run_macro_validation(monthly_table_names, 'monthly', '月频宏观数据')
                        run_macro_validation(quarterly_table_names, 'quarterly', '季频宏观数据')
                    
                    # Skip default display logic for macro
                    continue
                
                else:
                    # Standard logic for other categories
                    frequency = 'daily'
                    if cat == 'finance':
                        frequency = 'quarterly'

                    status, daily = get_database_status(
                        db_path=config['db_path'],
                        basic_db_path=BASIC_DB_PATH,
                        tables=tables_list,
                        start_date=val_start,
                        end_date=val_end,
                        detailed=detailed,
                        exchange='SSE',
                        frequency=frequency
                    )
                all_status.extend(status)
                if daily:
                    all_daily = daily  # 只保留最后一个类别的逐日详情（避免混淆）

            print("\n" + "=" * 80)
            if all_status:
                print(tabulate(all_status, headers='keys', tablefmt='psql', stralign='right'))
            else:
                print("未获取到任何状态信息")

            # === 原代码（有行数限制）===
            # if detailed and all_daily:
            #     print(f"\n逐日数据量详情（共 {len(all_daily)} 天，前50行预览）：")
            #     print(tabulate(all_daily[:50], headers='keys', tablefmt='psql'))

            # === 升级后代码（完整展示 + 智能分页提示）===
            if detailed and all_daily:
                total_days = len(all_daily)
                print(f"\n逐日数据量详情（共 {total_days} 天，完整展示所有日期）：")
                print("=" * 120)

                # 直接完整输出，不再截断
                print(tabulate(all_daily, headers='keys', tablefmt='psql', stralign='right', numalign='right'))

                print("=" * 120)
                print(f"已完整展示全部 {total_days} 天的逐日数据量")
                print("技巧：可使用终端上下滚动，或复制到 Excel/Notion 进一步分析缺失段")
                print("=" * 120)


        elif choice in category_map:
            category = category_map[choice]
            config_group = API_CONFIG[category]
            logger.info(f"您选择了: {choice}. {category.upper()} 数据更新")

            # === 宏观数据特殊处理：频率子菜单 ===
            if category == 'macro':
                macro_tables = API_CONFIG['macro']['tables']
                
                # 按频率分类表
                daily_tables = [t for t, cfg in macro_tables.items() 
                               if cfg.get('date_column') in ['date'] and cfg.get('api_date_format') != 'YYYYMM']
                monthly_tables = [t for t, cfg in macro_tables.items() 
                                 if cfg.get('api_date_format') == 'YYYYMM']
                quarterly_tables = [t for t, cfg in macro_tables.items() 
                                   if cfg.get('api_date_format') == 'YYYYQN']
                
                print("\n宏观数据分类（按数据频率）:")
                print(f"  1. 日频数据 ({len(daily_tables)}个): {', '.join(daily_tables[:5])}{'...' if len(daily_tables) > 5 else ''}")
                print(f"  2. 月频数据 ({len(monthly_tables)}个): {', '.join(monthly_tables)}")
                print(f"  3. 季频数据 ({len(quarterly_tables)}个): {', '.join(quarterly_tables)}")
                print("  4. 全部")
                
                freq_choice = get_input("请选择频率 [默认 4]: ", allow_zero=True, default='4')
                if freq_choice is None: continue
                
                if freq_choice == '1':
                    available_tables = daily_tables
                    date_format_hint = "YYYYMMDD"
                    freq_label = "日频"
                elif freq_choice == '2':
                    available_tables = monthly_tables
                    date_format_hint = "YYYYMM"
                    freq_label = "月频"
                elif freq_choice == '3':
                    available_tables = quarterly_tables
                    date_format_hint = "YYYYQN (如 2019Q1)"
                    freq_label = "季频"
                else:
                    available_tables = list(macro_tables.keys())
                    date_format_hint = "YYYYMMDD/YYYYMM/YYYYQN"
                    freq_label = "全部"
                
                print(f"\n{freq_label}宏观数据可用表（{len(available_tables)}个）: {', '.join(available_tables)}")
                selected_tables = get_input("选择表（逗号分隔，all 为全部，默认 all）: ", allow_zero=True, default='all')
                if selected_tables is None: continue
                
                # 处理表选择
                if selected_tables == 'all':
                    target_tables = available_tables
                else:
                    target_tables = [t.strip() for t in selected_tables.split(',') if t.strip() in available_tables]
                
                # 日期输入（根据选择的频率提供不同提示）
                raw_start = get_input(f"开始日期（{date_format_hint}，默认 {start_date_default}）: ", allow_zero=True, default=start_date_default)
                if raw_start is None: continue
                raw_end = get_input(f"结束日期（{date_format_hint}，默认 {end_date_default}）: ", allow_zero=True, default=end_date_default)
                if raw_end is None: continue
                
                # 对于季度格式，不做转换，直接传递；其他格式做模糊处理
                if 'Q' in raw_start.upper():
                    start_date = raw_start.upper()
                    end_date = raw_end.upper()
                else:
                    # === 日期模糊处理 (YYYYMM -> YYYYMMDD) ===
                    def parse_fuzzy_date(d_str, is_end=False):
                        if len(d_str) == 6:
                            try:
                                dt = datetime.strptime(d_str, '%Y%m')
                                if is_end:
                                    _, last_day = calendar.monthrange(dt.year, dt.month)
                                    return f"{d_str}{last_day}"
                                else:
                                    return f"{d_str}01"
                            except:
                                return d_str
                        return d_str
                    
                    start_date = parse_fuzzy_date(raw_start, is_end=False)
                    end_date = parse_fuzzy_date(raw_end, is_end=True)
                
                batch_size = get_input("批次大小（默认 50）: ", allow_zero=True, default='50')
                if batch_size is None: continue
                
                mode = get_input("模式: 1.增量插入 2.强制覆盖 3.强制去重插入 [默认1]: ", allow_zero=True, default='1')
                if mode not in ['1','2','3']:
                    print("无效模式")
                    continue
                force_fetch = mode in ['2', '3']
                overwrite = mode == '2'
                
                try:
                    # Always pass explicit table list for macro data (not 'all')
                    fetch_and_store_data(
                        category='macro',
                        start_date=start_date,
                        end_date=end_date,
                        selected_tables=','.join(target_tables),
                        ts_code=None,
                        exchange='SSE',
                        batch_size=batch_size,
                        force_fetch=force_fetch,
                        overwrite=overwrite
                    )
                except Exception as e:
                    logger.error(f"更新失败: {e}")
                continue
            
            # === 非宏观数据的标准处理流程 ===
            # === 智能分类：快照数据 vs 行情数据 ===
            config_group_tables = API_CONFIG[category]['tables']
            current_all_tables = all_tables_dict[category]
            
            snapshot_tables = [t for t in current_all_tables if config_group_tables[t].get('requires_date', True) is False]
            market_tables = [t for t in current_all_tables if config_group_tables[t].get('requires_date', True) is not False]
            
            target_tables = current_all_tables
            
            # 如果该类别混合了快照和行情数据，提供子菜单
            if snapshot_tables and market_tables:
                print(f"\n{category.upper()} 数据类型选择：")
                print(f"  1. 基础/快照数据 (Snapshot) - 无需日期 ({len(snapshot_tables)}个表)")
                print(f"  2. 行情/时序数据 (Market)   - 需指定日期 ({len(market_tables)}个表)")
                print(f"  3. 全部")
                
                sub_choice = get_input("请选择数据类型 [默认 3]: ", allow_zero=True, default='3')
                if sub_choice == '1':
                    target_tables = snapshot_tables
                    print(f"\n已选择快照数据模式，自动跳过日期输入。")
                elif sub_choice == '2':
                    target_tables = market_tables
                    print(f"\n已选择行情数据模式。")
                elif sub_choice is None:
                    continue
            
            print(f"可用表（{len(target_tables)}个）: {', '.join(target_tables)}")
            selected_tables = get_input("选择表（逗号分隔，all 为全部，默认 all）: ", allow_zero=True, default='all')
            if selected_tables is None: continue
            
            if selected_tables == 'all':
                final_tables = target_tables
            else:
                 # 校验用户输入的表是否在当前目标列表中
                final_tables = [t.strip() for t in selected_tables.split(',') if t.strip() in target_tables]
            
            if not final_tables:
                print("错误：未选中任何有效表")
                continue

            # 检查是否所有选中的表都不需要日期 (requires_date: false)
            all_tables_no_date = all(config_group_tables[t].get('requires_date', True) is False for t in final_tables)
            
            if all_tables_no_date:
                logger.info("检测到所选表均为基础信息表 (requires_date=False)，自动跳过日期输入")
                # 使用当前日期作为占位符（fetcher会自动忽略）
                start_date = datetime.now().strftime('%Y%m%d')
                end_date = start_date
            else:
                raw_start = get_input(f"开始日期（YYYYMMDD/YYYYMM，默认 {start_date_default}）: ", allow_zero=True, default=start_date_default)
                if raw_start is None: continue
                raw_end = get_input(f"结束日期（YYYYMMDD/YYYYMM，默认 {end_date_default}）: ", allow_zero=True, default=end_date_default)
                if raw_end is None: continue

                # === 日期模糊处理 (YYYYMM -> YYYYMMDD) ===
                def parse_fuzzy_date(d_str, is_end=False):
                    if len(d_str) == 6:
                        try:
                            dt = datetime.strptime(d_str, '%Y%m')
                            if is_end:
                                _, last_day = calendar.monthrange(dt.year, dt.month)
                                return f"{d_str}{last_day}"
                            else:
                                return f"{d_str}01"
                        except:
                            return d_str
                    return d_str

                start_date = parse_fuzzy_date(raw_start, is_end=False)
                end_date = parse_fuzzy_date(raw_end, is_end=True)

                try:
                    datetime.strptime(start_date, '%Y%m%d')
                    datetime.strptime(end_date, '%Y%m%d')
                    if start_date > end_date:
                        print(f"错误：开始日期 {start_date} 不能晚于结束日期 {end_date}")
                        continue
                except:
                    print(f"日期格式错误，支持 YYYYMMDD 或 YYYYMM")
                    continue

            # 交易所选择改为从配置获取
            exchange = config_group.get('list_exchange', 'SSE')

            batch_size = get_input("批次大小（默认 50）: ", allow_zero=True, default='50')
            if batch_size is None: continue

            mode = get_input("模式: 1.增量插入 2.强制覆盖 3.强制去重插入 [默认1]: ", allow_zero=True, default='1')
            if mode not in ['1','2','3']:
                print("无效模式")
                continue
            force_fetch = mode in ['2', '3']
            overwrite = mode == '2'

            ts_code = get_input("特定代码（如指数TS代码，多个逗号分隔，默认留空）: ", allow_zero=True, default='')

            try:
                fetch_and_store_data(
                    category=category,
                    start_date=start_date,
                    end_date=end_date,
                    selected_tables=','.join(final_tables),
                    ts_code=ts_code or None,
                    exchange=exchange,
                    batch_size=batch_size,
                    force_fetch=force_fetch,
                    overwrite=overwrite
                )
            except Exception as e:
                logger.error(f"更新失败: {e}")

        elif choice == '17':
            run_explorer()

        else:
            print("无效选择，请输入有效数字")


if __name__ == "__main__":
    main()