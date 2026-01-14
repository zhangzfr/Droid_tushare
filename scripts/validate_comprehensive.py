#!/usr/bin/env python3
"""
股票数据全量校验与修复脚本 (V2 - API First)

校验逻辑：
1. 股票池定义: stock_basic ∪ bak_basic
2. 两条校验线:
   - 行情线: daily vs bak_daily
   - 指标线: daily_basic vs bak_basic
3. 缺口分析 (Gap Analysis):
   - 理论交易日 vs 实际交易日 vs 停牌记录
   - 区分: 正常停牌 / 异常缺口 (可修复/未解释)

修复策略:
- API First: 发现缺口优先调用 API (daily & suspend_d)
- Local Backup: API 无数据时，仅报告可用本地 bak 数据修复的缺口

使用方法:
    python -m scripts.validate_comprehensive --scan            # 全量扫描
    python -m scripts.validate_comprehensive --scan --sample 100 # 抽样扫描
    python -m scripts.validate_comprehensive --fix-api         # API 自动修复
    python -m scripts.validate_comprehensive --report-local    # 报告可本地修复缺口
"""

import argparse
import sys
import time
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from src.tushare_duckdb.config import API_CONFIG, TUSHARE_TOKEN
from src.tushare_duckdb.utils import get_connection
from src.tushare_duckdb.logger import logger
import tushare as ts

# 初始化 Tushare
pro = ts.pro_api(TUSHARE_TOKEN)
TODAY = datetime.now().strftime('%Y%m%d')

def get_db_paths():
    stock_db = API_CONFIG.get('stock', {}).get('db_path', '')
    events_db = API_CONFIG.get('stock_events', {}).get('db_path', '')
    return stock_db, events_db

class DataValidator:
    def __init__(self, sample_size=None):
        self.stock_db, self.events_db = get_db_paths()
        self.sample_size = sample_size
        self.report = {
            'universe_count': 0,
            'gaps_found': 0,
            'gaps_details': [], # (ts_code, date, type)
            'recoverable_local': 0,
            'unexplained': 0
        }

    def _get_universe(self):
        """获取全量股票池 (stock_basic ∪ bak_basic)"""
        universe = {}
        
        with get_connection(self.stock_db, read_only=True) as conn:
            # 1. 获取所有有数据的代码 (已证实的股票)
            # 只有当代码在 daily 或 bak_daily 中存在时，才被认为是有效历史代码
            # 这能过滤掉如 601313.SH 这种已被合并且无数据的空壳代码
            known_daily = conn.execute("SELECT DISTINCT ts_code FROM daily").fetchall()
            known_bak = conn.execute("SELECT DISTINCT ts_code FROM bak_daily").fetchall()
            valid_codes_set = {r[0] for r in known_daily} | {r[0] for r in known_bak}
            
            # 2. 当前上市 (stock_basic 是最权威的)
            basic = conn.execute("SELECT ts_code, list_date, delist_date FROM stock_basic").fetchall()
            for code, ldate, ddate in basic:
                if not self._is_valid_date(ldate): ldate = None
                if not self._is_valid_date(ddate): ddate = None
                universe[code] = {'list_date': ldate, 'delist_date': ddate}
            
            # 3. 历史列表 (bak_basic 补充 stock_basic 缺失的，如退市股)
            bak = conn.execute("""
                SELECT ts_code, list_date 
                FROM bak_basic 
                WHERE list_date IS NOT NULL AND length(list_date) = 8 AND list_date > '19900101'
            """).fetchall()
            
            for code, ldate in bak:
                if code not in universe:
                    # 关键过滤：必须有数据实证
                    if code in valid_codes_set:
                        universe[code] = {'list_date': ldate, 'delist_date': None} # bak_basic 没 delist_date
                    # else: 丢弃 (幽灵代码)
                else:
                    # 如果 stock_basic 里有，但 list_date 无效，尝试修复
                    if not universe[code]['list_date'] and self._is_valid_date(ldate):
                        universe[code]['list_date'] = ldate

        # 转换为列表
        uni_list = []
        for code, data in universe.items():
            if data['list_date']: # 必须有上市日期才校验
                uni_list.append({'ts_code': code, **data})
        
        # 抽样
        if self.sample_size:
            import random
            uni_list = random.sample(uni_list, min(self.sample_size, len(uni_list)))
            
        self.report['universe_count'] = len(uni_list)
        return uni_list

    def _is_valid_date(self, date_str):
        if not date_str: return False
        if len(date_str) != 8: return False
        if date_str == '0': return False
        return True

    def scan_gaps(self):
        """执行全量缺口扫描"""
        logger.info("开始全量缺口扫描...")
        universe = self._get_universe()
        
        # 截止日期：昨天 (避免误报今天)
        CHECK_END = (datetime.now() - timedelta(days=1)).strftime('%Y%m%d')
        
        # 获取交易日历 (SSE 为准)
        with get_connection(self.events_db, read_only=True) as conn:
            cal = conn.execute(f"SELECT cal_date FROM trade_cal WHERE is_open='1' AND exchange='SSE' AND cal_date<='{CHECK_END}' ORDER BY cal_date").fetchall()
            trade_days = [r[0] for r in cal]
            trade_days_set = set(trade_days)

        # 逐个股票检查 (由于全量加载 daily 太大，这里采用循环查询或优化 SQL)
        # 优化方案：使用 SQL 直接找出缺口，避免 Python 循环
        # 但需要复杂的 SQL 生成预期序列。
        # 折中方案：按 500 只股票一批处理
        
        batch_size = 500
        total_batches = (len(universe) + batch_size - 1) // batch_size
        
        for i in range(total_batches):
            batch = universe[i*batch_size : (i+1)*batch_size]
            logger.info(f"处理批次 {i+1}/{total_batches} ({len(batch)} 只股票)...")
            self._process_batch(batch, trade_days_set)
            
        self._print_scan_summary()

    def _process_batch(self, batch, trade_days_set):
        codes = [item['ts_code'] for item in batch]
        codes_str = "'" + "','".join(codes) + "'"
        
        # 批量获取各表数据
        with get_connection(self.stock_db, read_only=True) as conn:
            # 1. daily
            daily_recs = conn.execute(f"SELECT ts_code, trade_date FROM daily WHERE ts_code IN ({codes_str})").fetchall()
            daily_map = defaultdict(set)
            for c, d in daily_recs: daily_map[c].add(d)
                
            # 2. adj_factor
            adj_recs = conn.execute(f"SELECT ts_code, trade_date FROM adj_factor WHERE ts_code IN ({codes_str})").fetchall()
            adj_map = defaultdict(set)
            for c, d in adj_recs: adj_map[c].add(d)

            # 3. daily_basic
            basic_recs = conn.execute(f"SELECT ts_code, trade_date FROM daily_basic WHERE ts_code IN ({codes_str})").fetchall()
            basic_map = defaultdict(set)
            for c, d in basic_recs: basic_map[c].add(d)

            # 4. bak_daily
            bak_recs = conn.execute(f"SELECT ts_code, trade_date FROM bak_daily WHERE ts_code IN ({codes_str})").fetchall()
            bak_map = defaultdict(set)
            for c, d in bak_recs: bak_map[c].add(d)

        with get_connection(self.events_db, read_only=True) as conn:
            # 5. suspend_d
            susp_recs = conn.execute(f"SELECT ts_code, trade_date FROM suspend_d WHERE ts_code IN ({codes_str})").fetchall()
            susp_map = defaultdict(set)
            for c, d in susp_recs: susp_map[c].add(d)
                
        # 分析矩阵
        for item in batch:
            ts_code = item['ts_code']
            list_date = item['list_date']
            delist_date = item['delist_date']
            
            if not list_date: continue
            
            # 截止日期：昨天
            CHECK_END = (datetime.now() - timedelta(days=1)).strftime('%Y%m%d')
            end_date = min(delist_date, CHECK_END) if delist_date else CHECK_END
            
            # 理论交易日
            expected = [d for d in trade_days_set if list_date <= d <= end_date]
            
            for date in expected:
                has_daily = date in daily_map[ts_code]
                has_adj = date in adj_map[ts_code]
                has_basic = date in basic_map[ts_code]
                has_susp = date in susp_map[ts_code]
                has_bak = date in bak_map[ts_code]
                
                # 判定逻辑
                # 1. 正常: 有daily 且（有adj 或 无需adj? 通常每一天都该有adj）
                #    这里简化：只要 daily/adj/basic 全有，或者 susp 有，就算正常？
                #    用户想要看 adj 是否缺失。
                
                # 如果停牌，通常其他表都没有（除了 possible daily_basic?）
                if has_susp:
                    # 停牌日，不再追究 gap，除非用户想看停牌日是否有 daily_basic?
                    # 按照之前逻辑，停牌日视为正常
                    continue
                
                is_missing = False
                issue_types = []
                
                if not has_daily:
                    issue_types.append('missing_daily')
                    is_missing = True
                if not has_adj:
                    issue_types.append('missing_adj')
                    is_missing = True
                if not has_basic:
                    issue_types.append('missing_basic')
                    is_missing = True
                    
                if is_missing:
                    # 聚合类型
                    if 'missing_daily' in issue_types and 'missing_adj' in issue_types and 'missing_basic' in issue_types:
                        main_type = 'total_gap' # 可能是停牌漏录
                    elif 'missing_daily' in issue_types:
                        main_type = 'missing_daily_only' # 奇怪，有指标均无行情？
                    elif 'missing_adj' in issue_types:
                        main_type = 'missing_adj_only' # 常见
                    else:
                        main_type = 'partial_gap'
                        
                    self.report['gaps_found'] += 1
                    if main_type == 'total_gap' and has_bak:
                        recoverable = True
                    else:
                        recoverable = False

                    self.report['gaps_details'].append({
                        'ts_code': ts_code,
                        'trade_date': date,
                        'daily': int(has_daily),
                        'adj': int(has_adj),
                        'basic': int(has_basic),
                        'bak': int(has_bak),
                        'type': main_type,
                        'recoverable': int(recoverable)
                    })

    def _print_scan_summary(self):
        print("\n" + "="*60)
        print("  校验扫描结果 (Enhanced)")
        print("="*60)
        print(f"  检查股票: {self.report['universe_count']}")
        print(f"  发现异常日: {self.report['gaps_found']}")
        
        df = pd.DataFrame(self.report['gaps_details'])
        if df.empty:
            print("  ✓ 数据完整，无异常。")
            return

        # 统计类型
        print("\n  [异常类型统计]")
        print(df['type'].value_counts().to_string())

        # 导出CSV
        csv_path = './tmp/validation_matrix.csv'
        df.to_csv(csv_path, index=False)
        print(f"\n  矩阵明细已导出至: {csv_path}")
        
        # 导出详细文本报告
        self._generate_range_report(df)

    def _generate_range_report(self, df):
        txt_path = './tmp/validation_detail.txt'
        print(f"  正在生成详细聚合报告: {txt_path} ...")
        
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write("股票数据缺失详情报告 (聚合版)\n")
            f.write(f"生成时间: {datetime.now()}\n")
            f.write("="*80 + "\n\n")
            
            # 按股票分组
            gb = df.groupby('ts_code')
            # 排序：按缺失总天数倒序
            sorted_groups = sorted(gb, key=lambda x: len(x[1]), reverse=True)
            
            for ts_code, group in sorted_groups:
                f.write(f"[{ts_code}] 共 {len(group)} 天异常\n")
                
                # 按类型分组聚合
                type_gb = group.groupby('type')
                for issue_type, sub_group in type_gb:
                    dates = sorted(sub_group['trade_date'].unique())
                    ranges = self._dates_to_ranges(dates)
                    range_str = ", ".join(ranges)
                    f.write(f"  - {issue_type}: {range_str}\n")
                f.write("-" * 40 + "\n")
        
        print("  详细报告生成完成。")

    def _dates_to_ranges(self, dates):
        """将日期列表转为范围字符串列表"""
        if not dates: return []
        # 假设日期是 str 'YYYYMMDD' 或 int
        # 先转 int
        try:
            dates = sorted([int(d) for d in dates])
        except:
            return dates # fallback
            
        ranges = []
        if not dates: return []
        
        start = dates[0]
        prev = dates[0]
        
        from datetime import datetime
        
        # 辅助：判断是否连续 (需要考虑日历，但这里简单判断数值差距不大或者直接显示区间)
        # 简单数值判断对于跨月跨年不准，最好用 date obj
        # 但为了性能，这里简化：如果是连续的 index? 
        # 不，这里最好只是简单的折叠。如果中间缺几天也分开显示。
        # 简单逻辑：如果 diff == 1 (同月日增) 或 diff < 100 (同月跨周?) 
        # 严格连续比较麻烦，需要日历。
        # 这里采用简化策略：只要是列表里连续的，就合并？
        # 不，列表本身就是缺失的日期。
        # 还是采用简单的数值连续判断吧，虽然跨月会断开，但也足够了。
        
        for d in dates[1:]:
            # 简单的 +1 判断无法处理换月 (20200131 -> 20200201)
            # 所以这里只合并真正的连续整数，或者我们容忍跨月断开
            if d == prev + 1:
                prev = d
            else:
                # 尝试用 datetime 判断是否只隔了几天（比如周末）
                # 这里不引入复杂日历，简单断开
                if start == prev:
                    ranges.append(str(start))
                else:
                    ranges.append(f"{start}~{prev}")
                start = d
                prev = d
                
        if start == prev:
            ranges.append(str(start))
        else:
            ranges.append(f"{start}~{prev}")
            
        return ranges

    def fix_with_api(self):
        """执行 API 修复"""
        # 读取扫描结果
        try:
            df = pd.read_csv('./tmp/validation_gaps.csv')
        except FileNotFoundError:
            logger.error("未找到扫描结果，请先运行 --scan")
            return
            
        logger.info(f"开始 API 修复，共 {len(df)} 个缺口任务")
        
        # 按日期分组，批量处理（减少API调用次数）
        # 但 suspend_d 需要按日期获取，daily 也是
        # 注意: pro.daily(trade_date=...) 返回当日所有股票
        # 注意: pro.suspend_d(suspend_date=...) 返回当日所有停牌
        
        dates = df['trade_date'].unique()
        dates.sort()
        
        for i, date in enumerate(dates):
            logger.info(f"处理日期 {date} ({i+1}/{len(dates)})...")
            str_date = str(date)
            
            # 该日期的目标股票
            target_codes = set(df[df['trade_date'] == date]['ts_code'])
            
            try:
                # 1. 获取行情
                daily_df = pro.daily(trade_date=str_date)
                if daily_df is not None and not daily_df.empty:
                    # 筛选出我们缺的股票
                    to_insert_daily = daily_df[daily_df['ts_code'].isin(target_codes)]
                    if not to_insert_daily.empty:
                        self._insert_daily(to_insert_daily)
                        logger.info(f"  [Daily] 修复 {len(to_insert_daily)} 条")
                
                time.sleep(0.3) 
                
                # 2. 获取停牌
                susp_df = pro.suspend_d(suspend_date=str_date)
                if susp_df is not None and not susp_df.empty:
                    to_insert_susp = susp_df[susp_df['ts_code'].isin(target_codes)]
                    if not to_insert_susp.empty:
                        self._insert_suspend(to_insert_susp)
                        logger.info(f"  [Suspend] 修复 {len(to_insert_susp)} 条")
                
                time.sleep(0.3)
                
            except Exception as e:
                logger.error(f"  处理日期 {date} 出错: {e}")
                time.sleep(2)

    def _insert_daily(self, df):
        with get_connection(self.stock_db) as conn:
            # 1. 查出已存在的 (ts_code, trade_date)
            dates = df['trade_date'].unique().tolist()
            if not dates: return
            
            # 构建查询条件
            dates_str = "'" + "','".join([str(d) for d in dates]) + "'"
            codes_str = "'" + "','".join(df['ts_code'].unique().tolist()) + "'"
            
            existing = conn.execute(f"""
                SELECT ts_code, trade_date 
                FROM daily 
                WHERE trade_date IN ({dates_str}) AND ts_code IN ({codes_str})
            """).fetchall()
            existing_set = {(r[0], r[1]) for r in existing}
            
            # 2. 过滤
            to_insert = []
            for _, row in df.iterrows():
                key = (row['ts_code'], row['trade_date'])
                if key not in existing_set:
                    to_insert.append([
                        row['ts_code'], row['trade_date'], 
                        row.get('open'), row.get('high'), row.get('low'), row.get('close'),
                        row.get('pre_close'), row.get('change'), row.get('pct_chg'), 
                        row.get('vol'), row.get('amount')
                    ])
            
            if not to_insert: return

            # 3. 批量插入
            conn.execute("BEGIN")
            for row in to_insert:
                conn.execute("""
                    INSERT INTO daily (ts_code, trade_date, open, high, low, close, 
                                     pre_close, change, pct_chg, vol, amount)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, row)
            conn.execute("COMMIT")

    def _insert_suspend(self, df):
        with get_connection(self.events_db) as conn:
            # 1. 查出已存在的
            dates = df['trade_date'].unique().tolist()
            if not dates: return
            
            dates_str = "'" + "','".join([str(d) for d in dates]) + "'"
            codes_str = "'" + "','".join(df['ts_code'].unique().tolist()) + "'"
            
            existing = conn.execute(f"""
                SELECT ts_code, trade_date 
                FROM suspend_d 
                WHERE trade_date IN ({dates_str}) AND ts_code IN ({codes_str})
            """).fetchall()
            existing_set = {(r[0], r[1]) for r in existing}
            
            # 2. 过滤
            to_insert = []
            for _, row in df.iterrows():
                key = (row['ts_code'], row['trade_date'])
                if key not in existing_set:
                    to_insert.append([
                        row['ts_code'], row['trade_date'], 
                        row.get('suspend_timing'), row.get('suspend_type')
                    ])
            
            if not to_insert: return

            # 3. 批量插入
            conn.execute("BEGIN")
            for row in to_insert:
                conn.execute("""
                    INSERT INTO suspend_d (ts_code, trade_date, suspend_timing, suspend_type)
                    VALUES (?, ?, ?, ?)
                """, row)
            conn.execute("COMMIT")

    def fix_suspend_by_range(self, start_year=1990, end_year=None):
        """按年份批量修复停牌数据"""
        if end_year is None:
            end_year = datetime.now().year
            
        logger.info(f"开始批量修复停牌数据: {start_year} - {end_year}")
        
        for year in range(start_year, end_year + 1):
            start_date = f"{year}0101"
            end_date = f"{year}1231"
            
            logger.info(f"获取停牌数据: {start_date} ~ {end_date} ...")
            try:
                # 批量获取全市场停牌数据
                # Tushare suspend_d 接口分页限制通常是 5000 或 8000
                # 需要分页获取
                offset = 0
                limit = 5000
                while True:
                    df = pro.suspend_d(start_date=start_date, end_date=end_date, limit=limit, offset=offset)
                    if df is None or df.empty:
                        break
                        
                    self._insert_suspend(df)
                    count = len(df)
                    logger.info(f"  - 插入/更新 {count} 条 (Offset {offset})")
                    
                    if count < limit:
                        break
                    offset += limit
                    time.sleep(0.5)
                    
            except Exception as e:
                logger.error(f"处理年份 {year} 失败: {e}")
                time.sleep(2)
        
        logger.info("批量修复完成。")

def main():
    parser = argparse.ArgumentParser(description='股票数据全量校验与修复 (V2)')
    parser.add_argument('--scan', action='store_true', help='执行全量缺口扫描')
    parser.add_argument('--sample', type=int, help='扫描抽样股票数')
    parser.add_argument('--fix-api', action='store_true', help='执行 API 修复 (针对 residual gaps)')
    parser.add_argument('--fix-suspend-range', action='store_true', help='按年份批量修复停牌数据 (推荐优先运行)')
    parser.add_argument('--report-local', action='store_true', help='报告可本地修复缺口')
    parser.add_argument('--start-year', type=int, default=1990, help='批量修复起始年份')
    
    args = parser.parse_args()
    
    validator = DataValidator(sample_size=args.sample)
    
    if args.scan:
        validator.scan_gaps()
    elif args.fix_suspend_range:
        validator.fix_suspend_by_range(start_year=args.start_year)
    elif args.fix_api:
        validator.fix_with_api()
    elif args.report_local:
        validator.report_local_recoverable()
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
