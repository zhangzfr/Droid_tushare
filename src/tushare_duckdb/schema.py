# 统一表结构配置：{table_name: "CREATE TABLE SQL"}
TABLE_SCHEMAS = {
    # === stock 相关 ===
    'daily': """
        CREATE TABLE daily (
            ts_code VARCHAR NOT NULL,
            trade_date VARCHAR NOT NULL,
            open DOUBLE,
            high DOUBLE,
            low DOUBLE,
            close DOUBLE,
            pre_close DOUBLE,
            change DOUBLE,
            pct_chg DOUBLE,
            vol DOUBLE,
            amount DOUBLE,
            PRIMARY KEY (ts_code, trade_date)
        )""",
    'adj_factor': """
        CREATE TABLE adj_factor (
            ts_code VARCHAR NOT NULL,
            trade_date VARCHAR NOT NULL,
            adj_factor DOUBLE,
            PRIMARY KEY (ts_code, trade_date)
        )""",
    'daily_basic': """
        CREATE TABLE daily_basic (
            ts_code VARCHAR NOT NULL,
            trade_date VARCHAR NOT NULL,
            close DOUBLE,
            turnover_rate DOUBLE,
            turnover_rate_f DOUBLE,
            volume_ratio DOUBLE,
            pe DOUBLE,
            pe_ttm DOUBLE,
            pb DOUBLE,
            ps DOUBLE,
            ps_ttm DOUBLE,
            dv_ratio DOUBLE,
            dv_ttm DOUBLE,
            total_share DOUBLE,
            float_share DOUBLE,
            free_share DOUBLE,
            total_mv DOUBLE,
            circ_mv DOUBLE,
            PRIMARY KEY (ts_code, trade_date)
        )""",
    'stk_limit': """
        CREATE TABLE stk_limit (
            ts_code VARCHAR NOT NULL,
            trade_date VARCHAR NOT NULL,
            pre_close DOUBLE,
            up_limit DOUBLE,
            down_limit DOUBLE,
            PRIMARY KEY (ts_code, trade_date)
        )""",
    'suspend_d': """
        CREATE TABLE suspend_d (
            ts_code VARCHAR NOT NULL,
            trade_date VARCHAR NOT NULL,
            suspend_timing VARCHAR,
            suspend_type VARCHAR,
            PRIMARY KEY (ts_code, trade_date)
            )""",
    'bak_basic': """
        CREATE TABLE bak_basic (
            trade_date VARCHAR NOT NULL,
            ts_code VARCHAR NOT NULL,
            name VARCHAR,
            industry VARCHAR,
            area VARCHAR,
            pe DOUBLE,
            float_share DOUBLE,
            total_share DOUBLE,
            total_assets DOUBLE,
            liquid_assets DOUBLE,
            fixed_assets DOUBLE,
            reserved DOUBLE,
            reserved_pershare DOUBLE,
            eps DOUBLE,
            bvps DOUBLE,
            pb DOUBLE,
            list_date VARCHAR,
            undp DOUBLE,
            per_undp DOUBLE,
            rev_yoy DOUBLE,
            profit_yoy DOUBLE,
            gpr DOUBLE,
            npr DOUBLE,
            holder_num INTEGER,
            PRIMARY KEY (ts_code, trade_date)
            )""",

    # === ref 相关 ===
    'block_trade': """
        CREATE TABLE block_trade (
            ts_code VARCHAR NOT NULL,        -- TS代码
            trade_date VARCHAR NOT NULL,     -- 交易日期
            price DOUBLE,                    -- 成交价
            vol DOUBLE,                      -- 成交量（万股）
            amount DOUBLE,                   -- 成交金额
            buyer VARCHAR,                   -- 买方营业部
            seller VARCHAR,                  -- 卖方营业部
            PRIMARY KEY (ts_code, trade_date)
        )""",

    # === basic 相关 ===
    'trade_cal': """
        CREATE TABLE trade_cal (
            exchange VARCHAR,        -- 交易所 SSE上交所 SZSE深交所
            cal_date VARCHAR,        -- 日历日期
            is_open VARCHAR,         -- 是否交易 0休市 1交易
            pretrade_date VARCHAR    -- 上一个交易日
            last_updated TIMESTAMP, -- << 新增或确认存在 (虽然通常每日更新，但保持一致性)
            PRIMARY KEY (exchange, cal_date) -- << 新增主键)""",
    'stock_basic': """
        CREATE TABLE stock_basic (
            ts_code VARCHAR,         -- TS代码
            symbol VARCHAR,         -- 股票代码
            name VARCHAR,           -- 股票名称
            area VARCHAR,           -- 地域
            industry VARCHAR,       -- 所属行业
            fullname VARCHAR,       -- 股票全称
            enname VARCHAR,         -- 英文全称
            cnspell VARCHAR,        -- 拼音缩写
            market VARCHAR,         -- 市场类型（主板/创业板/科创板/CDR）
            exchange VARCHAR,       -- 交易所代码
            curr_type VARCHAR,      -- 交易货币
            list_status VARCHAR,    -- 上市状态 L上市 D退市 P暂停上市
            list_date VARCHAR,      -- 上市日期
            delist_date VARCHAR,    -- 退市日期
            is_hs VARCHAR,          -- 是否沪深港通标的，N否 H沪股通 S深股通
            act_name VARCHAR,       -- 实控人名称
            act_ent_type VARCHAR    -- 实控人企业性质
            last_updated TIMESTAMP  -- << 新增或确认存在
            )""",
    'namechange': """
        CREATE TABLE namechange (
            ts_code VARCHAR,         -- TS代码
            name VARCHAR,           -- 证券名称
            start_date VARCHAR,     -- 开始日期
            end_date VARCHAR,       -- 结束日期
            ann_date VARCHAR,       -- 公告日期
            change_reason VARCHAR,  -- 变更原因
            last_updated TIMESTAMP, -- << 确认类型为 TIMESTAMP
            PRIMARY KEY (ts_code, name, start_date, ann_date) -- << 示例主键，根据API_CONFIG调整
        )
    """,
    'hs_const': """
        CREATE TABLE hs_const (
            ts_code VARCHAR,         -- TS代码
            hs_type VARCHAR,         -- 沪深港通类型SH沪SZ深
            in_date VARCHAR,         -- 纳入日期
            out_date VARCHAR,        -- 剔除日期
            is_new VARCHAR           -- 是否最新 1是 0否
            last_updated TIMESTAMP, -- << 新增或确认存在
            PRIMARY KEY (ts_code, hs_type, in_date) -- << 示例主键，根据API_CONFIG调整
        )""",
    'stk_managers': """
        CREATE TABLE stk_managers (
            ts_code VARCHAR,         -- TS股票代码
            ann_date VARCHAR,        -- 公告日期
            name VARCHAR,            -- 姓名
            gender VARCHAR,          -- 性别
            lev VARCHAR,             -- 岗位类别
            title VARCHAR,           -- 岗位
            edu VARCHAR,             -- 学历
            national VARCHAR,        -- 国籍
            birthday VARCHAR,        -- 出生年月
            begin_date VARCHAR,      -- 上任日期
            end_date VARCHAR,        -- 离任日期
            resume VARCHAR,          -- 个人简历
            last_updated TIMESTAMP, -- << 新增或确认存在
            PRIMARY KEY (ts_code, name, ann_date, begin_date) -- << 示例主键，根据API_CONFIG调整
        )""",
    'stk_rewards': """
        CREATE TABLE stk_rewards (
            ts_code VARCHAR,         -- TS股票代码
            ann_date VARCHAR,        -- 公告日期
            end_date VARCHAR,        -- 截止日期
            name VARCHAR,            -- 姓名
            title VARCHAR,           -- 职务
            reward DOUBLE,           -- 报酬
            hold_vol DOUBLE,         -- 持股数
            last_updated TIMESTAMP, -- << 新增或确认存在
            PRIMARY KEY (ts_code, name, ann_date, end_date) -- << 示例主键，根据API_CONFIG调整
        )""",
    'stock_company': """
        CREATE TABLE stock_company (
            ts_code VARCHAR,         -- 股票代码
            com_name VARCHAR,        -- 公司全称
            com_id VARCHAR,          -- 统一社会信用代码
            exchange VARCHAR,        -- 交易所代码
            chairman VARCHAR,        -- 法人代表
            manager VARCHAR,         -- 总经理
            secretary VARCHAR,       -- 董秘
            reg_capital DOUBLE,      -- 注册资本(万元)
            setup_date VARCHAR,      -- 注册日期
            province VARCHAR,        -- 所在省份
            city VARCHAR,            -- 所在城市
            introduction VARCHAR,    -- 公司介绍
            website VARCHAR,         -- 公司主页
            email VARCHAR,           -- 电子邮件
            office VARCHAR,          -- 办公室
            employees INTEGER,       -- 员工人数
            main_business VARCHAR,   -- 主要业务及产品
            business_scope VARCHAR   -- 经营范围
            last_updated TIMESTAMP  -- << 新增
            -- PRIMARY KEY (ts_code) -- << 示例主键，根据API_CONFIG调整)""",

    # === options 相关 ===
    'opt_basic': """
        CREATE TABLE opt_basic (
            ts_code VARCHAR,                 -- 期权代码（主键）
            exchange VARCHAR,                -- 交易所代码（如 SSE-上海，SZSE-深圳）
            name VARCHAR,                    -- 期权名称
            per_unit VARCHAR,                -- 每张期权对应的数量
            opt_code VARCHAR,                -- 期权标准代码
            opt_type VARCHAR,                -- 期权类型（如 Vanilla-普通期权）
            call_put VARCHAR,                -- 看涨看跌类型（C-看涨，P-看跌）
            exercise_type VARCHAR,           -- 行权类型（如 A-美式，E-欧式）
            exercise_price DOUBLE,           -- 行权价格
            s_month VARCHAR,                 -- 结算月份
            maturity_date VARCHAR,           -- 到期日期
            list_price DOUBLE,               -- 上市价格
            list_date VARCHAR,               -- 上市日期
            delist_date VARCHAR,             -- 摘牌日期
            last_edate VARCHAR,              -- 最后行权日期
            last_ddate VARCHAR,              -- 最后交割日期
            quote_unit VARCHAR,              -- 报价单位
            min_price_chg VARCHAR,           -- 最小价格变动单位
            last_updated TIMESTAMP,          -- 最后更新时间
            PRIMARY KEY (ts_code),           -- << 新增主键)
            )""",
    'opt_daily': """
        CREATE TABLE opt_daily (
            ts_code VARCHAR NOT NULL,        -- 期权代码
            trade_date VARCHAR NOT NULL,     -- 交易日期
            exchange VARCHAR,                -- 交易所代码（如 SSE-上海，SZSE-深圳）
            pre_settle DOUBLE,               -- 前结算价
            pre_close DOUBLE,                -- 前收盘价
            open DOUBLE,                     -- 开盘价
            high DOUBLE,                     -- 最高价
            low DOUBLE,                      -- 最低价
            close DOUBLE,                    -- 收盘价
            settle DOUBLE,                   -- 结算价
            vol DOUBLE,                      -- 成交量（张）
            amount DOUBLE,                   -- 成交额（元）
            oi DOUBLE,                       -- 持仓量（张）
            PRIMARY KEY (ts_code, trade_date))""",

    # === moneyflow 相关 ===
    'moneyflow': """
        CREATE TABLE moneyflow (
            ts_code VARCHAR NOT NULL,        -- 股票代码
            trade_date VARCHAR NOT NULL,     -- 交易日期
            buy_sm_vol INTEGER,              -- 小单买入量（手）
            buy_sm_amount DOUBLE,            -- 小单买入金额（元）
            sell_sm_vol INTEGER,             -- 小单卖出量（手）
            sell_sm_amount DOUBLE,           -- 小单卖出金额（元）
            buy_md_vol INTEGER,              -- 中单买入量（手）
            buy_md_amount DOUBLE,            -- 中单买入金额（元）
            sell_md_vol INTEGER,             -- 中单卖出量（手）
            sell_md_amount DOUBLE,           -- 中单卖出金额（元）
            buy_lg_vol INTEGER,              -- 大单买入量（手）
            buy_lg_amount DOUBLE,            -- 大单买入金额（元）
            sell_lg_vol INTEGER,             -- 大单卖出量（手）
            sell_lg_amount DOUBLE,           -- 大单卖出金额（元）
            buy_elg_vol INTEGER,             -- 特大单买入量（手）
            buy_elg_amount DOUBLE,           -- 特大单买入金额（元）
            sell_elg_vol INTEGER,            -- 特大单卖出量（手）
            sell_elg_amount DOUBLE,          -- 特大单卖出金额（元）
            net_mf_vol INTEGER,              -- 净流入量（手）
            net_mf_amount DOUBLE,            -- 净流入金额（元）
            PRIMARY KEY (ts_code, trade_date))""",
    'moneyflow_ths': """
        CREATE TABLE moneyflow_ths (
            trade_date VARCHAR NOT NULL,     -- 交易日期
            ts_code VARCHAR NOT NULL,        -- 股票代码
            name VARCHAR,                    -- 股票名称
            pct_change DOUBLE,               -- 涨跌幅（%）
            latest DOUBLE,                   -- 最新价
            net_amount DOUBLE,               -- 净流入金额（元）
            net_d5_amount DOUBLE,            -- 5日净流入金额（元）
            buy_lg_amount DOUBLE,            -- 大单买入金额（元）
            buy_lg_amount_rate DOUBLE,       -- 大单买入金额占比（%）
            buy_md_amount DOUBLE,            -- 中单买入金额（元）
            buy_md_amount_rate DOUBLE,       -- 中单买入金额占比（%）
            buy_sm_amount DOUBLE,            -- 小单买入金额（元）
            buy_sm_amount_rate DOUBLE,       -- 小单买入金额占比（%）
            PRIMARY KEY (ts_code, trade_date)
        )""",
    'moneyflow_dc': """
        CREATE TABLE moneyflow_dc (
            trade_date VARCHAR NOT NULL,     -- 交易日期
            ts_code VARCHAR NOT NULL,        -- 股票代码
            name VARCHAR,                    -- 股票名称
            pct_change DOUBLE,               -- 涨跌幅（%）
            close DOUBLE,                    -- 收盘价
            net_amount DOUBLE,               -- 净流入金额（元）
            net_amount_rate DOUBLE,          -- 净流入金额占比（%）
            buy_elg_amount DOUBLE,           -- 特大单买入金额（元）
            buy_elg_amount_rate DOUBLE,      -- 特大单买入金额占比（%）
            buy_lg_amount DOUBLE,            -- 大单买入金额（元）
            buy_lg_amount_rate DOUBLE,       -- 大单买入金额占比（%）
            buy_md_amount DOUBLE,            -- 中单买入金额（元）
            buy_md_amount_rate DOUBLE,       -- 中单买入金额占比（%）
            buy_sm_amount DOUBLE,            -- 小单买入金额（元）
            buy_sm_amount_rate DOUBLE,       -- 小单买入金额占比（%）
            PRIMARY KEY (ts_code, trade_date)
        )""",
    'moneyflow_ind_ths': """
        CREATE TABLE moneyflow_ind_ths (
            trade_date VARCHAR NOT NULL,     -- 交易日期
            ts_code VARCHAR NOT NULL,        -- 行业代码
            industry VARCHAR,                -- 行业名称
            lead_stock VARCHAR,              -- 领涨股票代码
            close DOUBLE,                    -- 收盘价
            pct_change DOUBLE,               -- 涨跌幅（%）
            company_num INTEGER,             -- 公司数量
            pct_change_stock DOUBLE,         -- 领涨股票涨跌幅（%）
            close_price DOUBLE,              -- 领涨股票收盘价
            net_buy_amount DOUBLE,           -- 净买入金额（元）
            net_sell_amount DOUBLE,          -- 净卖出金额（元）
            net_amount DOUBLE,               -- 净流入金额（元）
            PRIMARY KEY (ts_code, trade_date)
        )""",
    'moneyflow_ind_dc': """
        CREATE TABLE moneyflow_ind_dc (
            trade_date VARCHAR NOT NULL,     -- 交易日期
            ts_code VARCHAR NOT NULL,        -- 行业代码
            name VARCHAR,                    -- 行业名称
            pct_change DOUBLE,               -- 涨跌幅（%）
            close DOUBLE,                    -- 收盘价
            net_amount DOUBLE,               -- 净流入金额（元）
            net_amount_rate DOUBLE,          -- 净流入金额占比（%）
            buy_elg_amount DOUBLE,           -- 特大单买入金额（元）
            buy_elg_amount_rate DOUBLE,      -- 特大单买入金额占比（%）
            buy_lg_amount DOUBLE,            -- 大单买入金额（元）
            buy_lg_amount_rate DOUBLE,       -- 大单买入金额占比（%）
            buy_md_amount DOUBLE,            -- 中单买入金额（元）
            buy_md_amount_rate DOUBLE,       -- 中单买入金额占比（%）
            buy_sm_amount DOUBLE,            -- 小单买入金额（元）
            buy_sm_amount_rate DOUBLE,       -- 小单买入金额占比（%）
            buy_sm_amount_stock VARCHAR,     -- 小单买入主力股票
            rank INTEGER,                    -- 排名
            PRIMARY KEY (ts_code, trade_date)
        )""",
    'moneyflow_mkt_dc': """
        CREATE TABLE moneyflow_mkt_dc (
            trade_date VARCHAR PRIMARY KEY,  -- 交易日期（主键）
            close_sh DOUBLE,                 -- 上证收盘价
            pct_change_sh DOUBLE,            -- 上证涨跌幅（%）
            close_sz DOUBLE,                 -- 深证收盘价
            pct_change_sz DOUBLE,            -- 深证涨跌幅（%）
            net_amount DOUBLE,               -- 净流入金额（元）
            net_amount_rate DOUBLE,          -- 净流入金额占比（%）
            buy_elg_amount DOUBLE,           -- 特大单买入金额（元）
            buy_elg_amount_rate DOUBLE,      -- 特大单买入金额占比（%）
            buy_lg_amount DOUBLE,            -- 大单买入金额（元）
            buy_lg_amount_rate DOUBLE,       -- 大单买入金额占比（%）
            buy_md_amount DOUBLE,            -- 中单买入金额（元）
            buy_md_amount_rate DOUBLE,       -- 中单买入金额占比（%）
            buy_sm_amount DOUBLE,            -- 小单买入金额（元）
            buy_sm_amount_rate DOUBLE        -- 小单买入金额占比（%）
        )""",
    'moneyflow_cnt_ths': """
        CREATE TABLE moneyflow_cnt_ths (
            trade_date VARCHAR NOT NULL,
            ts_code VARCHAR NOT NULL,
            name VARCHAR,
            lead_stock VARCHAR,
            close_price DOUBLE,
            pct_change DOUBLE,
            industry_index DOUBLE,
            company_num INTEGER,
            pct_change_stock DOUBLE,
            net_buy_amount DOUBLE,
            net_sell_amount DOUBLE,
            net_amount DOUBLE,
            last_updated TIMESTAMP,
            PRIMARY KEY (ts_code, trade_date, name)
        )""",

    # === index 相关 ===
    'index_basic': """
        CREATE TABLE index_basic (
            "ts_code" VARCHAR PRIMARY KEY,
            "name" VARCHAR,
            "fullname" VARCHAR,
            "market" VARCHAR,
            "publisher" VARCHAR,
            "index_type" VARCHAR,
            "category" VARCHAR,
            "base_date" VARCHAR,
            "base_point" DOUBLE,
            "list_date" VARCHAR,
            "weight_rule" VARCHAR,
            "desc" VARCHAR,
            "exp_date" VARCHAR,
            "last_updated" TIMESTAMP
        )""",
    'sw_index_classify_2014': """
        CREATE TABLE sw_index_classify_2014 (
            index_code VARCHAR,
            industry_name VARCHAR,
            level VARCHAR,
            industry_code VARCHAR,
            is_pub VARCHAR,
            parent_code VARCHAR,
            src VARCHAR,
            last_updated TIMESTAMP,
            PRIMARY KEY (index_code)
        )""",
    'sw_index_classify_2021': """
        CREATE TABLE sw_index_classify_2021 (
            index_code VARCHAR,
            industry_name VARCHAR,
            level VARCHAR,
            industry_code VARCHAR,
            is_pub VARCHAR,
            parent_code VARCHAR,
            src VARCHAR,
            last_updated TIMESTAMP,
            PRIMARY KEY (index_code)
        )""",
    'sw_index_member_all': """
        CREATE TABLE sw_index_member_all (
            "l1_code" VARCHAR,          -- 一级行业代码
            "l1_name" VARCHAR,          -- 一级行业名称
            "l2_code" VARCHAR,          -- 二级行业代码
            "l2_name" VARCHAR,          -- 二级行业名称
            "l3_code" VARCHAR,          -- 三级行业代码
            "l3_name" VARCHAR,          -- 三级行业名称
            "ts_code" VARCHAR,          -- 成分股票代码
            "name" VARCHAR,             -- 成分股票名称
            "in_date" VARCHAR,          -- 纳入日期
            "out_date" VARCHAR,         -- 剔除日期
            "is_new" VARCHAR,           -- 是否最新
            PRIMARY KEY ("ts_code", "in_date")
        )""",
    'ths_index': """
        CREATE TABLE ths_index (
            ts_code VARCHAR,
            name VARCHAR,
            count INTEGER,
            exchange VARCHAR,
            list_date VARCHAR,
            type VARCHAR,
            last_updated TIMESTAMP,
            PRIMARY KEY (ts_code)
        )""",
    'ths_member': """
        CREATE TABLE ths_member (
            ts_code VARCHAR,
            con_code VARCHAR,
            con_name VARCHAR,
            weight FLOAT,
            in_date VARCHAR,
            out_date VARCHAR,
            is_new VARCHAR,
            last_updated TIMESTAMP,
            PRIMARY KEY (ts_code, con_code)
        )""",
    'dc_index': """
        CREATE TABLE dc_index (
            ts_code VARCHAR,
            trade_date VARCHAR,
            name VARCHAR,
            leading_stock VARCHAR,  -- 重命名为 leading_stock
            leading_code VARCHAR,
            pct_change FLOAT,
            leading_pct FLOAT,
            total_mv FLOAT,
            turnover_rate FLOAT,
            up_num INTEGER,
            down_num INTEGER,
            last_updated TIMESTAMP,
            PRIMARY KEY (ts_code, trade_date)
        )""",
    'dc_member': """
        CREATE TABLE dc_member (
            trade_date VARCHAR,
            ts_code VARCHAR,
            con_code VARCHAR,
            name VARCHAR,
            last_updated TIMESTAMP,
            PRIMARY KEY (ts_code, con_code, trade_date)
        )""",
    'index_daily': """
        CREATE TABLE index_daily (
            ts_code VARCHAR NOT NULL,      -- 指数代码
            trade_date VARCHAR NOT NULL,   -- 交易日期
            close DOUBLE,                  -- 收盘点位
            open DOUBLE,                   -- 开盘点位
            high DOUBLE,                   -- 最高点位
            low DOUBLE,                    -- 最低点位
            pre_close DOUBLE,              -- 前收盘点位
            change DOUBLE,                 -- 涨跌点位
            pct_chg DOUBLE,                -- 涨跌幅（%）
            vol DOUBLE,                    -- 成交量
            amount DOUBLE,                 -- 成交额
            PRIMARY KEY (ts_code, trade_date)
        )""",
    'index_dailybasic': """
        CREATE TABLE index_dailybasic (
            ts_code VARCHAR NOT NULL,      -- 指数代码
            trade_date VARCHAR NOT NULL,   -- 交易日期
            total_mv DOUBLE,               -- 总市值（亿元）
            float_mv DOUBLE,               -- 流通市值（亿元）
            total_share DOUBLE,            -- 总股本（亿股）
            float_share DOUBLE,            -- 流通股本（亿股）
            free_share DOUBLE,             -- 自由流通股本（亿股）
            turnover_rate DOUBLE,          -- 换手率（%）
            turnover_rate_f DOUBLE,        -- 自由流通换手率（%）
            pe DOUBLE,                     -- 市盈率
            pe_ttm DOUBLE,                 -- 市盈率（TTM）
            pb DOUBLE,                     -- 市净率
            PRIMARY KEY (ts_code, trade_date)
        )""",
    'daily_info': """
        CREATE TABLE daily_info (
            trade_date VARCHAR NOT NULL,   -- 交易日期
            ts_code VARCHAR NOT NULL,      -- 市场代码（如 SH-上海，SZ-深圳）
            ts_name VARCHAR,               -- 市场名称
            com_count INTEGER,             -- 公司数量
            total_share DOUBLE,            -- 总股本（亿股）
            float_share DOUBLE,            -- 流通股本（亿股）
            total_mv DOUBLE,               -- 总市值（亿元）
            float_mv DOUBLE,               -- 流通市值（亿元）
            amount DOUBLE,                 -- 成交额（亿元）
            vol DOUBLE,                    -- 成交量（亿股）
            trans_count INTEGER,           -- 交易笔数
            pe DOUBLE,                     -- 市盈率
            tr DOUBLE,                     -- 换手率（%）
            exchange VARCHAR,              -- 交易所
            PRIMARY KEY (trade_date, ts_code)
        )""",
    'sz_daily_info': """
        CREATE TABLE sz_daily_info (
            trade_date VARCHAR NOT NULL,   -- 交易日期
            ts_code VARCHAR NOT NULL,      -- 市场代码
            count INTEGER,                 -- 交易公司数量
            amount DOUBLE,                 -- 成交额（亿元）
            vol DOUBLE,                    -- 成交量（亿股）
            total_share DOUBLE,            -- 总股本（亿股）
            total_mv DOUBLE,               -- 总市值（亿元）
            float_share DOUBLE,            -- 流通股本（亿股）
            float_mv DOUBLE,               -- 流通市值（亿元）
            PRIMARY KEY (trade_date, ts_code)
        )""",
    'ths_daily': """
        CREATE TABLE ths_daily (
            ts_code VARCHAR NOT NULL,      -- 指数代码
            trade_date VARCHAR NOT NULL,   -- 交易日期
            open DOUBLE,                   -- 开盘点位
            high DOUBLE,                   -- 最高点位
            low DOUBLE,                    -- 最低点位
            close DOUBLE,                  -- 收盘点位
            pre_close DOUBLE,              -- 前收盘点位
            avg_price DOUBLE,              -- 平均价格
            change DOUBLE,                 -- 涨跌点位
            pct_change DOUBLE,             -- 涨跌幅（%）
            vol DOUBLE,                    -- 成交量
            turnover_rate DOUBLE,          -- 换手率（%）
            PRIMARY KEY (ts_code, trade_date)
        )""",
    'ci_daily': """
        CREATE TABLE ci_daily (
            ts_code VARCHAR NOT NULL,      -- 指数代码
            trade_date VARCHAR NOT NULL,   -- 交易日期
            open DOUBLE,                   -- 开盘点位
            low DOUBLE,                    -- 最低点位
            high DOUBLE,                   -- 最高点位
            close DOUBLE,                  -- 收盘点位
            pre_close DOUBLE,              -- 前收盘点位
            change DOUBLE,                 -- 涨跌点位
            pct_change DOUBLE,             -- 涨跌幅（%）
            vol DOUBLE,                    -- 成交量
            amount DOUBLE,                 -- 成交额
            PRIMARY KEY (ts_code, trade_date)
        )""",
    'sw_daily': """
        CREATE TABLE sw_daily (
            ts_code VARCHAR NOT NULL,      -- 指数代码
            trade_date VARCHAR NOT NULL,   -- 交易日期
            name VARCHAR,                  -- 指数名称
            open DOUBLE,                   -- 开盘点位
            low DOUBLE,                    -- 最低点位
            high DOUBLE,                   -- 最高点位
            close DOUBLE,                  -- 收盘点位
            change DOUBLE,                 -- 涨跌点位
            pct_change DOUBLE,             -- 涨跌幅（%）
            vol DOUBLE,                    -- 成交量
            amount DOUBLE,                 -- 成交额
            pe DOUBLE,                     -- 市盈率
            pb DOUBLE,                     -- 市净率
            float_mv DOUBLE,               -- 流通市值（亿元）
            total_mv DOUBLE,               -- 总市值（亿元）
            PRIMARY KEY (ts_code, trade_date)
        )""",
    'dc_daily': """
        CREATE TABLE dc_daily (
            ts_code VARCHAR,
            trade_date VARCHAR,
            close FLOAT,
            open FLOAT,
            high FLOAT,
            low FLOAT,
            change FLOAT,
            pct_change FLOAT,
            vol FLOAT,
            amount FLOAT,
            swing FLOAT,
            turnover_rate FLOAT,
            PRIMARY KEY (ts_code, trade_date)
        )""",
    'tdx_index': """
        CREATE TABLE tdx_index (
            ts_code VARCHAR,
            trade_date VARCHAR,
            name VARCHAR,
            idx_type VARCHAR,
            idx_count INTEGER,
            total_share FLOAT,
            float_share FLOAT,
            total_mv FLOAT,
            float_mv FLOAT,
            last_updated TIMESTAMP,
            PRIMARY KEY (ts_code, trade_date)
        )""",
    'tdx_member': """
        CREATE TABLE tdx_member (
                ts_code VARCHAR,
                trade_date VARCHAR,
                con_code VARCHAR,
                con_name VARCHAR,
                last_updated TIMESTAMP,
                PRIMARY KEY (ts_code, con_code, trade_date)
            )""",
    'tdx_daily': """
        CREATE TABLE tdx_daily (
            ts_code VARCHAR,
            trade_date VARCHAR,
            close FLOAT,
            open FLOAT,
            high FLOAT,
            low FLOAT,
            pre_close FLOAT,
            change FLOAT,
            pct_change FLOAT,
            vol FLOAT,
            amount FLOAT,
            rise VARCHAR,
            vol_ratio FLOAT,
            turnover_rate FLOAT,
            swing FLOAT,
            up_num INTEGER,
            down_num INTEGER,
            limit_up_num INTEGER,
            limit_down_num INTEGER,
            lu_days INTEGER,
            "3day" FLOAT,
            "5day" FLOAT,
            "10day" FLOAT,
            "20day" FLOAT,
            "60day" FLOAT,
            mtd FLOAT,
            ytd FLOAT,
            "1year" FLOAT,
            pe VARCHAR,
            pb VARCHAR,
            float_mv FLOAT,
            ab_total_mv FLOAT,
            float_share FLOAT,
            total_share FLOAT,
            bm_buy_net FLOAT,
            bm_buy_ratio FLOAT,
            bm_net FLOAT,
            bm_ratio FLOAT,
            PRIMARY KEY (ts_code, trade_date)
        )""",
    'index_global': """
        CREATE TABLE index_global (
            ts_code VARCHAR NOT NULL,      -- 指数代码
            trade_date VARCHAR NOT NULL,   -- 交易日期
            open DOUBLE,                   -- 开盘点位
            close DOUBLE,                  -- 收盘点位
            high DOUBLE,                   -- 最高点位
            low DOUBLE,                    -- 最低点位
            pre_close DOUBLE,              -- 前收盘点位
            change DOUBLE,                 -- 涨跌点位
            pct_chg DOUBLE,                -- 涨跌幅（%）
            swing DOUBLE,                  -- 振幅（%）
            vol DOUBLE,                    -- 成交量
            amount DOUBLE,
            PRIMARY KEY (ts_code, trade_date)
        )""",

    'index_weight': """
        CREATE TABLE index_weight (
            index_code VARCHAR NOT NULL,   -- 指数代码
            con_code VARCHAR NOT NULL,     -- 成分股代码
            trade_date VARCHAR NOT NULL,   -- 交易日期
            weight DOUBLE,                 -- 权重
            PRIMARY KEY (index_code, con_code, trade_date)
        )""",

    # === margin 相关 ===
    'margin': """
        CREATE TABLE margin (
            trade_date VARCHAR NOT NULL,     -- 交易日期
            exchange_id VARCHAR NOT NULL,    -- 交易所代码（如 SSE-上海，SZSE-深圳）
            rzye DOUBLE,                     -- 融资余额（元）
            rzmre DOUBLE,                    -- 融资买入额（元）
            rzche DOUBLE,                    -- 融资偿还额（元）
            rqye DOUBLE,                     -- 融券余额（元）
            rqmcl DOUBLE,                    -- 融券卖出量（股）
            rzrqye DOUBLE,                   -- 融资融券余额（元）
            rqyl DOUBLE,                     -- 融券余量（股）
            PRIMARY KEY (trade_date, exchange_id)
        )""",
    'margin_detail': """
        CREATE TABLE margin_detail (
            trade_date VARCHAR NOT NULL,     -- 交易日期
            ts_code VARCHAR NOT NULL,        -- 股票代码
            rzye DOUBLE,                     -- 融资余额（元）
            rqye DOUBLE,                     -- 融券余额（元）
            rzmre DOUBLE,                    -- 融资买入额（元）
            rqyl DOUBLE,                     -- 融券余量（股）
            rzche DOUBLE,                    -- 融资偿还额（元）
            rqchl DOUBLE,                    -- 融券偿还量（股）
            rqmcl DOUBLE,                    -- 融券卖出量（股）
            rzrqye DOUBLE,                   -- 融资融券余额（元）
            PRIMARY KEY (trade_date, ts_code)
        )""",
    'margin_secs': """
        CREATE TABLE margin_secs (
            trade_date VARCHAR NOT NULL,     -- 交易日期
            ts_code VARCHAR NOT NULL,        -- 股票代码
            name VARCHAR,                    -- 股票名称
            exchange VARCHAR,                -- 交易所代码（如 SSE-上海，SZSE-深圳）
            PRIMARY KEY (trade_date, ts_code)
        )""",
    'slb_sec': """
        CREATE TABLE slb_sec (
            trade_date VARCHAR NOT NULL,     -- 交易日期
            ts_code VARCHAR NOT NULL,        -- 股票代码
            name VARCHAR,                    -- 股票名称
            ope_inv DOUBLE,                  -- 期初余额（股）
            lent_qnt DOUBLE,                 -- 出借数量（股）
            cls_inv DOUBLE,                  -- 期末余额（股）
            end_bal DOUBLE,                  -- 期末余额（元）
            PRIMARY KEY (trade_date, ts_code)
        )""",
    'slb_len': """
        CREATE TABLE slb_len (
            trade_date VARCHAR PRIMARY KEY,  -- 交易日期（主键）
            ob DOUBLE,                       -- 期初余额（元）
            auc_amount DOUBLE,               -- 出借成交金额（元）
            repo_amount DOUBLE,              -- 融入金额（元）
            repay_amount DOUBLE,             -- 归还金额（元）
            cb DOUBLE                        -- 期末余额（元）
        )""",
    'slb_sec_detail': """
        CREATE TABLE slb_sec_detail (
            trade_date VARCHAR NOT NULL,     -- 交易日期
            ts_code VARCHAR NOT NULL,        -- 股票代码
            name VARCHAR,                    -- 股票名称
            tenor INTEGER,                   -- 出借期限（天）
            fee_rate DOUBLE,                 -- 出借费率（%）
            lent_qnt DOUBLE,                 -- 出借数量（股）
            PRIMARY KEY (trade_date, ts_code)
        )""",
    'slb_len_mm': """
        CREATE TABLE slb_len_mm (
            trade_date VARCHAR NOT NULL,     -- 交易日期
            ts_code VARCHAR NOT NULL,        -- 股票代码
            name VARCHAR,                    -- 股票名称
            ope_inv DOUBLE,                  -- 期初余额（元）
            lent_qnt DOUBLE,                 -- 出借数量（股）
            cls_inv DOUBLE,                  -- 期末余额（元）
            end_bal DOUBLE,                  -- 期末余额（元）
            PRIMARY KEY (trade_date, ts_code)
        )""",

    # === fund 相关 ===
    'fund_basic': """
        CREATE TABLE fund_basic (
            ts_code VARCHAR PRIMARY KEY,
            name VARCHAR,
            management VARCHAR,
            custodian VARCHAR,
            fund_type VARCHAR,
            found_date VARCHAR,
            due_date VARCHAR,
            list_date VARCHAR,
            issue_date VARCHAR,
            delist_date VARCHAR,
            issue_amount DOUBLE,
            m_fee DOUBLE,
            c_fee DOUBLE,
            duration_year DOUBLE,
            p_value DOUBLE,
            min_amount DOUBLE,
            exp_return DOUBLE,
            benchmark VARCHAR,
            status VARCHAR,
            invest_type VARCHAR,
            type VARCHAR,
            trustee VARCHAR,
            purc_startdate VARCHAR,
            redm_startdate VARCHAR,
            market VARCHAR
        )""",
    'fund_company': """
        CREATE TABLE fund_company (
            ts_code VARCHAR PRIMARY KEY,
            name VARCHAR,
            shortname VARCHAR,
            province VARCHAR,
            address VARCHAR,
            phone VARCHAR,
            office VARCHAR,
            website VARCHAR,
            chairman VARCHAR,
            manager VARCHAR,
            reg_capital DOUBLE,
            setup_date VARCHAR,
            end_date VARCHAR,
            staff DOUBLE,
            email VARCHAR,
            main_business VARCHAR,
            PRIMARY KEY (ts_code)
        )""",
    'fund_nav': """
            CREATE TABLE fund_nav (
                ts_code VARCHAR,
                ann_date VARCHAR,
                nav_date VARCHAR,
                unit_nav DOUBLE,
                accum_nav DOUBLE,
                accum_div DOUBLE,
                net_asset DOUBLE,
                total_netasset DOUBLE,
                adj_nav DOUBLE,
                update_flag VARCHAR,
                PRIMARY KEY (ts_code, nav_date)
            )""",
    'fund_portfolio': """
        CREATE TABLE fund_portfolio (
            ts_code VARCHAR,
            ann_date VARCHAR,
            end_date VARCHAR,
            symbol VARCHAR,
            mkv DOUBLE,
            amount DOUBLE,
            stk_mkv_ratio DOUBLE,
            stk_float_ratio DOUBLE,
            PRIMARY KEY (ts_code, end_date, symbol)
        )""",
    'fund_daily': """
        CREATE TABLE fund_daily (
            ts_code VARCHAR,
            trade_date VARCHAR,
            pre_close DOUBLE,
            open DOUBLE,
            high DOUBLE,
            low DOUBLE,
            close DOUBLE,
            change DOUBLE,
            pct_chg DOUBLE,
            vol DOUBLE,
            amount DOUBLE,
            PRIMARY KEY (ts_code, trade_date)
        )""",
    'etf_basic': """
        CREATE TABLE etf_basic (
            ts_code VARCHAR PRIMARY KEY,       -- ETF代码
            csname VARCHAR,                    -- ETF简称（中文）
            extname VARCHAR,                   -- ETF扩展名称
            cname VARCHAR,                     -- ETF名称
            index_code VARCHAR,                -- 跟踪指数代码
            index_name VARCHAR,                -- 跟踪指数名称
            setup_date VARCHAR,                -- 成立日期
            list_date VARCHAR,                 -- 上市日期
            list_status VARCHAR,               -- 上市状态
            exchange VARCHAR,                  -- 交易所
            mgr_name VARCHAR,                  -- 管理人名称
            custod_name VARCHAR,               -- 托管人名称
            mgt_fee DOUBLE,                    -- 管理费率
            etf_type VARCHAR                   -- ETF类型
        )""",
    'etf_index': """
        CREATE TABLE etf_index (
            ts_code VARCHAR PRIMARY KEY,       -- ETF代码
            indx_name VARCHAR,                 -- 指数名称
            indx_csname VARCHAR,               -- 指数简称
            pub_party_name VARCHAR,            -- 发布机构
            pub_date VARCHAR,                  -- 发布日期
            base_date VARCHAR,                 -- 基期日期
            bp DOUBLE,                         -- 基点
            adj_circle VARCHAR                 -- 调整周期
        )""",
    'fund_adj': """
        CREATE TABLE fund_adj (
            ts_code VARCHAR NOT NULL,          -- 基金代码
            trade_date VARCHAR NOT NULL,       -- 交易日期
            adj_factor DOUBLE,                 -- 复权因子
            PRIMARY KEY (ts_code, trade_date)
        )""",
    'etf_share_size': """
        CREATE TABLE etf_share_size (
            trade_date VARCHAR NOT NULL,       -- 交易日期
            ts_code VARCHAR NOT NULL,          -- ETF代码
            etf_name VARCHAR,                  -- ETF名称
            total_share DOUBLE,                -- 总份额（万份）
            total_size DOUBLE,                 -- 总规模（亿元）
            nav DOUBLE,                        -- 单位净值
            close DOUBLE,                      -- 收盘价
            exchange VARCHAR,                  -- 交易所
            PRIMARY KEY (ts_code, trade_date)
        )""",

    # === marco 相关 ===
    'shibor': """
        CREATE TABLE shibor (
            date VARCHAR,
            "on" DOUBLE,
            "1w" DOUBLE,
            "2w" DOUBLE,
            "1m" DOUBLE,
            "3m" DOUBLE,
            "6m" DOUBLE,
            "9m" DOUBLE,
            "1y" DOUBLE,
            last_updated VARCHAR
        )""",
    'shibor_quote': """
        CREATE TABLE shibor_quote (
            date VARCHAR,
            bank VARCHAR,
            on_b DOUBLE,
            on_a DOUBLE,
            "1w_b" DOUBLE,
            "1w_a" DOUBLE,
            "2w_b" DOUBLE,
            "2w_a" DOUBLE,
            "1m_b" DOUBLE,
            "1m_a" DOUBLE,
            "3m_b" DOUBLE,
            "3m_a" DOUBLE,
            "6m_b" DOUBLE,
            "6m_a" DOUBLE,
            "9m_b" DOUBLE,
            "9m_a" DOUBLE,
            "1y_b" DOUBLE,
            "1y_a" DOUBLE,
            last_updated VARCHAR
        )""",
    'us_tycr': """
        CREATE TABLE us_tycr (
            date VARCHAR,
            m1 DOUBLE,
            m2 DOUBLE,
            m3 DOUBLE,
            m6 DOUBLE,
            y1 DOUBLE,
            y2 DOUBLE,
            y3 DOUBLE,
            y5 DOUBLE,
            y7 DOUBLE,
            y10 DOUBLE,
            y20 DOUBLE,
            y30 DOUBLE,
            last_updated VARCHAR
        )""",
    'us_trycr': """
        CREATE TABLE us_trycr (
            date VARCHAR,
            y5 DOUBLE,
            y7 DOUBLE,
            y10 DOUBLE,
            y20 DOUBLE,
            y30 DOUBLE,
            last_updated VARCHAR
        )""",
    'us_tltr': """
        CREATE TABLE us_tltr (
            date VARCHAR,
            ltc DOUBLE,
            cmt DOUBLE,
            e_factor VARCHAR,
            last_updated VARCHAR
        )""",
    'us_trltr': """
        CREATE TABLE us_trltr (
            date VARCHAR,
            ltr_avg DOUBLE,
            last_updated VARCHAR
        )""",
    'us_tbr': """
        CREATE TABLE us_tbr (
            date VARCHAR,
            w4_bd DOUBLE,
            w4_ce DOUBLE,
            w8_bd DOUBLE,
            w8_ce DOUBLE,
            w13_bd DOUBLE,
            w13_ce DOUBLE,
            w17_bd DOUBLE,
            w17_ce DOUBLE,
            w26_bd DOUBLE,
            w26_ce DOUBLE,
            w52_bd DOUBLE,
            w52_ce DOUBLE,
            last_updated VARCHAR
        )""",
    'cn_m': """
        CREATE TABLE cn_m (
            month VARCHAR PRIMARY KEY,
            m0 DOUBLE,
            m0_yoy DOUBLE,
            m0_mom DOUBLE,
            m1 DOUBLE,
            m1_yoy DOUBLE,
            m1_mom DOUBLE,
            m2 DOUBLE,
            m2_yoy DOUBLE,
            m2_mom DOUBLE
        )""",
    'cn_pmi': """
        CREATE TABLE cn_pmi (
            month VARCHAR PRIMARY KEY,     -- 月份 YYYYMM
            pmi010000 DOUBLE,              -- 制造业PMI
            pmi010100 DOUBLE,              -- 大型企业PMI
            pmi010200 DOUBLE,              -- 中型企业PMI
            pmi010300 DOUBLE,              -- 小型企业PMI
            pmi010400 DOUBLE,              -- 生产指数
            pmi010401 DOUBLE,
            pmi010402 DOUBLE,
            pmi010403 DOUBLE,
            pmi010500 DOUBLE,              -- 新订单指数
            pmi010501 DOUBLE,
            pmi010502 DOUBLE,
            pmi010503 DOUBLE,
            pmi010600 DOUBLE,              -- 新出口订单指数
            pmi010601 DOUBLE,
            pmi010602 DOUBLE,
            pmi010603 DOUBLE,
            pmi010700 DOUBLE,
            pmi010701 DOUBLE,
            pmi010702 DOUBLE,
            pmi010703 DOUBLE,
            pmi010800 DOUBLE,
            pmi010801 DOUBLE,
            pmi010802 DOUBLE,
            pmi010803 DOUBLE,
            pmi010900 DOUBLE,
            pmi010901 DOUBLE,
            pmi010902 DOUBLE,
            pmi010903 DOUBLE,
            pmi011000 DOUBLE,
            pmi011001 DOUBLE,
            pmi011002 DOUBLE,
            pmi011003 DOUBLE,
            pmi011100 DOUBLE,
            pmi011101 DOUBLE,
            pmi011102 DOUBLE,
            pmi011103 DOUBLE,
            pmi011200 DOUBLE,
            pmi011201 DOUBLE,
            pmi011202 DOUBLE,
            pmi011203 DOUBLE,
            pmi011300 DOUBLE,
            pmi011400 DOUBLE,
            pmi011500 DOUBLE,
            pmi011600 DOUBLE,
            pmi011700 DOUBLE,
            pmi011800 DOUBLE,
            pmi011900 DOUBLE,
            pmi012000 DOUBLE,
            pmi020100 DOUBLE,              -- 非制造业PMI
            pmi020101 DOUBLE,
            pmi020102 DOUBLE,
            pmi020200 DOUBLE,
            pmi020201 DOUBLE,
            pmi020202 DOUBLE,
            pmi020300 DOUBLE,
            pmi020301 DOUBLE,
            pmi020302 DOUBLE,
            pmi020400 DOUBLE,
            pmi020401 DOUBLE,
            pmi020402 DOUBLE,
            pmi020500 DOUBLE,
            pmi020501 DOUBLE,
            pmi020502 DOUBLE,
            pmi020600 DOUBLE,
            pmi020601 DOUBLE,
            pmi020602 DOUBLE,
            pmi020700 DOUBLE,
            pmi020800 DOUBLE,
            pmi020900 DOUBLE,
            pmi021000 DOUBLE,
            pmi030000 DOUBLE,              -- 综合PMI
            last_updated VARCHAR
        )""",
    'sf_month': """
        CREATE TABLE sf_month (
            month VARCHAR PRIMARY KEY,     -- 月份 YYYYMM
            inc_month DOUBLE,              -- 当月新增（亿元）
            inc_cumval DOUBLE,             -- 累计值（亿元）
            stk_endval DOUBLE,             -- 存量期末值（万亿元）
            last_updated VARCHAR
            )""",

    # === bond 相关 ===
    'cb_basic': """
        CREATE TABLE b_basic (
            ts_code VARCHAR,   -- 债券代码
            bond_full_name VARCHAR,        -- 债券全称
            bond_short_name VARCHAR,       -- 债券简称
            cb_code VARCHAR,               -- 可转债代码
            stk_code VARCHAR,              -- 股票代码
            stk_short_name VARCHAR,        -- 股票简称
            maturity DOUBLE,               -- 期限
            par DOUBLE,                    -- 面值
            issue_price DOUBLE,            -- 发行价格
            issue_size DOUBLE,             -- 发行规模
            remain_size DOUBLE,            -- 剩余规模
            value_date VARCHAR,            -- 起息日期
            maturity_date VARCHAR,         -- 到期日期
            rate_type VARCHAR,             -- 利率类型
            coupon_rate DOUBLE,            -- 票面利率
            add_rate DOUBLE,               -- 加息率
            pay_per_year INTEGER,          -- 每年支付次数
            list_date VARCHAR,             -- 上市日期
            delist_date VARCHAR,           -- 退市日期
            exchange VARCHAR,              -- 交易所
            conv_start_date VARCHAR,       -- 转股开始日期
            conv_end_date VARCHAR,         -- 转股结束日期
            conv_stop_date VARCHAR,        -- 转股暂停日期
            first_conv_price DOUBLE,       -- 首次转股价
            conv_price DOUBLE,             -- 当前转股价
            rate_clause VARCHAR,           -- 利率条款
            put_clause VARCHAR,            -- 赎回条款
            maturity_put_price DOUBLE,     -- 到期赎回价格
            call_clause VARCHAR,           -- 回售条款
            reset_clause VARCHAR,          -- 重置条款
            conv_clause VARCHAR,           -- 转股条款
            guarantor VARCHAR,             -- 担保人
            guarantee_type VARCHAR,        -- 担保类型
            issue_rating VARCHAR,          -- 发行评级
            newest_rating VARCHAR,         -- 最新评级
            rating_comp VARCHAR,            -- 评级公司
            last_updated TIMESTAMP, -- << 新增
            PRIMARY KEY (ts_code)
        )""",
    'cb_issue': """
        CREATE TABLE cb_issue (
            ts_code VARCHAR NOT NULL,           -- 转债代码
            ann_date VARCHAR NOT NULL,          -- 发行公告日
            res_ann_date VARCHAR,               -- 发行结果公告日
            plan_issue_size DOUBLE,             -- 计划发行总额（元）
            issue_size DOUBLE,                  -- 发行总额（元）
            issue_price DOUBLE,                 -- 发行价格
            issue_type VARCHAR,                 -- 发行方式
            issue_cost DOUBLE,                  -- 发行费用（元）
            onl_code VARCHAR,                   -- 网上申购代码
            onl_name VARCHAR,                   -- 网上申购简称
            onl_date VARCHAR,                   -- 网上发行日期
            onl_size DOUBLE,                    -- 网上发行总额（张）
            onl_pch_vol DOUBLE,                 -- 网上发行有效申购数量（张）
            onl_pch_num INTEGER,                -- 网上发行有效申购户数
            onl_pch_excess DOUBLE,              -- 网上发行超额认购倍数
            onl_winning_rate DOUBLE,            -- 网上发行中签率（%）
            shd_ration_code VARCHAR,            -- 老股东配售代码
            shd_ration_name VARCHAR,            -- 老股东配售简称
            shd_ration_date VARCHAR,            -- 老股东配售日
            shd_ration_record_date VARCHAR,     -- 老股东配售股权登记日
            shd_ration_pay_date VARCHAR,        -- 老股东配售缴款日
            shd_ration_price DOUBLE,            -- 老股东配售价格
            shd_ration_ratio DOUBLE,            -- 老股东配售比例
            shd_ration_size DOUBLE,             -- 老股东配售数量（张）
            shd_ration_vol DOUBLE,              -- 老股东配售有效申购数量（张）
            shd_ration_num INTEGER,             -- 老股东配售有效申购户数
            shd_ration_excess DOUBLE,           -- 老股东配售超额认购倍数
            offl_size DOUBLE,                   -- 网下发行总额（张）
            offl_deposit DOUBLE,                -- 网下发行定金比例（%）
            offl_pch_vol DOUBLE,                -- 网下发行有效申购数量（张）
            offl_pch_num INTEGER,               -- 网下发行有效申购户数
            offl_pch_excess DOUBLE,             -- 网下发行超额认购倍数
            offl_winning_rate DOUBLE,           -- 网下发行中签率
            lead_underwriter VARCHAR,           -- 主承销商
            lead_underwriter_vol DOUBLE,        -- 主承销商包销数量（张）
            last_updated TIMESTAMP, -- << 新增
            PRIMARY KEY (ts_code, ann_date)
            )""",
    'cb_rate': """
        CREATE TABLE cb_rate (
        ts_code VARCHAR,                   -- 转债代码
        rate_freq INTEGER,                 -- 利率频率
        rate_start_date VARCHAR,           -- 利率开始日期
        rate_end_date VARCHAR,             -- 利率结束日期
        coupon_rate DOUBLE,                -- 票面利率
        last_updated TIMESTAMP, -- << 新增
        PRIMARY KEY (ts_code, rate_start_date)
        )""",
    'cb_share': """
        CREATE TABLE cb_share (
        ts_code VARCHAR,                   -- 债券代码
        bond_short_name VARCHAR,           -- 债券简称
        publish_date VARCHAR,              -- 公告日期
        end_date VARCHAR,                  -- 统计截止日期
        issue_size DOUBLE,                 -- 可转债发行总额
        convert_price_initial DOUBLE,      -- 初始转换价格
        convert_price DOUBLE,              -- 本次转换价格
        convert_val DOUBLE,                -- 本次转股金额
        convert_vol DOUBLE,                -- 本次转股数量
        convert_ratio DOUBLE,              -- 本次转股比例
        acc_convert_val DOUBLE,            -- 累计转股金额
        acc_convert_vol DOUBLE,            -- 累计转股数量
        acc_convert_ratio DOUBLE,          -- 累计转股比例
        remain_size DOUBLE,                -- 可转债剩余金额
        total_shares DOUBLE,               -- 转股后总股本
        last_updated TIMESTAMP,            -- 最后更新时间
        PRIMARY KEY (ts_code, publish_date, end_date)
        )""",
    'cb_call': """
        CREATE TABLE cb_call (
            ts_code VARCHAR NOT NULL,          -- 转债代码
            call_type VARCHAR,                 -- 赎回类型
            is_call VARCHAR,                   -- 是否赎回
            ann_date VARCHAR NOT NULL,         -- 公告/提示日期
            call_date VARCHAR,                 -- 赎回日期
            call_price DOUBLE,                 -- 赎回价格(含税)
            call_price_tax DOUBLE,             -- 赎回价格(扣税)
            call_vol DOUBLE,                   -- 赎回债券数量
            call_amount DOUBLE,                -- 赎回金额
            payment_date VARCHAR,              -- 款项到账日
            call_reg_date VARCHAR,             -- 赎回登记日
            last_updated TIMESTAMP, -- << 新增
            PRIMARY KEY (ts_code, ann_date)
        )""",
    'cb_daily': """
        CREATE TABLE cb_daily (
            ts_code VARCHAR NOT NULL,          -- 转债代码
            trade_date VARCHAR NOT NULL,       -- 交易日期
            pre_close DOUBLE,                  -- 昨收盘价
            open DOUBLE,                       -- 开盘价
            high DOUBLE,                       -- 最高价
            low DOUBLE,                        -- 最低价
            close DOUBLE,                      -- 收盘价
            change DOUBLE,                     -- 涨跌
            pct_chg DOUBLE,                    -- 涨跌幅
            vol DOUBLE,                        -- 成交量
            amount DOUBLE,                     -- 成交金额
            bond_value DOUBLE,                 -- 纯债价值
            bond_over_rate DOUBLE,             -- 纯债溢价率
            cb_value DOUBLE,                   -- 转股价值
            cb_over_rate DOUBLE,               -- 转股溢价率
            PRIMARY KEY (ts_code, trade_date)
        )""",
    'repo_daily': """
        CREATE TABLE repo_daily (
            ts_code VARCHAR NOT NULL,          -- TS代码
            trade_date VARCHAR NOT NULL,       -- 交易日期
            repo_maturity VARCHAR,             -- 期限品种
            pre_close DOUBLE,                  -- 前收盘
            open DOUBLE,                       -- 开盘价
            high DOUBLE,                       -- 最高价
            low DOUBLE,                        -- 最低价
            close DOUBLE,                      -- 收盘价
            weight DOUBLE,                     -- 加权价
            weight_r DOUBLE,                   -- 加权价(利率债)
            amount DOUBLE,                     -- 成交金额
            num INTEGER,                       -- 成交笔数
            PRIMARY KEY (ts_code, trade_date)
        )""",
    'bond_blk': """
        CREATE TABLE bond_blk (
            trade_date VARCHAR NOT NULL,       -- 交易日期
            ts_code VARCHAR NOT NULL,          -- 债券代码
            name VARCHAR,                      -- 债券名称
            price DOUBLE,                      -- 成交价
            vol DOUBLE,                        -- 累计成交数量
            amount DOUBLE,                     -- 累计成交金额
            PRIMARY KEY (ts_code, trade_date) -- 注意：原定义中主键是 (ts_code, trade_date)，这里保持一致
        )""",
    'bond_blk_detail': """
        CREATE TABLE bond_blk_detail (
            trade_date VARCHAR NOT NULL,       -- 交易日期
            ts_code VARCHAR NOT NULL,          -- 债券代码
            name VARCHAR,                      -- 债券名称
            price DOUBLE,                      -- 成交价
            vol DOUBLE,                        -- 成交数量
            amount DOUBLE,                     -- 成交金额
            buy_dp VARCHAR,                    -- 买方营业部
            sell_dp VARCHAR,                   -- 卖方营业部
            PRIMARY KEY (ts_code, trade_date)  -- 假设 (ts_code, trade_date) 唯一，否则调整
        )""",
    'yc_cb': """
        CREATE TABLE yc_cb (
            trade_date VARCHAR NOT NULL,       -- 交易日期
            ts_code VARCHAR NOT NULL,          -- 债券代码
            curve_name VARCHAR,                -- 曲线名称
            curve_type VARCHAR NOT NULL,       -- 曲线类型
            curve_term DOUBLE NOT NULL,        -- 曲线期限
            yield DOUBLE,                      -- 收益率
            PRIMARY KEY (trade_date, ts_code, curve_term, curve_type)
        )""",

    # === future 相关 ===
    'fut_basic': """
        CREATE TABLE fut_basic (
            ts_code VARCHAR, 
            symbol VARCHAR, 
            exchange VARCHAR,
            name VARCHAR, 
            fut_code VARCHAR, 
            multiplier DOUBLE, 
            trade_unit VARCHAR,
            per_unit DOUBLE, 
            quote_unit VARCHAR, 
            quote_unit_desc VARCHAR,
            d_mode_desc VARCHAR, 
            list_date VARCHAR, 
            delist_date VARCHAR,
            d_month VARCHAR, 
            last_ddate VARCHAR, 
            trade_time_desc VARCHAR,
            last_updated TIMESTAMP,
            PRIMARY KEY (ts_code)
        )""",
    'trade_cal_future': """
        CREATE TABLE trade_cal_future (
            exchange VARCHAR NOT NULL, 
            cal_date VARCHAR NOT NULL, 
            is_open INTEGER,
            pretrade_date VARCHAR, 
            last_updated TIMESTAMP,
            PRIMARY KEY (exchange, cal_date)
        )""",
    'fut_daily': """
        CREATE TABLE fut_daily (
            ts_code VARCHAR NOT NULL,      -- TS合约代码
            trade_date VARCHAR NOT NULL,   -- 交易日期
            pre_close DOUBLE,              -- 昨收盘价
            pre_settle DOUBLE,             -- 昨结算价
            open DOUBLE,                   -- 开盘价
            high DOUBLE,                   -- 最高价
            low DOUBLE,                    -- 最低价
            close DOUBLE,                  -- 收盘价
            settle DOUBLE,                 -- 结算价
            change1 DOUBLE,                -- 涨跌1(收盘价-昨结算价)
            change2 DOUBLE,                -- 涨跌2(结算价-昨结算价)
            vol DOUBLE,                    -- 成交量(手)
            amount DOUBLE,                 -- 成交金额(万元)
            oi DOUBLE,                     -- 持仓量(手)
            oi_chg DOUBLE,                 -- 持仓量变化
            delv_settle DOUBLE,            -- 交割结算价
            PRIMARY KEY (ts_code, trade_date) -- 联合主键
        )""",
    'fut_wsr': """
        CREATE TABLE fut_wsr (
            trade_date VARCHAR,
            symbol VARCHAR,
            fut_name VARCHAR,
            warehouse VARCHAR,
            wh_id VARCHAR,
            pre_vol INTEGER,
            vol INTEGER,
            vol_chg INTEGER,
            area VARCHAR,
            year VARCHAR,
            grade VARCHAR,
            brand VARCHAR,
            place VARCHAR,
            pd INTEGER,
            is_ct VARCHAR,
            unit VARCHAR,
            exchange VARCHAR,
            PRIMARY KEY (trade_date, symbol, fut_name, warehouse)
        )""",
    'fut_settle': """
        CREATE TABLE fut_settle (
            ts_code VARCHAR,
            trade_date VARCHAR,
            settle DOUBLE,
            trading_fee_rate DOUBLE,
            trading_fee DOUBLE,
            delivery_fee DOUBLE,
            b_hedging_margin_rate DOUBLE,
            s_hedging_margin_rate DOUBLE,
            long_margin_rate DOUBLE,
            short_margin_rate DOUBLE,
            offset_today_fee DOUBLE,
            exchange VARCHAR,
            PRIMARY KEY (ts_code, trade_date)
        )""",
    'fut_holding': """
        CREATE TABLE fut_holding (
            trade_date VARCHAR,
            symbol VARCHAR,
            broker VARCHAR,
            vol INTEGER,
            vol_chg INTEGER,
            long_hld INTEGER,
            long_chg INTEGER,
            short_hld INTEGER,
            short_chg INTEGER,
            exchange VARCHAR,
            PRIMARY KEY (trade_date, symbol, broker)
        )""",
    'fut_index_daily': """
        CREATE TABLE fut_index_daily (
            ts_code VARCHAR,
            trade_date VARCHAR,
            close DOUBLE,
            open DOUBLE,
            high DOUBLE,
            low DOUBLE,
            pre_close DOUBLE,
            change DOUBLE,
            pct_chg DOUBLE,
            vol DOUBLE,
            amount DOUBLE,
            PRIMARY KEY (ts_code, trade_date)
        )""",

    # === 其他表（可继续扩展）===
    'income': '''
              CREATE TABLE income
              (
                  ts_code     VARCHAR NOT NULL,     -- TS代码
                  ann_date    VARCHAR NOT NULL,     -- 公告日期
                  f_ann_date  VARCHAR,              -- 实际公告日期
                  end_date    VARCHAR NOT NULL,     -- 报告期
                  report_type VARCHAR,              -- 报告类型
                  comp_type   VARCHAR,              -- 公司类型(1一般工商业2银行3保险4证券)
                  end_type    VARCHAR,              -- 报告期类型
                  basic_eps DOUBLE,                 -- 基本每股收益
                  diluted_eps DOUBLE,               -- 稀释每股收益
                  total_revenue DOUBLE,             -- 营业总收入
                  revenue DOUBLE,                   -- 营业收入
                  int_income DOUBLE,                -- 利息收入
                  prem_earned DOUBLE,               -- 已赚保费
                  comm_income DOUBLE,               -- 手续费及佣金收入
                  n_commis_income DOUBLE,           -- 手续费及佣金净收入
                  n_oth_income DOUBLE,              -- 其他经营净收益
                  n_oth_b_income DOUBLE,            -- 加:其他业务净收益
                  prem_income DOUBLE,               -- 保险业务收入
                  out_prem DOUBLE,                  -- 减:分出保费
                  une_prem_reser DOUBLE,            -- 提取未到期责任准备金
                  reins_income DOUBLE,              -- 其中:分保费收入
                  n_sec_tb_income DOUBLE,           -- 代理买卖证券业务净收入
                  n_sec_uw_income DOUBLE,           -- 证券承销业务净收入
                  n_asset_mg_income DOUBLE,         -- 受托客户资产管理业务净收入
                  oth_b_income DOUBLE,              -- 其他业务收入
                  fv_value_chg_gain DOUBLE,         -- 加:公允价值变动净收益
                  invest_income DOUBLE,             -- 加:投资净收益
                  ass_invest_income DOUBLE,         -- 其中:对联营企业和合营企业的投资收益
                  forex_gain DOUBLE,                -- 加:汇兑净收益
                  total_cogs DOUBLE,                -- 营业总成本
                  oper_cost DOUBLE,                 -- 减:营业成本
                  int_exp DOUBLE,                   -- 减:利息支出
                  comm_exp DOUBLE,                  -- 减:手续费及佣金支出
                  biz_tax_surchg DOUBLE,            -- 减:营业税金及附加
                  sell_exp DOUBLE,                  -- 减:销售费用
                  admin_exp DOUBLE,                 -- 减:管理费用
                  fin_exp DOUBLE,                   -- 减:财务费用
                  assets_impair_loss DOUBLE,        -- 减:资产减值损失
                  prem_refund DOUBLE,               -- 退保金
                  compens_payout DOUBLE,            -- 赔付总支出
                  reser_insur_liab DOUBLE,          -- 提取保险责任准备金
                  div_payt DOUBLE,                  -- 保户红利支出
                  reins_exp DOUBLE,                 -- 分保费用
                  oper_exp DOUBLE,                  -- 营业支出
                  compens_payout_refu DOUBLE,       -- 减:摊回赔付支出
                  insur_reser_refu DOUBLE,          -- 减:摊回保险责任准备金
                  reins_cost_refund DOUBLE,         -- 减:摊回分保费用
                  other_bus_cost DOUBLE,            -- 其他业务成本
                  operate_profit DOUBLE,            -- 营业利润
                  non_oper_income DOUBLE,           -- 加:营业外收入
                  non_oper_exp DOUBLE,              -- 减:营业外支出
                  nca_disploss DOUBLE,              -- 其中:减:非流动资产处置净损失
                  total_profit DOUBLE,              -- 利润总额
                  income_tax DOUBLE,                -- 所得税费用
                  n_income DOUBLE,                  -- 净利润(含少数股东损益)
                  n_income_attr_p DOUBLE,           -- 净利润(不含少数股东损益)
                  minority_gain DOUBLE,             -- 少数股东损益
                  oth_compr_income DOUBLE,          -- 其他综合收益
                  t_compr_income DOUBLE,            -- 综合收益总额
                  compr_inc_attr_p DOUBLE,          -- 归属于母公司(或股东)的综合收益总额
                  compr_inc_attr_m_s DOUBLE,        -- 归属于少数股东的综合收益总额
                  ebit DOUBLE,                      -- 息税前利润
                  ebitda DOUBLE,                    -- 息税折旧摊销前利润
                  insurance_exp DOUBLE,             -- 保险业务支出
                  undist_profit DOUBLE,             -- 年初未分配利润
                  distable_profit DOUBLE,           -- 可分配利润
                  rd_exp DOUBLE,                    -- 研发费用
                  fin_exp_int_exp DOUBLE,           -- 财务费用:利息费用
                  fin_exp_int_inc DOUBLE,           -- 财务费用:利息收入
                  transfer_surplus_rese DOUBLE,     -- 盈余公积转入
                  transfer_housing_imprest DOUBLE,  -- 住房周转金转入
                  transfer_oth DOUBLE,              -- 其他转入
                  adj_lossgain DOUBLE,              -- 调整以前年度损益
                  withdra_legal_surplus DOUBLE,     -- 提取法定盈余公积
                  withdra_legal_pubfund DOUBLE,     -- 提取法定公益金
                  withdra_biz_devfund DOUBLE,       -- 提取企业发展基金
                  withdra_rese_fund DOUBLE,         -- 提取储备基金
                  withdra_oth_ersu DOUBLE,          -- 提取任意盈余公积金
                  workers_welfare DOUBLE,           -- 职工奖金福利
                  distr_profit_shrhder DOUBLE,      -- 可供股东分配的利润
                  prfshare_payable_dvd DOUBLE,      -- 应付优先股股利
                  comshare_payable_dvd DOUBLE,      -- 应付普通股股利
                  capit_comstock_div DOUBLE,        -- 转作股本的普通股股利
                  net_after_nr_lp_correct DOUBLE,   -- 扣除非经常性损益后的净利润（更正前）
                  credit_impa_loss DOUBLE,          -- 信用减值损失
                  net_expo_hedging_benefits DOUBLE, -- 净敞口套期收益
                  oth_impair_loss_assets DOUBLE,    -- 其他资产减值损失
                  total_opcost DOUBLE,              -- 营业总成本（二）
                  amodcost_fin_assets DOUBLE,       -- 以摊余成本计量的金融资产终止确认收益
                  oth_income DOUBLE,                -- 其他收益
                  asset_disp_income DOUBLE,         -- 资产处置收益
                  continued_net_profit DOUBLE,      -- 持续经营净利润
                  end_net_profit DOUBLE,            -- 终止经营净利润
                  update_flag VARCHAR DEFAULT '0',  -- 更新标识 (1 表示更新)
                  PRIMARY KEY (ts_code, end_date, ann_date, update_flag)
              )
              ''',
    'balance': '''
               CREATE TABLE balance 
        (
        ts_code VARCHAR NOT NULL,               -- TS股票代码
        ann_date VARCHAR NOT NULL,              -- 公告日期
        f_ann_date VARCHAR,                     -- 实际公告日期
        end_date VARCHAR NOT NULL,              -- 报告期
        report_type VARCHAR,                    -- 报表类型
        comp_type VARCHAR,                      -- 公司类型(1一般工商业2银行3保险4证券)
        end_type VARCHAR,                       -- 报告期类型
        total_share DOUBLE,                     -- 期末总股本
        cap_rese DOUBLE,                        -- 资本公积金
        undistr_porfit DOUBLE,                  -- 未分配利润
        surplus_rese DOUBLE,                    -- 盈余公积金
        special_rese DOUBLE,                    -- 专项储备
        money_cap DOUBLE,                       -- 货币资金
        trad_asset DOUBLE,                      -- 交易性金融资产
        notes_receiv DOUBLE,                    -- 应收票据
        accounts_receiv DOUBLE,                 -- 应收账款
        oth_receiv DOUBLE,                      -- 其他应收款
        prepayment DOUBLE,                      -- 预付款项
        div_receiv DOUBLE,                      -- 应收股利
        int_receiv DOUBLE,                      -- 应收利息
        inventories DOUBLE,                     -- 存货
        amor_exp DOUBLE,                        -- 待摊费用
        nca_within_1y DOUBLE,                   -- 一年内到期的非流动资产
        sett_rsrv DOUBLE,                       -- 结算备付金
        loanto_oth_bank_fi DOUBLE,              -- 拆出资金
        premium_receiv DOUBLE,                  -- 应收保费
        reinsur_receiv DOUBLE,                  -- 应收分保账款
        reinsur_res_receiv DOUBLE,              -- 应收分保合同准备金
        pur_resale_fa DOUBLE,                   -- 买入返售金融资产
        oth_cur_assets DOUBLE,                  -- 其他流动资产
        total_cur_assets DOUBLE,                -- 流动资产合计
        fa_avail_for_sale DOUBLE,               -- 可供出售金融资产
        htm_invest DOUBLE,                      -- 持有至到期投资
        lt_eqt_invest DOUBLE,                   -- 长期股权投资
        invest_real_estate DOUBLE,              -- 投资性房地产
        time_deposits DOUBLE,                   -- 定期存款
        oth_assets DOUBLE,                      -- 其他资产
        lt_rec DOUBLE,                          -- 长期应收款
        fix_assets DOUBLE,                      -- 固定资产
        cip DOUBLE,                             -- 在建工程
        const_materials DOUBLE,                 -- 工程物资
        fixed_assets_disp DOUBLE,               -- 固定资产清理
        produc_bio_assets DOUBLE,               -- 生产性生物资产
        oil_and_gas_assets DOUBLE,              -- 油气资产
        intan_assets DOUBLE,                    -- 无形资产
        r_and_d DOUBLE,                         -- 研发支出
        goodwill DOUBLE,                        -- 商誉
        lt_amor_exp DOUBLE,                     -- 长期待摊费用
        defer_tax_assets DOUBLE,                -- 递延所得税资产
        decr_in_disbur DOUBLE,                  -- 发放贷款及垫款
        oth_nca DOUBLE,                         -- 其他非流动资产
        total_nca DOUBLE,                       -- 非流动资产合计
        cash_reser_cb DOUBLE,                   -- 现金及存放中央银行款项
        depos_in_oth_bfi DOUBLE,                -- 存放同业和其它金融机构款项
        prec_metals DOUBLE,                     -- 贵金属
        deriv_assets DOUBLE,                    -- 衍生金融资产
        rr_reins_une_prem DOUBLE,               -- 应收分保未到期责任准备金
        rr_reins_outstd_cla DOUBLE,             -- 应收分保未决赔款准备金
        rr_reins_lins_liab DOUBLE,              -- 应收分保寿险责任准备金
        rr_reins_lthins_liab DOUBLE,            -- 应收分保长期健康险责任准备金
        refund_depos DOUBLE,                    -- 存出保证金
        ph_pledge_loans DOUBLE,                 -- 保户质押贷款
        refund_cap_depos DOUBLE,                -- 存出资本保证金
        indep_acct_assets DOUBLE,               -- 独立账户资产
        client_depos DOUBLE,                    -- 其中：客户资金存款
        client_prov DOUBLE,                     -- 其中：客户备付金
        transac_seat_fee DOUBLE,                -- 其中:交易席位费
        invest_as_receiv DOUBLE,                -- 应收款项类投资
        total_assets DOUBLE,                    -- 资产总计
        lt_borr DOUBLE,                         -- 长期借款
        st_borr DOUBLE,                         -- 短期借款
        cb_borr DOUBLE,                         -- 向中央银行借款
        depos_ib_deposits DOUBLE,               -- 吸收存款及同业存放
        loan_oth_bank DOUBLE,                   -- 拆入资金
        trading_fl DOUBLE,                      -- 交易性金融负债
        notes_payable DOUBLE,                   -- 应付票据
        acct_payable DOUBLE,                    -- 应付账款
        adv_receipts DOUBLE,                    -- 预收款项
        sold_for_repur_fa DOUBLE,               -- 卖出回购金融资产款
        comm_payable DOUBLE,                    -- 应付手续费及佣金
        payroll_payable DOUBLE,                 -- 应付职工薪酬
        taxes_payable DOUBLE,                   -- 应交税费
        int_payable DOUBLE,                     -- 应付利息
        div_payable DOUBLE,                     -- 应付股利
        oth_payable DOUBLE,                     -- 其他应付款
        acc_exp DOUBLE,                         -- 预提费用
        deferred_inc DOUBLE,                    -- 递延收益
        st_bonds_payable DOUBLE,                -- 应付短期债券
        payable_to_reinsurer DOUBLE,            -- 应付分保账款
        rsrv_insur_cont DOUBLE,                 -- 保险合同准备金
        acting_trading_sec DOUBLE,              -- 代理买卖证券款
        acting_uw_sec DOUBLE,                   -- 代理承销证券款
        non_cur_liab_due_1y DOUBLE,             -- 一年内到期的非流动负债
        oth_cur_liab DOUBLE,                    -- 其他流动负债
        total_cur_liab DOUBLE,                  -- 流动负债合计
        bond_payable DOUBLE,                    -- 应付债券
        lt_payable DOUBLE,                      -- 长期应付款
        specific_payables DOUBLE,               -- 专项应付款
        estimated_liab DOUBLE,                  -- 预计负债
        defer_tax_liab DOUBLE,                  -- 递延所得税负债
        defer_inc_non_cur_liab DOUBLE,          -- 递延收益-非流动负债
        oth_ncl DOUBLE,                         -- 其他非流动负债
        total_ncl DOUBLE,                       -- 非流动负债合计
        depos_oth_bfi DOUBLE,                   -- 同业和其它金融机构存放款项
        deriv_liab DOUBLE,                      -- 衍生金融负债
        depos DOUBLE,                           -- 吸收存款
        agency_bus_liab DOUBLE,                 -- 代理业务负债
        oth_liab DOUBLE,                        -- 其他负债
        prem_receiv_adva DOUBLE,                -- 预收保费
        depos_received DOUBLE,                  -- 存入保证金
        ph_invest DOUBLE,                       -- 保户储金及投资款
        reser_une_prem DOUBLE,                  -- 未到期责任准备金
        reser_outstd_claims DOUBLE,             -- 未决赔款准备金
        reser_lins_liab DOUBLE,                 -- 寿险责任准备金
        reser_lthins_liab DOUBLE,               -- 长期健康险责任准备金
        indept_acc_liab DOUBLE,                 -- 独立账户负债
        pledge_borr DOUBLE,                     -- 其中:质押借款
        indem_payable DOUBLE,                   -- 应付赔付款
        policy_div_payable DOUBLE,              -- 应付保单红利
        total_liab DOUBLE,                      -- 负债合计
        treasury_share DOUBLE,                  -- 减:库存股
        ordin_risk_reser DOUBLE,                -- 一般风险准备
        forex_differ DOUBLE,                    -- 外币报表折算差额
        invest_loss_unconf DOUBLE,              -- 未确认的投资损失
        minority_int DOUBLE,                    -- 少数股东权益
        total_hldr_eqy_exc_min_int DOUBLE,      -- 股东权益合计(不含少数股东权益)
        total_hldr_eqy_inc_min_int DOUBLE,      -- 股东权益合计(含少数股东权益)
        total_liab_hldr_eqy DOUBLE,             -- 负债及股东权益总计
        lt_payroll_payable DOUBLE,              -- 长期应付职工薪酬
        oth_comp_income DOUBLE,                 -- 其他综合收益
        oth_eqt_tools DOUBLE,                   -- 其他权益工具
        oth_eqt_tools_p_shr DOUBLE,             -- 其他权益工具(优先股)
        lending_funds DOUBLE,                   -- 融出资金
        acc_receivable DOUBLE,                  -- 应收款项
        st_fin_payable DOUBLE,                  -- 应付短期融资款
        payables DOUBLE,                        -- 应付款项
        hfs_assets DOUBLE,                      -- 持有待售的资产
        hfs_sales DOUBLE,                       -- 持有待售的负债
        cost_fin_assets DOUBLE,                 -- 以摊余成本计量的金融资产
        fair_value_fin_assets DOUBLE,           -- 以公允价值计量且其变动计入其他综合收益的金融资产
        cip_total DOUBLE,                       -- 在建工程(合计)(元)
        oth_pay_total DOUBLE,                   -- 其他应付款(合计)(元)
        long_pay_total DOUBLE,                  -- 长期应付款(合计)(元)
        debt_invest DOUBLE,                     -- 债权投资(元)
        oth_debt_invest DOUBLE,                 -- 其他债权投资(元)
        oth_eq_invest DOUBLE,                   -- 其他权益工具投资(元)
        oth_illiq_fin_assets DOUBLE,            -- 其他非流动金融资产(元)
        oth_eq_ppbond DOUBLE,                   -- 其他权益工具:永续债(元)
        receiv_financing DOUBLE,                -- 应收款项融资
        use_right_assets DOUBLE,                -- 使用权资产
        lease_liab DOUBLE,                      -- 租赁负债
        contract_assets DOUBLE,                 -- 合同资产
        contract_liab DOUBLE,                   -- 合同负债
        accounts_receiv_bill DOUBLE,            -- 应收票据及应收账款
        accounts_pay DOUBLE,                    -- 应付票据及应付账款
        oth_rcv_total DOUBLE,                   -- 其他应收款(合计)(元)
        fix_assets_total DOUBLE,                -- 固定资产(合计)(元)
        update_flag VARCHAR DEFAULT '0',        -- 更新标识
        PRIMARY KEY (ts_code, end_date, ann_date, update_flag)
        )
        ''',
    'cashflow': '''
                CREATE TABLE cashflow
                (
                    ts_code     VARCHAR NOT NULL,       -- TS股票代码
                    ann_date    VARCHAR NOT NULL,       -- 公告日期
                    f_ann_date  VARCHAR,                -- 实际公告日期
                    end_date    VARCHAR NOT NULL,       -- 报告期
                    comp_type   VARCHAR,                -- 公司类型(1一般工商业2银行3保险4证券)
                    report_type VARCHAR,                -- 报表类型
                    end_type    VARCHAR,                -- 报告期类型
                    net_profit DOUBLE,                  -- 净利润
                    finan_exp DOUBLE,                   -- 财务费用
                    c_fr_sale_sg DOUBLE,                -- 销售商品、提供劳务收到的现金
                    recp_tax_rends DOUBLE,              -- 收到的税费返还
                    n_depos_incr_fi DOUBLE,             -- 客户存款和同业存放款项净增加额
                    n_incr_loans_cb DOUBLE,             -- 向中央银行借款净增加额
                    n_inc_borr_oth_fi DOUBLE,           -- 向其他金融机构拆入资金净增加额
                    prem_fr_orig_contr DOUBLE,          -- 收到原保险合同保费取得的现金
                    n_incr_insured_dep DOUBLE,          -- 保户储金净增加额
                    n_reinsur_prem DOUBLE,              -- 收到再保业务现金净额
                    n_incr_disp_tfa DOUBLE,             -- 处置交易性金融资产净增加额
                    ifc_cash_incr DOUBLE,               -- 收取利息和手续费净增加额
                    n_incr_disp_faas DOUBLE,            -- 处置可供出售金融资产净增加额
                    n_incr_loans_oth_bank DOUBLE,       -- 拆入资金净增加额
                    n_cap_incr_repur DOUBLE,            -- 回购业务资金净增加额
                    c_fr_oth_operate_a DOUBLE,          -- 收到其他与经营活动有关的现金
                    c_inf_fr_operate_a DOUBLE,          -- 经营活动现金流入小计
                    c_paid_goods_s DOUBLE,              -- 购买商品、接受劳务支付的现金
                    c_paid_to_for_empl DOUBLE,          -- 支付给职工以及为职工支付的现金
                    c_paid_for_taxes DOUBLE,            -- 支付的各项税费
                    n_incr_clt_loan_adv DOUBLE,         -- 客户贷款及垫款净增加额
                    n_incr_dep_cbob DOUBLE,             -- 存放央行和同业款项净增加额
                    c_pay_claims_orig_inco DOUBLE,      -- 支付原保险合同赔付款项的现金
                    pay_handling_chrg DOUBLE,           -- 支付手续费的现金
                    pay_comm_insur_plcy DOUBLE,         -- 支付保单红利的现金
                    oth_cash_pay_oper_act DOUBLE,       -- 支付其他与经营活动有关的现金
                    st_cash_out_act DOUBLE,             -- 经营活动现金流出小计
                    n_cashflow_act DOUBLE,              -- 经营活动产生的现金流量净额
                    oth_recp_ral_inv_act DOUBLE,        -- 收到其他与投资活动有关的现金
                    c_disp_withdrwl_invest DOUBLE,      -- 收回投资收到的现金
                    c_recp_return_invest DOUBLE,        -- 取得投资收益收到的现金
                    n_recp_disp_fiolta DOUBLE,          -- 处置固定资产、无形资产和其他长期资产收回的现金净额
                    n_recp_disp_sobu DOUBLE,            -- 处置子公司及其他营业单位收到的现金净额
                    stot_inflows_inv_act DOUBLE,        -- 投资活动现金流入小计
                    c_pay_acq_const_fiolta DOUBLE,      -- 购建固定资产、无形资产和其他长期资产支付的现金
                    c_paid_invest DOUBLE,               -- 投资支付的现金
                    n_disp_subs_oth_biz DOUBLE,         -- 取得子公司及其他营业单位支付的现金净额
                    oth_pay_ral_inv_act DOUBLE,         -- 支付其他与投资活动有关的现金
                    n_incr_pledge_loan DOUBLE,          -- 质押贷款净增加额
                    stot_out_inv_act DOUBLE,            -- 投资活动现金流出小计
                    n_cashflow_inv_act DOUBLE,          -- 投资活动产生的现金流量净额
                    c_recp_borrow DOUBLE,               -- 取得借款收到的现金
                    proc_issue_bonds DOUBLE,            -- 发行债券收到的现金
                    oth_cash_recp_ral_fnc_act DOUBLE,   -- 收到其他与筹资活动有关的现金
                    stot_cash_in_fnc_act DOUBLE,        -- 筹资活动现金流入小计
                    free_cashflow DOUBLE,               -- 企业自由现金流量
                    c_prepay_amt_borr DOUBLE,           -- 偿还债务支付的现金
                    c_pay_dist_dpcp_int_exp DOUBLE,     -- 分配股利、利润或偿付利息支付的现金
                    incl_dvd_profit_paid_sc_ms DOUBLE,  -- 其中:子公司支付给少数股东的股利、利润
                    oth_cashpay_ral_fnc_act DOUBLE,     -- 支付其他与筹资活动有关的现金
                    stot_cashout_fnc_act DOUBLE,        -- 筹资活动现金流出小计
                    n_cash_flows_fnc_act DOUBLE,        -- 筹资活动产生的现金流量净额
                    eff_fx_flu_cash DOUBLE,             -- 汇率变动对现金的影响
                    n_incr_cash_cash_equ DOUBLE,        -- 现金及现金等价物净增加额
                    c_cash_equ_beg_period DOUBLE,       -- 期初现金及现金等价物余额
                    c_cash_equ_end_period DOUBLE,       -- 期末现金及现金等价物余额
                    c_recp_cap_contrib DOUBLE,          -- 吸收投资收到的现金
                    incl_cash_rec_saims DOUBLE,         -- 其中:子公司吸收少数股东投资收到的现金
                    uncon_invest_loss DOUBLE,           -- 未确认投资损失
                    prov_depr_assets DOUBLE,            -- 加:资产减值准备
                    depr_fa_coga_dpba DOUBLE,           -- 固定资产折旧、油气资产折耗、生产性生物资产折旧
                    amort_intang_assets DOUBLE,         -- 无形资产摊销
                    lt_amort_deferred_exp DOUBLE,       -- 长期待摊费用摊销
                    decr_deferred_exp DOUBLE,           -- 待摊费用减少
                    incr_acc_exp DOUBLE,                -- 预提费用增加
                    loss_disp_fiolta DOUBLE,            -- 处置固定、无形资产和其他长期资产的损失
                    loss_scr_fa DOUBLE,                 -- 固定资产报废损失
                    loss_fv_chg DOUBLE,                 -- 公允价值变动损失
                    invest_loss DOUBLE,                 -- 投资损失
                    decr_def_inc_tax_assets DOUBLE,     -- 递延所得税资产减少
                    incr_def_inc_tax_liab DOUBLE,       -- 递延所得税负债增加
                    decr_inventories DOUBLE,            -- 存货的减少
                    decr_oper_payable DOUBLE,           -- 经营性应收项目的减少
                    incr_oper_payable DOUBLE,           -- 经营性应付项目的增加
                    others DOUBLE,                      -- 其他
                    im_net_cashflow_oper_act DOUBLE,    -- 经营活动产生的现金流量净额(间接法)
                    conv_debt_into_cap DOUBLE,          -- 债务转为资本
                    conv_copbonds_due_within_1y DOUBLE, -- 一年内到期的可转换公司债券
                    fa_fnc_leases DOUBLE,               -- 融资租入固定资产
                    im_n_incr_cash_equ DOUBLE,          -- 现金及现金等价物净增加额(间接法)
                    net_dism_capital_add DOUBLE,        -- 拆出资金净增加额
                    net_cash_rece_sec DOUBLE,           -- 代理买卖证券收到的现金净额(元)
                    credit_impa_loss DOUBLE,            -- 信用减值损失
                    use_right_asset_dep DOUBLE,         -- 使用权资产折旧
                    oth_loss_asset DOUBLE,              -- 其他资产减值损失
                    end_bal_cash DOUBLE,                -- 现金的期末余额
                    beg_bal_cash DOUBLE,                -- 减:现金的期初余额
                    end_bal_cash_equ DOUBLE,            -- 加:现金等价物的期末余额
                    beg_bal_cash_equ DOUBLE,            -- 减:现金等价物的期初余额
                    update_flag VARCHAR DEFAULT '0',    -- 更新标志(1最新)
                    PRIMARY KEY (ts_code, end_date, ann_date, update_flag)
                )
                ''',
    'forecast': '''
                CREATE TABLE forecast
                (
                    ts_code        VARCHAR NOT NULL, -- TS股票代码
                    ann_date       VARCHAR NOT NULL, -- 公告日期
                    end_date       VARCHAR NOT NULL, -- 报告期
                    type           VARCHAR,          -- 业绩预告类型(预增/预减/扭亏/首亏/续亏/续盈/略增/略减)
                    p_change_min DOUBLE,             -- 预告净利润变动幅度下限（%）
                    p_change_max DOUBLE,             -- 预告净利润变动幅度上限（%）
                    net_profit_min DOUBLE,           -- 预告净利润下限（万元）
                    net_profit_max DOUBLE,           -- 预告净利润上限（万元）
                    last_parent_net DOUBLE,          -- 上年同期归属母公司净利润
                    first_ann_date VARCHAR,          -- 首次公告日
                    summary        VARCHAR,          -- 业绩预告摘要
                    change_reason  VARCHAR,          -- 业绩变动原因
                    update_flag    VARCHAR,
                    PRIMARY KEY (ts_code, end_date, ann_date, update_flag)
                )
                ''',
    'express': '''
               CREATE TABLE express (
       ts_code      VARCHAR NOT NULL,     -- TS股票代码
       ann_date     VARCHAR NOT NULL,     -- 公告日期
       end_date     VARCHAR NOT NULL,     -- 报告期
       revenue DOUBLE,                    -- 营业收入(元)
       operate_profit DOUBLE,             -- 营业利润(元)
       total_profit DOUBLE,               -- 利润总额(元)
       n_income DOUBLE,                   -- 净利润(元)
       total_assets DOUBLE,               -- 总资产(元)
       total_hldr_eqy_exc_min_int DOUBLE, -- 股东权益合计(不含少数股东权益)(元)
       diluted_eps DOUBLE,                -- 每股收益(摊薄)(元)
       diluted_roe DOUBLE,                -- 净资产收益率(摊薄)(%)
       yoy_net_profit DOUBLE,             -- 去年同期修正后净利润
       bps DOUBLE,                        -- 每股净资产
       yoy_sales DOUBLE,                  -- 同比增长率:营业收入
       yoy_op DOUBLE,                     -- 同比增长率:营业利润
       yoy_tp DOUBLE,                     -- 同比增长率:利润总额
       yoy_dedu_np DOUBLE,                -- 同比增长率:归属母公司股东的净利润
       yoy_eps DOUBLE,                    -- 同比增长率:基本每股收益
       yoy_roe DOUBLE,                    -- 同比增减:加权平均净资产收益率
       growth_assets DOUBLE,              -- 比年初增长率:总资产
       yoy_equity DOUBLE,                 -- 比年初增长率:归属母公司的股东权益
       growth_bps DOUBLE,                 -- 比年初增长率:归属于母公司股东的每股净资产
       or_last_year DOUBLE,               -- 去年同期营业收入
       op_last_year DOUBLE,               -- 去年同期营业利润
       tp_last_year DOUBLE,               -- 去年同期利润总额
       np_last_year DOUBLE,               -- 去年同期净利润
       eps_last_year DOUBLE,              -- 去年同期每股收益
       open_net_assets DOUBLE,            -- 期初净资产
       open_bps DOUBLE,                   -- 期初每股净资产
       perf_summary VARCHAR,              -- 业绩简要说明
       is_audit     INTEGER,              -- 是否审计：1是 0否
       remark       VARCHAR,              -- 备注
       update_flag  VARCHAR,
       PRIMARY KEY (ts_code, end_date, ann_date, update_flag)
    )
    ''',
    'fina_indicator': '''
                      CREATE TABLE fina_indicator (
    ts_code VARCHAR NOT NULL,               -- TS代码
    ann_date VARCHAR,                       -- 公告日期
    end_date VARCHAR NOT NULL,              -- 报告期
    eps DOUBLE,                             -- 基本每股收益
    dt_eps DOUBLE,                          -- 稀释每股收益
    total_revenue_ps DOUBLE,                -- 每股营业总收入
    revenue_ps DOUBLE,                      -- 每股营业收入
    capital_rese_ps DOUBLE,                 -- 每股资本公积
    surplus_rese_ps DOUBLE,                 -- 每股盈余公积
    undist_profit_ps DOUBLE,                -- 每股未分配利润
    extra_item DOUBLE,                      -- 非经常性损益
    profit_dedt DOUBLE,                     -- 扣除非经常性损益后的净利润（扣非净利润）
    gross_margin DOUBLE,                    -- 毛利
    current_ratio DOUBLE,                   -- 流动比率
    quick_ratio DOUBLE,                     -- 速动比率
    cash_ratio DOUBLE,                      -- 保守速动比率
    invturn_days DOUBLE,                    -- 存货周转天数
    arturn_days DOUBLE,                     -- 应收账款周转天数
    inv_turn DOUBLE,                        -- 存货周转率
    ar_turn DOUBLE,                         -- 应收账款周转率
    ca_turn DOUBLE,                         -- 流动资产周转率
    fa_turn DOUBLE,                         -- 固定资产周转率
    assets_turn DOUBLE,                     -- 总资产周转率
    op_income DOUBLE,                       -- 经营活动净收益
    valuechange_income DOUBLE,              -- 价值变动净收益
    interst_income DOUBLE,                  -- 利息费用
    daa DOUBLE,                             -- 折旧与摊销
    ebit DOUBLE,                            -- 息税前利润
    ebitda DOUBLE,                          -- 息税折旧摊销前利润
    fcff DOUBLE,                            -- 企业自由现金流量
    fcfe DOUBLE,                            -- 股权自由现金流量
    current_exint DOUBLE,                   -- 无息流动负债
    noncurrent_exint DOUBLE,                -- 无息非流动负债
    interestdebt DOUBLE,                    -- 带息债务
    netdebt DOUBLE,                         -- 净债务
    tangible_asset DOUBLE,                  -- 有形资产
    working_capital DOUBLE,                 -- 营运资金
    networking_capital DOUBLE,              -- 营运流动资本
    invest_capital DOUBLE,                  -- 全部投入资本
    retained_earnings DOUBLE,               -- 留存收益
    diluted2_eps DOUBLE,                    -- 期末摊薄每股收益
    bps DOUBLE,                             -- 每股净资产
    ocfps DOUBLE,                           -- 每股经营活动产生的现金流量净额
    retainedps DOUBLE,                      -- 每股留存收益
    cfps DOUBLE,                            -- 每股现金流量净额
    ebit_ps DOUBLE,                         -- 每股息税前利润
    fcff_ps DOUBLE,                         -- 每股企业自由现金流量
    fcfe_ps DOUBLE,                         -- 每股股东自由现金流量
    netprofit_margin DOUBLE,                -- 销售净利率
    grossprofit_margin DOUBLE,              -- 销售毛利率
    cogs_of_sales DOUBLE,                   -- 销售成本率
    expense_of_sales DOUBLE,                -- 销售期间费用率
    profit_to_gr DOUBLE,                    -- 净利润/营业总收入
    saleexp_to_gr DOUBLE,                   -- 销售费用/营业总收入
    adminexp_of_gr DOUBLE,                  -- 管理费用/营业总收入
    finaexp_of_gr DOUBLE,                   -- 财务费用/营业总收入
    impai_ttm DOUBLE,                       -- 资产减值损失/营业总收入
    gc_of_gr DOUBLE,                        -- 营业总成本/营业总收入
    op_of_gr DOUBLE,                        -- 营业利润/营业总收入
    ebit_of_gr DOUBLE,                      -- 息税前利润/营业总收入
    roe DOUBLE,                             -- 净资产收益率
    roe_waa DOUBLE,                         -- 加权平均净资产收益率
    roe_dt DOUBLE,                          -- 净资产收益率(扣除非经常损益)
    roa DOUBLE,                             -- 总资产报酬率
    npta DOUBLE,                            -- 总资产净利润
    roic DOUBLE,                            -- 投入资本回报率
    roe_yearly DOUBLE,                      -- 年化净资产收益率
    roa2_yearly DOUBLE,                     -- 年化总资产报酬率
    roe_avg DOUBLE,                         -- 平均净资产收益率(增发条件)
    opincome_of_ebt DOUBLE,                 -- 经营活动净收益/利润总额
    investincome_of_ebt DOUBLE,             -- 价值变动净收益/利润总额
    n_op_profit_of_ebt DOUBLE,              -- 营业外收支净额/利润总额
    tax_to_ebt DOUBLE,                      -- 所得税/利润总额
    dtprofit_to_profit DOUBLE,              -- 扣除非经常损益后的净利润/净利润
    salescash_to_or DOUBLE,                 -- 销售商品提供劳务收到的现金/营业收入
    ocf_to_or DOUBLE,                       -- 经营活动产生的现金流量净额/营业收入
    ocf_to_opincome DOUBLE,                 -- 经营活动产生的现金流量净额/经营活动净收益
    capitalized_to_da DOUBLE,               -- 资本支出/折旧和摊销
    debt_to_assets DOUBLE,                  -- 资产负债率
    assets_to_eqt DOUBLE,                   -- 权益乘数
    dp_assets_to_eqt DOUBLE,                -- 权益乘数(杜邦分析)
    ca_to_assets DOUBLE,                    -- 流动资产/总资产
    nca_to_assets DOUBLE,                   -- 非流动资产/总资产
    tbassets_to_totalassets DOUBLE,         -- 有形资产/总资产
    int_to_talcap DOUBLE,                   -- 带息债务/全部投入资本
    eqt_to_talcapital DOUBLE,               -- 归属于母公司的股东权益/全部投入资本
    currentdebt_to_debt DOUBLE,             -- 流动负债/负债合计
    longdeb_to_debt DOUBLE,                 -- 非流动负债/负债合计
    ocf_to_shortdebt DOUBLE,                -- 经营活动产生的现金流量净额/流动负债
    debt_to_eqt DOUBLE,                     -- 产权比率
    eqt_to_debt DOUBLE,                     -- 归属于母公司的股东权益/负债合计
    eqt_to_interestdebt DOUBLE,             -- 归属于母公司的股东权益/带息债务
    tangibleasset_to_debt DOUBLE,           -- 有形资产/负债合计
    tangasset_to_intdebt DOUBLE,            -- 有形资产/带息债务
    tangibleasset_to_netdebt DOUBLE,        -- 有形资产/净债务
    ocf_to_debt DOUBLE,                     -- 经营活动产生的现金流量净额/负债合计
    ocf_to_interestdebt DOUBLE,             -- 经营活动产生的现金流量净额/带息债务
    ocf_to_netdebt DOUBLE,                  -- 经营活动产生的现金流量净额/净债务
    ebit_to_interest DOUBLE,                -- 已获利息倍数(EBIT/利息费用)
    longdebt_to_workingcapital DOUBLE,      -- 长期债务与营运资金比率
    ebitda_to_debt DOUBLE,                  -- 息税折旧摊销前利润/负债合计
    turn_days DOUBLE,                       -- 营业周期
    roa_yearly DOUBLE,                      -- 年化总资产净利率
    roa_dp DOUBLE,                          -- 总资产净利率(杜邦分析)
    fixed_assets DOUBLE,                    -- 固定资产合计
    profit_prefin_exp DOUBLE,               -- 扣除财务费用前营业利润
    non_op_profit DOUBLE,                   -- 非营业利润
    op_to_ebt DOUBLE,                       -- 营业利润／利润总额
    nop_to_ebt DOUBLE,                      -- 非营业利润／利润总额
    ocf_to_profit DOUBLE,                   -- 经营活动产生的现金流量净额／营业利润
    cash_to_liqdebt DOUBLE,                 -- 货币资金／流动负债
    cash_to_liqdebt_withinterest DOUBLE,    -- 货币资金／带息流动负债
    op_to_liqdebt DOUBLE,                   -- 营业利润／流动负债
    op_to_debt DOUBLE,                      -- 营业利润／负债合计
    roic_yearly DOUBLE,                     -- 年化投入资本回报率
    total_fa_trun DOUBLE,                   -- 固定资产合计周转率
    profit_to_op DOUBLE,                    -- 利润总额／营业收入
    q_opincome DOUBLE,                      -- 经营活动单季度净收益
    q_investincome DOUBLE,                  -- 价值变动单季度净收益
    q_dtprofit DOUBLE,                      -- 扣除非经常损益后的单季度净利润
    q_eps DOUBLE,                           -- 每股收益(单季度)
    q_netprofit_margin DOUBLE,              -- 销售净利率(单季度)
    q_gsprofit_margin DOUBLE,               -- 销售毛利率(单季度)
    q_exp_to_sales DOUBLE,                  -- 销售期间费用率(单季度)
    q_profit_to_gr DOUBLE,                  -- 净利润／营业总收入(单季度)
    q_saleexp_to_gr DOUBLE,                 -- 销售费用／营业总收入 (单季度)
    q_adminexp_to_gr DOUBLE,                -- 管理费用／营业总收入 (单季度)
    q_finaexp_to_gr DOUBLE,                 -- 财务费用／营业总收入 (单季度)
    q_impair_to_gr_ttm DOUBLE,              -- 资产减值损失／营业总收入(单季度)
    q_gc_to_gr DOUBLE,                      -- 营业总成本／营业总收入 (单季度)
    q_op_to_gr DOUBLE,                      -- 营业利润／营业总收入(单季度)
    q_roe DOUBLE,                           -- 净资产收益率(单季度)
    q_dt_roe DOUBLE,                        -- 净资产单季度收益率(扣除非经常损益)
    q_npta DOUBLE,                          -- 总资产净利润(单季度)
    q_opincome_to_ebt DOUBLE,               -- 经营活动净收益／利润总额(单季度)
    q_investincome_to_ebt DOUBLE,           -- 价值变动净收益／利润总额(单季度)
    q_dtprofit_to_profit DOUBLE,            -- 扣除非经常损益后的净利润／净利润(单季度)
    q_salescash_to_or DOUBLE,               -- 销售商品提供劳务收到的现金／营业收入(单季度)
    q_ocf_to_sales DOUBLE,                  -- 经营活动产生的现金流量净额／营业收入(单季度)
    q_ocf_to_or DOUBLE,                     -- 经营活动产生的现金流量净额／经营活动净收益(单季度)
    basic_eps_yoy DOUBLE,                   -- 基本每股收益同比增长率(%)
    dt_eps_yoy DOUBLE,                      -- 稀释每股收益同比增长率(%)
    cfps_yoy DOUBLE,                        -- 每股经营活动产生的现金流量净额同比增长率(%)
    op_yoy DOUBLE,                          -- 营业利润同比增长率(%)
    ebt_yoy DOUBLE,                         -- 利润总额同比增长率(%)
    netprofit_yoy DOUBLE,                   -- 归属母公司股东的净利润同比增长率(%)
    dt_netprofit_yoy DOUBLE,                -- 归属母公司股东的净利润-扣除非经常损益同比增长率(%)
    ocf_yoy DOUBLE,                         -- 经营活动产生的现金流量净额同比增长率(%)
    roe_yoy DOUBLE,                         -- 净资产收益率(摊薄)同比增长率(%)
    bps_yoy DOUBLE,                         -- 每股净资产相对年初增长率(%)
    assets_yoy DOUBLE,                      -- 资产总计相对年初增长率(%)
    eqt_yoy DOUBLE,                         -- 归属母公司的股东权益相对年初增长率(%)
    tr_yoy DOUBLE,                          -- 营业总收入同比增长率(%)
    or_yoy DOUBLE,                          -- 营业收入同比增长率(%)
    q_gr_yoy DOUBLE,                        -- 营业总收入同比增长率(%)(单季度)
    q_gr_qoq DOUBLE,                        -- 营业总收入环比增长率(%)(单季度)
    q_sales_yoy DOUBLE,                     -- 营业收入同比增长率(%)(单季度)
    q_sales_qoq DOUBLE,                     -- 营业收入环比增长率(%)(单季度)
    q_op_yoy DOUBLE,                        -- 营业利润同比增长率(%)(单季度)
    q_op_qoq DOUBLE,                        -- 营业利润环比增长率(%)(单季度)
    q_profit_yoy DOUBLE,                    -- 净利润同比增长率(%)(单季度)
    q_profit_qoq DOUBLE,                    -- 净利润环比增长率(%)(单季度)
    q_netprofit_yoy DOUBLE,                 -- 归属母公司股东的净利润同比增长率(%)(单季度)
    q_netprofit_qoq DOUBLE,                 -- 归属母公司股东的净利润环比增长率(%)(单季度)
    equity_yoy DOUBLE,                      -- 净资产同比增长率
    rd_exp DOUBLE,                          -- 研发费用
    update_flag VARCHAR,                    -- 更新标识
    PRIMARY KEY (ts_code, end_date, ann_date, update_flag)
    )
    ''',
    'dividend': '''
                CREATE TABLE dividend (
        ts_code      VARCHAR NOT NULL, -- TS代码
        end_date     VARCHAR NOT NULL, -- 分红年度
        ann_date     VARCHAR NOT NULL, -- 预案公告日
        div_proc     VARCHAR NOT NULL, -- 实施进度
        stk_div DOUBLE,                -- 每股送转
        stk_bo_rate DOUBLE,            -- 每股送股比例
        stk_co_rate DOUBLE,            -- 每股转增比例
        cash_div DOUBLE,               -- 每股分红（税后）
        cash_div_tax DOUBLE,           -- 每股分红（税前）
        record_date  VARCHAR,          -- 股权登记日
        ex_date      VARCHAR,          -- 除权除息日
        pay_date     VARCHAR,          -- 派息日
        div_listdate VARCHAR,          -- 红股上市日
        imp_ann_date VARCHAR,          -- 实施公告日
        base_date    VARCHAR,          -- 基准日
        base_share DOUBLE,             -- 基准股本（万）
        update_flag  VARCHAR,
        PRIMARY KEY (ts_code, end_date, ann_date, div_proc, update_flag)
    )
    ''',
    'fina_mainbz': '''
    CREATE TABLE fina_mainbz
    (
       ts_code     VARCHAR NOT NULL, -- TS代码
       end_date    VARCHAR NOT NULL, -- 报告期
       bz_item     VARCHAR NOT NULL, -- 主营业务
       bz_sales DOUBLE,              -- 主营业务收入
       bz_profit DOUBLE,             -- 主营业务利润
       bz_cost DOUBLE,               -- 主营业务成本
       curr_type   VARCHAR,          -- 货币代码
       update_flag VARCHAR,
       PRIMARY KEY (ts_code, end_date, bz_item, update_flag)
    )
    ''',
    'disclosure_date': '''
    CREATE TABLE disclosure_date
    (
       ts_code     VARCHAR NOT NULL, -- TS代码
       ann_date    VARCHAR,          -- 公告日期
       end_date    VARCHAR,          -- 报告期
       pre_date    VARCHAR,          -- 预计披露日期
       actual_date VARCHAR,          -- 实际披露日期
       modify_date VARCHAR,          -- 修改日期
       PRIMARY KEY (ts_code, end_date, ann_date)
    )
    ''',
    'fina_audit': '''
    CREATE TABLE fina_audit
    (
      ts_code      VARCHAR NOT NULL,
      ann_date     VARCHAR,
      end_date     VARCHAR NOT NULL,
      audit_result VARCHAR,
      audit_fees   DOUBLE,
      audit_agency VARCHAR,
      audit_sign   VARCHAR,
      PRIMARY KEY (ts_code, end_date, ann_date)
    )
    ''',
    # 'stock_basic': """ ... """,
    # 'trade_cal': """ ... """,
}
