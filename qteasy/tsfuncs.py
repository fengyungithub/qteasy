# coding=utf-8
# ======================================
# File:     tsfuncs.py
# Author:   Jackie PENG
# Contact:  jackie.pengzhao@gmail.com
# Created:  2020-07-30
# Desc:
#   Interfaces to tushare data api.
# ======================================

import pandas as pd
import tushare as ts

from .utilfuncs import regulate_date_format, list_to_str_format
from .utilfuncs import retry


# tsfuncs interface function
# call this function to extract data for tables defined in DataSource module
# interface function should be defined in all data provider modules
def acquire_data(table, **kwargs):
    """ DataSource模块的接口函数，根据根据table的内容调用相应的tushare API下载数据，并以DataFrame的形式返回数据"""
    # function map 定义了table与tushare函数之间的对应关系，以便调用正确的函数下载数据
    from .database import TABLE_SOURCE_MAPPING, TABLE_SOURCE_MAPPING_COLUMNS
    assert isinstance(table, str), TypeError(f'A string should be given as table name, got {type(table)} instead')
    assert table in TABLE_SOURCE_MAPPING.keys(), ValueError(f'Invalid table name, {table} is not a valid table name')

    func_name = TABLE_SOURCE_MAPPING[table][TABLE_SOURCE_MAPPING_COLUMNS.index('tushare')]
    func = globals()[func_name]
    res = func(**kwargs)
    return res


# Tushare functions:
# Basic Market Data
# ==================


@retry(Exception)
def stock_basic(exchange: str = None):
    """ 获取基础信息数据，包括股票代码、名称、上市日期、退市日期等

    :param exchange: optional, 交易所 SSE上交所 SZSE深交所 HKEX港交所(未上线)
    :return: pd.DataFrame:
        column      type    description
        ts_code,    str,    TS代码
        symbol,     str,    股票代码
        name,       str,    股票名称
        area,       str,    所在地域
        industry,   str,    所属行业
        fullname,   str,    股票全称
        ennamem     str,    英文全称
        market,     str,    市场类型 （主板/中小板/创业板/科创板）
        exchange,   str,    交易所代码
        curr_type,  str,    交易货币
        list_status,str,    上市状态： L上市 D退市 P暂停上市
        list_date,  str,    上市日期
        delist_date,str,    退市日期
        is_hs,      str,    是否沪深港通标的，N否 H沪股通 S深股通
    """
    is_hs = ''
    list_status = 'L'
    if exchange is None:
        exchange = ''
    fields = 'ts_code,symbol,name,area,industry,fullname, enname, cnspell, market, exchange, curr_type, list_status, ' \
             'list_date, delist_date, is_hs'
    pro = ts.pro_api()
    return pro.stock_basic(exchange=exchange,
                           list_status=list_status,
                           is_hs=is_hs,
                           fields=fields)


@retry(Exception)
def trade_calendar(exchange: str = 'SSE',
                   start: str = None,
                   end: str = None,
                   is_open: int = None):
    """ 获取各大交易所交易日历数据,默认提取的是上交所
        如果不指定is_open，则返回包含所有日期以及is_open代码的DataFrame
        如果指定is_open == 0 或者 1， 则返回相应的日期列表

    :param exchange: 交易所 SSE上交所,SZSE深交所,CFFEX 中金所,SHFE 上期所,CZCE 郑商所,DCE 大商所,INE 上能源,IB 银行间,XHKG 港交所
    :param start: 开始日期
    :param end: 结束日期
    :param is_open: 是否交易 '0'休市 '1'交易
    :return: pd.DataFrame
        column          type    description
        exchange,       str,    交易所 SSE上交所 SZSE深交所
        cal_date,       str,    日历日期
        is_open,        str,    是否交易 0休市 1交易
        pretrade_date,  str,    默认不显示，  上一个交易日
    """
    pro = ts.pro_api()
    trade_cal = pro.trade_cal(exchange=exchange,
                              start_date=start,
                              end_date=end,
                              is_open=is_open)
    if is_open is None:
        return trade_cal
    else:
        return list(pd.to_datetime(trade_cal.cal_date))


@retry(Exception)
def name_change(shares: str = None,
                start: str = None,
                end: str = None):
    """ 历史名称变更记录

    :param shares:
    :param start:
    :param end:
    :return: pd.DataFrame
        column              type    default     description
        ts_code	            str	    Y	        TS代码
        name	            str	    Y	        证券名称
        start_date	        str	    Y	        开始日期
        end_date	        str	    Y	        结束日期
        ann_date	        str	    Y	        公告日期
        change_reason	    str	    Y	        变更原因
    example:
        pro = ts.pro_api()
        df = pro.namechange(ts_code='600848.SH',
                            fields='ts_code,name,start_date,end_date,change_reason')
    :output:
                ts_code     name      start_date   end_date      change_reason
        0       600848.SH   上海临港   20151118      None           改名
        1       600848.SH   自仪股份   20070514     20151117         撤销ST
        2       600848.SH   ST自仪     20061026    20070513         完成股改
        3       600848.SH   SST自仪   20061009     20061025        未股改加S
        4       600848.SH   ST自仪     20010508    20061008         ST
        5       600848.SH   自仪股份  19940324      20010507         其他
    """
    fields = 'ts_code,start_date,name,end_date,ann_date,change_reason'
    pro = ts.pro_api()
    return pro.namechange(ts_code=shares,
                          start_date=start,
                          end_date=end,
                          fields=fields)


@retry(Exception, mute=True)
def new_share(start: str = None,
              end: str = None) -> pd.DataFrame:
    """

    :param start: str, 上网发行开始日期
    :param end: str, 上网发行结束日期
    :return: pd.DataFrame
        column              type    default     description
        ts_code		        str	    Y	        TS股票代码
        sub_code	        str	    Y	        申购代码
        name		        str	    Y	        名称
        ipo_date	        str	    Y	        上网发行日期
        issue_date	        str	    Y	        上市日期
        amount		        float	Y	        发行总量（万股）
        market_amount	    float	Y	        上网发行总量（万股）
        price		        float	Y	        发行价格
        pe		            float	Y	        市盈率
        limit_amount	    float	Y	        个人申购上限（万股）
        funds		        float	Y	        募集资金（亿元）
        ballot		        float	Y	        中签率
    example:
        pro = ts.pro_api()
        df = pro.new_share(start_date='20180901', end='20181018')
    output:
            ts_code     ub_code  name  ipo_date    issue_date   amount  market_amount  \
        0   002939.SZ   002939  长城证券  20181017       None  31034.0        27931.0
        1   002940.SZ   002940   昂利康  20181011   20181023   2250.0         2025.0
        2   601162.SH   780162  天风证券  20181009   20181019  51800.0        46620.0
        3   300694.SZ   300694  蠡湖股份  20180927   20181015   5383.0         4845.0
        4   300760.SZ   300760  迈瑞医疗  20180927   20181016  12160.0        10944.0
        5   300749.SZ   300749  顶固集创  20180913   20180925   2850.0         2565.0
        6   002937.SZ   002937  兴瑞科技  20180912   20180926   4600.0         4140.0
        7   601577.SH   780577  长沙银行  20180912   20180926  34216.0        30794.0
        8   603583.SH   732583  捷昌驱动  20180911   20180921   3020.0         2718.0
        9   002936.SZ   002936  郑州银行  20180907   20180919  60000.0        54000.0
        10  300748.SZ   300748  金力永磁  20180906   20180921   4160.0         3744.0
        11  603810.SH   732810  丰山集团  20180906   20180917   2000.0         2000.0
        12  002938.SZ   002938  鹏鼎控股  20180905   20180918  23114.0        20803.0

            price     pe  limit_amount   funds  ballot
        0    6.31  22.98          9.30  19.582    0.16
        1   23.07  22.99          0.90   5.191    0.03
        2    1.79  22.86         15.50   0.000    0.25
        3    9.89  22.98          2.15   5.324    0.04
        4   48.80  22.99          3.60  59.341    0.08
        5   12.22  22.99          1.10   3.483    0.03
        6    9.94  22.99          1.80   4.572    0.04
        7    7.99   6.97         10.20  27.338    0.17
        8   29.17  22.99          1.20   8.809    0.03
        9    4.59   6.50         18.00  27.540    0.25
        10   5.39  22.98          1.20   2.242    0.05
        11  25.43  20.39          2.00   5.086    0.02
        12  16.07  22.99          6.90  37.145    0.12
    """
    pro = ts.pro_api()
    return pro.new_share(start_date=start, end_date=end)


@retry(Exception)
def stock_company(shares: str = None,
                  exchange: str = None,
                  fields: str = None) -> pd.DataFrame:
    """

    :param shares: str, 股票代码
    :param exchange: str, 交易所代码 ，SSE上交所 SZSE深交所
    :param fields: str, 逗号分隔的字段名称字符串，可选字段包括输出参数中的任意组合
    :return: pd.DataFrame
        column              type    default     description
        ts_code		        str	    Y	        股票代码
        exchange	        str	    Y	        交易所代码 ，SSE上交所 SZSE深交所
        chairman	        str	    Y	        法人代表
        manager		        str	    Y	        总经理
        secretary	        str	    Y	        董秘
        reg_capital	        float	Y	        注册资本
        setup_date	        str	    Y	        注册日期
        province	        str	    Y	        所在省份
        city		        str	    Y	        所在城市
        introduction	    str	    N	        公司介绍
        website		        str	    Y	        公司主页
        email		        str	    Y	        电子邮件
        office		        str	    N	        办公室
        employees	        int	    Y	        员工人数
        main_business	    str	    N	        主要业务及产品
        business_scope	    str	    N	        经营范围
    example:
        stock_company(exchange='SZSE',
                      fields='ts_code,chairman,manager,secretary,reg_capital,setup_date,province')
    output:
               ts_code     chairman manager     secretary   reg_capital setup_date province  \
        0     000001.SZ      谢永林     胡跃飞        周强  1.717041e+06   19871222       广东
        1     000002.SZ       郁亮     祝九胜        朱旭  1.103915e+06   19840530       广东
        2     000003.SZ      马钟鸿     马钟鸿        安汪  3.334336e+04   19880208       广东
        3     000004.SZ      李林琳     李林琳       徐文苏  8.397668e+03   19860505       广东
        4     000005.SZ       丁芃     郑列列       罗晓春  1.058537e+05   19870730       广东
        5     000006.SZ      赵宏伟     朱新宏        杜汛  1.349995e+05   19850525       广东
        6     000007.SZ      智德宇     智德宇       陈伟彬  3.464480e+04   19830311       广东
        7     000008.SZ      王志全      钟岩       王志刚  2.818330e+05   19891011       北京
        8     000009.SZ      陈政立     陈政立       郭山清  2.149345e+05   19830706       广东
        9     000010.SZ       曾嵘     李德友       金小刚  8.198547e+04   19881231       广东
        10    000011.SZ      刘声向     王航军       范维平  5.959791e+04   19830117       广东
    """
    if fields is None:
        fields = 'ts_code,chairman,manager,secretary,reg_capital,setup_date,province'
    pro = ts.pro_api()
    return pro.stock_company(ts_code=shares, exchange=exchange, fields=fields)


# Bar price data
# ==================
@retry(Exception, mute=True)
def daily_basic(shares: object = None,
                trade_date: object = None,
                start: object = None,
                end: object = None) -> pd.DataFrame:
    """ tushare function wrapper: """
    pro = ts.pro_api()
    return pro.daily_basic(ts_code=shares,
                           trade_date=trade_date,
                           start_date=start,
                           end_date=end)


@retry(Exception, mute=True)
def daily_basic2(shares: object = None,
                 trade_date: object = None,
                 start: object = None,
                 end: object = None) -> pd.DataFrame:
    """ tushare function wrapper: """
    pro = ts.pro_api()
    return pro.bak_daily(ts_code=shares,
                         trade_date=trade_date,
                         start_date=start,
                         end_date=end)


@retry(Exception, mute=True)
def index_daily_basic(shares: object = None,
                      trade_date: object = None,
                      start: object = None,
                      end: object = None) -> pd.DataFrame:
    """ tushare function wrapper: """
    pro = ts.pro_api()
    return pro.index_dailybasic(ts_code=shares,
                                trade_date=trade_date,
                                start_date=start,
                                end_date=end)


@retry(Exception, mute=True)
def mins(share: object = None,
         start=None,
         end=None,
         freq=None):
    # 注意，分钟数据是不分股票、基金、指数的，全部都在一张表中，所以必须先获取权限后下载
    pro = ts.pro_api()
    return pro.stk_mins(ts_code=share, start_date=start, end_date=end, freq=freq)


@retry(Exception, mute=True)
def daily(share=None,
          trade_date=None,
          start=None,
          end=None):
    """

    :param share:
    :param trade_date:
    :param start:
    :param end:
    :return:
    """
    pro = ts.pro_api()
    return pro.daily(ts_code=share, trade_date=trade_date, start_date=start, end_date=end)


@retry(Exception, mute=True)
def weekly(share=None,
           trade_date=None,
           start=None,
           end=None):
    """

    :param share:
    :param trade_date:
    :param start:
    :param end:
    :return:
    """
    pro = ts.pro_api()
    return pro.weekly(ts_code=share, trade_date=trade_date, start_date=start, end_date=end)


@retry(Exception, mute=True)
def monthly(share=None,
            trade_date=None,
            start=None,
            end=None):
    """

    :param share:
    :param trade_date:
    :param start:
    :param end:
    :return:
    """
    pro = ts.pro_api()
    return pro.monthly(ts_code=share, trade_date=trade_date, start_date=start, end_date=end)


@retry(Exception, mute=True)
def index_daily(index=None,
                trade_date=None,
                start=None,
                end=None):
    """

    :param index:
    :param trade_date:
    :param start:
    :param end:
    :return:
    """
    pro = ts.pro_api()
    return pro.index_daily(ts_code=index, trade_date=trade_date, start_date=start, end_date=end)


@retry(Exception, mute=True)
def index_weekly(index=None,
                 trade_date=None,
                 start=None,
                 end=None):
    """

    :param index:
    :param trade_date:
    :param start:
    :param end:
    :return:
    """
    pro = ts.pro_api()
    return pro.index_weekly(ts_code=index, trade_date=trade_date, start_date=start, end_date=end)


@retry(Exception, mute=True)
def index_monthly(index=None,
                  trade_date=None,
                  start=None,
                  end=None):
    """

    :param index:
    :param trade_date:
    :param start:
    :param end:
    :return:
    """
    pro = ts.pro_api()
    return pro.index_monthly(ts_code=index, trade_date=trade_date, start_date=start, end_date=end)


@retry(Exception, mute=True)
def fund_daily(fund=None,
               trade_date=None,
               start=None,
               end=None):
    """

    :param fund:
    :param trade_date:
    :param start:
    :param end:
    :return:
    """
    pro = ts.pro_api()
    return pro.fund_daily(ts_code=fund, trade_date=trade_date, start_date=start, end_date=end)


@retry(Exception, mute=True)
def adj_factors(shares=None,
                trade_date=None,
                start=None,
                end=None):
    """

    :param shares:
    :param trade_date:
    :param start:
    :param end:
    :return:
    """
    pro = ts.pro_api()
    return pro.adj_factor(ts_code=shares, trade_date=trade_date, start_date=start, end_date=end)


@retry(Exception, mute=True)
def fund_adj(shares=None,
             trade_date=None,
             start=None,
             end=None):
    """

    :param shares:
    :param trade_date:
    :param start:
    :param end:
    :return:
    """
    pro = ts.pro_api()
    return pro.fund_adj(ts_code=shares, trade_date=trade_date, start_date=start, end_date=end)


@retry(Exception, mute=True)
def fund_share(fund=None,
               trade_date=None,
               start=None,
               end=None):
    """

    :param fund: 基金代码，支持多只基金同时提取，用逗号分隔
    :param trade_date:  交易变动日期，格式YYYYMMDD
    :param start:
    :param end:
    :return:
    """
    pro = ts.pro_api()
    return pro.fund_share(ts_code=fund, trade_date=trade_date, start_date=start, end_date=end)


@retry(Exception, mute=True)
def fund_manager(fund=None,
                 ann_date=None,
                 offset=None):
    """

    :param fund: 基金代码，支持多只基金同时提取，用逗号分隔
    :param ann_date:  公告日期，格式YYYYMMDD
    :param offset:
    :return:
    """
    pro = ts.pro_api()
    return pro.fund_manager(ts_code=fund, ann_date=ann_date, offset=offset)


# Finance Data
# ================
@retry(Exception)
def income(share: str,
           rpt_date: str = None,
           start: str = None,
           end: str = None,
           period: str = None,
           report_type: str = None,
           comp_type: str = None,
           fields: [str, list] = None) -> pd.DataFrame:
    """ 获取上市公司财务利润表数据

    :rtype: pd.DataFrame
    :param share: 股票代码，注意一次只能读取一只股票的数据
    :param rpt_date: optional 公告日期
    :param start: optional 公告开始日期
    :param end: optional 公告结束日期
    :param period: optional 报告期(每个季度最后一天的日期，比如20171231表示年报)
    :param report_type: optional 报告类型： 参考下表说明
    :param comp_type: optional 公司类型：1一般工商业 2银行 3保险 4证券
    :param fields: str, 输出数据，结果DataFrame的数据列名，用逗号分隔
    :return: pd.DataFrame:
        column              type   dft  description
        ts_code	            str	    Y   TS代码
        ann_date	        str	    Y	公告日期
        f_ann_date	        str	    Y	实际公告日期
        end_date	        str	    Y	报告期
        report_type	        str	    Y	报告类型 1合并报表                  上市公司最新报表（默认）
                                                2单季合并                  单一季度的合并报表
                                                3调整单季合并表            调整后的单季合并报表（如果有）
                                                4调整合并报表             本年度公布上年同期的财务报表数据，报告期为上年度
                                                5调整前合并报表            数据发生变更，将原数据进行保留，即调整前的原数据
                                                6母公司报表              该公司母公司的财务报表数据
                                                7母公司单季表             母公司的单季度表
                                                8 母公司调整单季表         母公司调整后的单季表
                                                9母公司调整表             该公司母公司的本年度公布上年同期的财务报表数据
                                                10母公司调整前报表          母公司调整之前的原始财务报表数据
                                                11调整前合并报表           调整之前合并报表原数据
                                                12母公司调整前报表          母公司报表发生变更前保留的原数据
        comp_type	        str	    Y	公司类型(1一般工商业2银行3保险4证券)
        basic_eps	        float	Y	基本每股收益
        diluted_eps	        float	Y	稀释每股收益
        total_revenue	    float	Y	营业总收入
        revenue	            float	Y	营业收入
        int_income	        float	Y	利息收入
        prem_earned	        float	Y	已赚保费
        comm_income	        float	Y	手续费及佣金收入
        n_commis_income	    float	Y	手续费及佣金净收入
        n_oth_income	    float	Y	其他经营净收益
        n_oth_b_income	    float	Y	加:其他业务净收益
        prem_income	        float	Y	保险业务收入
        out_prem	        float	Y	减:分出保费
        une_prem_reser	    float	Y	提取未到期责任准备金
        reins_income	    float	Y	其中:分保费收入
        n_sec_tb_income	    float	Y	代理买卖证券业务净收入
        n_sec_uw_income	    float	Y	证券承销业务净收入
        n_asset_mg_income	float	Y	受托客户资产管理业务净收入
        oth_b_income	    float	Y	其他业务收入
        fv_value_chg_gain	float	Y	加:公允价值变动净收益
        invest_income	    float	Y	加:投资净收益
        ass_invest_income	float	Y	其中:对联营企业和合营企业的投资收益
        forex_gain	        float	Y	加:汇兑净收益
        total_cogs	        float	Y	营业总成本
        oper_cost	        float	Y	减:营业成本
        int_exp	            float	Y	减:利息支出
        comm_exp	        float	Y	减:手续费及佣金支出
        biz_tax_surchg	    float	Y	减:营业税金及附加
        sell_exp	        float	Y	减:销售费用
        admin_exp	        float	Y	减:管理费用
        fin_exp	            float	Y	减:财务费用
        assets_impair_loss	float	Y	减:资产减值损失
        prem_refund	        float	Y	退保金
        compens_payout	    float	Y	赔付总支出
        reser_insur_liab	float	Y	提取保险责任准备金
        div_payt	        float	Y	保户红利支出
        reins_exp	        float	Y	分保费用
        oper_exp	        float	Y	营业支出
        compens_payout_refu	float	Y	减:摊回赔付支出
        insur_reser_refu	float	Y	减:摊回保险责任准备金
        reins_cost_refund	float	Y	减:摊回分保费用
        other_bus_cost	    float	Y	其他业务成本
        operate_profit	    float	Y	营业利润
        non_oper_income	    float	Y	加:营业外收入
        non_oper_exp	    float	Y	减:营业外支出
        nca_disploss	    float	Y	其中:减:非流动资产处置净损失
        total_profit	    float	Y	利润总额
        income_tax	        float	Y	所得税费用
        n_income	        float	Y	净利润(含少数股东损益)
        n_income_attr_p	    float	Y	净利润(不含少数股东损益)
        minority_gain	    float	Y	少数股东损益
        oth_compr_income	float	Y	其他综合收益
        t_compr_income	    float	Y	综合收益总额
        compr_inc_attr_p	float	Y	归属于母公司(或股东)的综合收益总额
        compr_inc_attr_m_s	float	Y	归属于少数股东的综合收益总额
        ebit	            float	Y	息税前利润
        ebitda	            float	Y	息税折旧摊销前利润
        insurance_exp	    float	Y	保险业务支出
        undist_profit	    float	Y	年初未分配利润
        distable_profit	    float	Y	可分配利润
        update_flag	        str	    N	更新标识，0未修改1更正过
    :example
        income(share='600000.SH', start_date='20180101',
               end='20180730',
               fields='ts_code,ann_date,f_ann_date,report_type,comp_type,basic_eps,diluted_eps')
    """
    if fields is None:
        fields = 'ts_code, ann_date, f_ann_date, end_date, report_type, comp_type, end_type, basic_eps, diluted_eps, ' \
                 'total_revenue, revenue, int_income, prem_earned, comm_income, n_commis_income, n_oth_income, ' \
                 'n_oth_b_income, prem_income, out_prem, une_prem_reser, reins_income, n_sec_tb_income, ' \
                 'n_sec_uw_income, n_asset_mg_income, oth_b_income, fv_value_chg_gain, invest_income, ' \
                 'ass_invest_income, forex_gain, total_cogs, oper_cost, int_exp, comm_exp, biz_tax_surchg, sell_exp, ' \
                 'admin_exp, fin_exp, assets_impair_loss, prem_refund, compens_payout, reser_insur_liab, div_payt, ' \
                 'reins_exp, oper_exp, compens_payout_refu, insur_reser_refu, reins_cost_refund, other_bus_cost, ' \
                 'operate_profit, non_oper_income, non_oper_exp, nca_disploss, total_profit, income_tax, n_income, ' \
                 'n_income_attr_p, minority_gain, oth_compr_income, t_compr_income, compr_inc_attr_p, ' \
                 'compr_inc_attr_m_s, ebit, ebitda, insurance_exp, undist_profit, distable_profit, rd_exp, ' \
                 'fin_exp_int_exp, fin_exp_int_inc, transfer_surplus_rese, transfer_housing_imprest, transfer_oth,' \
                 'adj_lossgain, withdra_legal_surplus, withdra_legal_pubfund, withdra_biz_devfund, withdra_rese_fund,' \
                 'withdra_oth_ersu, workers_welfare, distr_profit_shrhder, prfshare_payable_dvd, ' \
                 'comshare_payable_dvd, capit_comstock_div, net_after_nr_lp_correct, credit_impa_loss, ' \
                 'net_expo_hedging_benefits, oth_impair_loss_assets, total_opcost, amodcost_fin_assets, oth_income, ' \
                 'asset_disp_income, continued_net_profit, end_net_profit, update_flag'
    if isinstance(share, list):
        share = list_to_str_format(share)
    if isinstance(fields, list):
        fields = list_to_str_format(fields)
    pro = ts.pro_api()
    if start is not None:
        start = regulate_date_format(start)
    if end is not None:
        end = regulate_date_format(end)
    return pro.income(ts_code=share,
                      ann_date=rpt_date,
                      start_date=start,
                      end_date=end,
                      period=period,
                      report_type=report_type,
                      comp_type=comp_type,
                      fields=fields)


@retry(Exception)
def balance(share: str,
            rpt_date: str = None,
            start: str = None,
            end: str = None,
            period: str = None,
            report_type: str = None,
            comp_type: str = None,
            fields: [str, list] = None) -> pd.DataFrame:
    """ 获取上市公司财务数据资产负债表

    :param share: 股票代码
    :param rpt_date: optional 公告日期
    :param start: optional 公告开始日期
    :param end: optional 公告结束日期
    :param period: optional 报告期(每个季度最后一天的日期，比如20171231表示年报)
    :param report_type: optional 报告类型： 参考下表说明
    :param comp_type: optional 公司类型：1一般工商业 2银行 3保险 4证券
    :param fields: str, 输出数据，结果DataFrame的数据列名，用逗号分隔
    :return: pd.DataFrame
        column              type    default description
        s_code			    str	        Y	TS股票代码
        ann_date		    str	        Y	公告日期
        f_ann_date		    str	        Y	实际公告日期
        end_date		    str	        Y	报告期
        report_type		    str	        Y	报表类型
        comp_type		    str	        Y	公司类型
        total_share		    float	    Y	期末总股本
        cap_rese		    float	    Y	资本公积金
        undistr_porfit		float	    Y	未分配利润
        surplus_rese		float	    Y	盈余公积金
        special_rese		float	    Y	专项储备
        money_cap		    float	    Y	货币资金
        trad_asset		    float	    Y	交易性金融资产
        notes_receiv		float	    Y	应收票据
        accounts_receiv		float	    Y	应收账款
        oth_receiv		    float	    Y  	其他应收款
        prepayment		    float	    Y	预付款项
        div_receiv		    float	    Y	应收股利
        int_receiv		    float   	Y	应收利息
        inventories		    float	    Y	存货
        amor_exp		    float	    Y	待摊费用
        nca_within_1y		float	    Y	一年内到期的非流动资产
        sett_rsrv		    float	    Y	结算备付金
        loanto_oth_bank_fi	float	    Y	拆出资金
        premium_receiv		float	    Y	应收保费
        reinsur_receiv		float	    Y	应收分保账款
        reinsur_res_receiv	float	    Y	应收分保合同准备金
        pur_resale_fa		float	    Y	买入返售金融资产
        oth_cur_assets		float	    Y	其他流动资产
        total_cur_assets	float	    Y	流动资产合计
        fa_avail_for_sale	float	    Y	可供出售金融资产
        htm_invest		    float	    Y   持有至到期投资
        lt_eqt_invest		float	    Y	长期股权投资
        invest_real_estate	float	    Y	投资性房地产
        time_deposits		float	    Y	定期存款
        oth_assets		    float	    Y	其他资产
        lt_rec			    float	    Y	长期应收款
        fix_assets		    float	    Y	固定资产
        cip			        float	    Y	在建工程
        const_materials		float	    Y	工程物资
        fixed_assets_disp	float	    Y	固定资产清理
        produc_bio_assets	float	    Y	生产性生物资产
        oil_and_gas_assets	float	    Y	油气资产
        intan_assets		float	    Y	无形资产
        r_and_d			    float	    Y	研发支出
        goodwill		    float	    Y	商誉
        lt_amor_exp		    float	    Y	长期待摊费用
        defer_tax_assets	float	    Y	递延所得税资产
        decr_in_disbur		float	    Y	发放贷款及垫款
        oth_nca			    float	    Y	其他非流动资产
        total_nca		    float	    Y	非流动资产合计
        cash_reser_cb		float	    Y	现金及存放中央银行款项
        depos_in_oth_bfi	float	    Y	存放同业和其它金融机构款项
        prec_metals		    float	    Y	贵金属
        deriv_assets		float	    Y	衍生金融资产
        rr_reins_une_prem	float	    Y	应收分保未到期责任准备金
        rr_reins_outstd_cla	float	    Y	应收分保未决赔款准备金
        rr_reins_lins_liab	float	    Y	应收分保寿险责任准备金
        rr_reins_lthins_liab	float	Y	应收分保长期健康险责任准备金
        refund_depos		float	    Y	存出保证金
        ph_pledge_loans		float	    Y	保户质押贷款
        refund_cap_depos	float	    Y	存出资本保证金
        indep_acct_assets	float	    Y	独立账户资产
        client_depos		float	    Y	其中：客户资金存款
        client_prov		    float	    Y	其中：客户备付金
        transac_seat_fee	float	    Y	其中:交易席位费
        invest_as_receiv	float	    Y	应收款项类投资
        total_assets		float	    Y	资产总计
        lt_borr			    float	    Y	长期借款
        st_borr			    float	    Y	短期借款
        cb_borr			    float	    Y	向中央银行借款
        depos_ib_deposits	float	    Y	吸收存款及同业存放
        loan_oth_bank		float	    Y	拆入资金
        trading_fl		    float	    Y	交易性金融负债
        notes_payable		float	    Y	应付票据
        acct_payable		float	    Y	应付账款
        adv_receipts		float	    Y	预收款项
        sold_for_repur_fa	float	    Y	卖出回购金融资产款
        comm_payable		float	    Y	应付手续费及佣金
        payroll_payable		float	    Y	应付职工薪酬
        taxes_payable		float	    Y	应交税费
        int_payable		    float	    Y	应付利息
        div_payable		    float	    Y	应付股利
        oth_payable		    float	    Y	其他应付款
        acc_exp			    float	    Y	预提费用
        deferred_inc		float	    Y	递延收益
        st_bonds_payable	float	    Y	应付短期债券
        payable_to_reinsurer	float	Y	应付分保账款
        rsrv_insur_cont		float	    Y	保险合同准备金
        acting_trading_sec	float	    Y	代理买卖证券款
        acting_uw_sec		float	    Y	代理承销证券款
        non_cur_liab_due_1y	float	    Y	一年内到期的非流动负债
        oth_cur_liab		float	    Y	其他流动负债
        total_cur_liab		float	    Y	流动负债合计
        bond_payable		float	    Y	应付债券
        lt_payable		    float	    Y	长期应付款
        specific_payables	float	    Y	专项应付款
        estimated_liab		float	    Y	预计负债
        defer_tax_liab		float	    Y	递延所得税负债
        defer_inc_non_cur_liab	float	Y	递延收益-非流动负债
        oth_ncl			    float	    Y	其他非流动负债
        total_ncl		    float	    Y	非流动负债合计
        depos_oth_bfi		float	    Y	同业和其它金融机构存放款项
        deriv_liab		    float	    Y	衍生金融负债
        depos			    float	    Y	吸收存款
        agency_bus_liab		float	    Y	代理业务负债
        oth_liab		    float	    Y	其他负债
        prem_receiv_adva	float	    Y	预收保费
        depos_received		float	    Y	存入保证金
        ph_invest		    float	    Y	保户储金及投资款
        reser_une_prem		float	    Y	未到期责任准备金
        reser_outstd_claims	float	    Y	未决赔款准备金
        reser_lins_liab		float	    Y	寿险责任准备金
        reser_lthins_liab	float	    Y	长期健康险责任准备金
        indept_acc_liab		float	    Y	独立账户负债
        pledge_borr		    float	    Y	其中:质押借款
        indem_payable		float	    Y	应付赔付款
        policy_div_payable	float	    Y	应付保单红利
        total_liab		    float	    Y	负债合计
        treasury_share		float	    Y	减:库存股
        ordin_risk_reser	float	    Y	一般风险准备
        forex_differ		float	    Y	外币报表折算差额
        invest_loss_unconf	float	    Y	未确认的投资损失
        minority_int		float	    Y	少数股东权益
        total_hldr_eqy_exc_min_int	float	Y	股东权益合计(不含少数股东权益)
        total_hldr_eqy_inc_min_int	float	Y	股东权益合计(含少数股东权益)
        total_liab_hldr_eqy	float	    Y	负债及股东权益总计
        lt_payroll_payable	float	    Y	长期应付职工薪酬
        oth_comp_income		float	    Y	其他综合收益
        oth_eqt_tools		float	    Y	其他权益工具
        oth_eqt_tools_p_shr	float	    Y	其他权益工具(优先股)
        lending_funds		float	    Y	融出资金
        acc_receivable		float	    Y	应收款项
        st_fin_payable		float	    Y	应付短期融资款
        payables		    float	    Y	应付款项
        hfs_assets		    float	    Y	持有待售的资产
        hfs_sales		    float	    Y	持有待售的负债
        update_flag		    str	        N	更新标识
    report types:
        code type           description
        1	合并报表	        上市公司最新报表（默认）
        2	单季合并	        单一季度的合并报表
        3	调整单季合并表	    调整后的单季合并报表（如果有）
        4	调整合并报表	    本年度公布上年同期的财务报表数据，报告期为上年度
        5	调整前合并报表	    数据发生变更，将原数据进行保留，即调整前的原数据
        6	母公司报表	    该公司母公司的财务报表数据
        7	母公司单季表	    母公司的单季度表
        8	母公司调整单季表	母公司调整后的单季表
        9	母公司调整表	    该公司母公司的本年度公布上年同期的财务报表数据
        10	母公司调整前报表	母公司调整之前的原始财务报表数据
        11	调整前合并报表 	调整之前合并报表原数据
        12	母公司调整前报表	母公司报表发生变更前保留的原数据
    example:
    df = balance(ts_code='600000.SH',
                 start_date='20180101',
                 end_date='20180730',
                 fields='ts_code,ann_date,f_ann_date,end_date,report_type,comp_type,cap_rese')
    """
    if fields is None:
        fields = 'ts_code, ann_date, f_ann_date, end_date, report_type, comp_type, end_type, total_share, cap_rese, ' \
                 'undistr_porfit, surplus_rese, special_rese, money_cap, trad_asset, notes_receiv, accounts_receiv, ' \
                 'oth_receiv, prepayment, div_receiv, int_receiv, inventories, amor_exp, nca_within_1y, sett_rsrv, ' \
                 'loanto_oth_bank_fi, premium_receiv, reinsur_receiv, reinsur_res_receiv, pur_resale_fa, ' \
                 'oth_cur_assets, total_cur_assets, fa_avail_for_sale, htm_invest, lt_eqt_invest, ' \
                 'invest_real_estate, time_deposits, oth_assets, lt_rec, fix_assets, cip, const_materials, ' \
                 'fixed_assets_disp, produc_bio_assets, oil_and_gas_assets, intan_assets, r_and_d, goodwill, ' \
                 'lt_amor_exp, defer_tax_assets, decr_in_disbur, oth_nca, total_nca, cash_reser_cb, ' \
                 'depos_in_oth_bfi, prec_metals, deriv_assets, rr_reins_une_prem, rr_reins_outstd_cla, ' \
                 'rr_reins_lins_liab, rr_reins_lthins_liab, refund_depos, ph_pledge_loans, refund_cap_depos, ' \
                 'indep_acct_assets, client_depos, client_prov, transac_seat_fee, invest_as_receiv, total_assets, ' \
                 'lt_borr, st_borr, cb_borr, depos_ib_deposits, loan_oth_bank, trading_fl, notes_payable, ' \
                 'acct_payable, adv_receipts, sold_for_repur_fa, comm_payable, payroll_payable, taxes_payable, ' \
                 'int_payable, div_payable, oth_payable, acc_exp, deferred_inc, st_bonds_payable, ' \
                 'payable_to_reinsurer, rsrv_insur_cont, acting_trading_sec, acting_uw_sec, non_cur_liab_due_1y, ' \
                 'oth_cur_liab, total_cur_liab, bond_payable, lt_payable, specific_payables, estimated_liab, ' \
                 'defer_tax_liab, defer_inc_non_cur_liab, oth_ncl, total_ncl, depos_oth_bfi, deriv_liab, depos, ' \
                 'agency_bus_liab, oth_liab, prem_receiv_adva, depos_received, ph_invest, reser_une_prem, ' \
                 'reser_outstd_claims, reser_lins_liab, reser_lthins_liab, indept_acc_liab, pledge_borr, ' \
                 'indem_payable, policy_div_payable, total_liab, treasury_share, ordin_risk_reser, forex_differ, ' \
                 'invest_loss_unconf, minority_int, total_hldr_eqy_exc_min_int, total_hldr_eqy_inc_min_int, ' \
                 'total_liab_hldr_eqy, lt_payroll_payable, oth_comp_income, oth_eqt_tools, oth_eqt_tools_p_shr, ' \
                 'lending_funds, acc_receivable, st_fin_payable, payables, hfs_assets, hfs_sales, cost_fin_assets, ' \
                 'fair_value_fin_assets, cip_total, oth_pay_total, long_pay_total, debt_invest, oth_debt_invest, ' \
                 'oth_eq_invest, oth_illiq_fin_assets, oth_eq_ppbond, receiv_financing, use_right_assets, ' \
                 'lease_liab, contract_assets, contract_liab, accounts_receiv_bill, accounts_pay, oth_rcv_total, ' \
                 'fix_assets_total, update_flag'
    if isinstance(share, list):
        share = list_to_str_format(share)
    if isinstance(fields, list):
        fields = list_to_str_format(fields)
    pro = ts.pro_api()
    start = regulate_date_format(start)
    end = regulate_date_format(end)
    res = pro.balancesheet(ts_code=share,
                           ann_date=rpt_date,
                           start_date=start,
                           end_date=end,
                           period=period,
                           report_type=report_type,
                           comp_type=comp_type,
                           fields=fields)
    return res


@retry(Exception)
def cashflow(share: str,
             rpt_date: str = None,
             start: str = None,
             end: str = None,
             period: str = None,
             report_type: str = None,
             comp_type: str = None,
             fields: [str, list] = None) -> pd.DataFrame:
    """ 获取上市公司财务数据现金流量表

    :param share:                     股票代码
    :param rpt_date: optional           公告日期
    :param start: optional         公告开始日期
    :param end: optional           公告结束日期
    :param period: optional             报告期(每个季度最后一天的日期，比如20171231表示年报)
    :param report_type: optional        报告类型： 参考下表说明
    :param comp_type: optional          公司类型：1一般工商业 2银行 3保险 4证券
    :param fields: str,                 输出数据，结果DataFrame的数据列名，用逗号分隔
    :return: pd.DataFrame
        column                      type    default description
        ts_code				        str	    Y	TS股票代码
        ann_date			        str	    Y	公告日期
        f_ann_date			        str	    Y	实际公告日期
        end_date			        str	    Y	报告期
        comp_type			        str	    Y	公司类型
        report_type			        str	    Y	报表类型
        net_profit			        float	Y	净利润
        finan_exp			        float	Y	财务费用
        c_fr_sale_sg			    float	Y	销售商品、提供劳务收到的现金
        recp_tax_rends			    float	Y	收到的税费返还
        n_depos_incr_fi			    float	Y	客户存款和同业存放款项净增加额
        n_incr_loans_cb			    float	Y	向中央银行借款净增加额
        n_inc_borr_oth_fi		    float	Y	向其他金融机构拆入资金净增加额
        prem_fr_orig_contr		    float	Y	收到原保险合同保费取得的现金
        n_incr_insured_dep		    float	Y	保户储金净增加额
        n_reinsur_prem			    float	Y	收到再保业务现金净额
        n_incr_disp_tfa			    float	Y	处置交易性金融资产净增加额
        ifc_cash_incr			    float	Y	收取利息和手续费净增加额
        n_incr_disp_faas		    float	Y	处置可供出售金融资产净增加额
        n_incr_loans_oth_bank		float	Y	拆入资金净增加额
        n_cap_incr_repur		    float	Y	回购业务资金净增加额
        c_fr_oth_operate_a		    float	Y	收到其他与经营活动有关的现金
        c_inf_fr_operate_a		    float	Y	经营活动现金流入小计
        c_paid_goods_s			    float	Y	购买商品、接受劳务支付的现金
        c_paid_to_for_empl		    float	Y	支付给职工以及为职工支付的现金
        c_paid_for_taxes		    float	Y	支付的各项税费
        n_incr_clt_loan_adv		    float	Y	客户贷款及垫款净增加额
        n_incr_dep_cbob			    float	Y	存放央行和同业款项净增加额
        c_pay_claims_orig_inco		float	Y	支付原保险合同赔付款项的现金
        pay_handling_chrg		    float	Y	支付手续费的现金
        pay_comm_insur_plcy		    float	Y	支付保单红利的现金
        oth_cash_pay_oper_act		float	Y	支付其他与经营活动有关的现金
        st_cash_out_act			    float	Y	经营活动现金流出小计
        n_cashflow_act			    float	Y	经营活动产生的现金流量净额
        oth_recp_ral_inv_act		float	Y	收到其他与投资活动有关的现金
        c_disp_withdrwl_invest		float	Y	收回投资收到的现金
        c_recp_return_invest		float	Y	取得投资收益收到的现金
        n_recp_disp_fiolta		    float	Y	处置固定资产、无形资产和其他长期资产收回的现金净额
        n_recp_disp_sobu		    float	Y	处置子公司及其他营业单位收到的现金净额
        stot_inflows_inv_act		float	Y	投资活动现金流入小计
        c_pay_acq_const_fiolta		float	Y	购建固定资产、无形资产和其他长期资产支付的现金
        c_paid_invest			    float	Y	投资支付的现金
        n_disp_subs_oth_biz		    float	Y	取得子公司及其他营业单位支付的现金净额
        oth_pay_ral_inv_act		    float	Y	支付其他与投资活动有关的现金
        n_incr_pledge_loan		    float	Y	质押贷款净增加额
        stot_out_inv_act		    float	Y	投资活动现金流出小计
        n_cashflow_inv_act		    float	Y	投资活动产生的现金流量净额
        c_recp_borrow			    float	Y	取得借款收到的现金
        proc_issue_bonds		    float	Y	发行债券收到的现金
        oth_cash_recp_ral_fnc_act	float	Y	收到其他与筹资活动有关的现金
        stot_cash_in_fnc_act		float	Y	筹资活动现金流入小计
        free_cashflow			    float	Y	企业自由现金流量
        c_prepay_amt_borr		    float	Y	偿还债务支付的现金
        c_pay_dist_dpcp_int_exp		float	Y	分配股利、利润或偿付利息支付的现金
        incl_dvd_profit_paid_sc_ms	float	Y	其中:子公司支付给少数股东的股利、利润
        oth_cashpay_ral_fnc_act		float	Y	支付其他与筹资活动有关的现金
        stot_cashout_fnc_act		float	Y	筹资活动现金流出小计
        n_cash_flows_fnc_act		float	Y	筹资活动产生的现金流量净额
        eff_fx_flu_cash			    float	Y	汇率变动对现金的影响
        n_incr_cash_cash_equ		float	Y	现金及现金等价物净增加额
        c_cash_equ_beg_period		float	Y	期初现金及现金等价物余额
        c_cash_equ_end_period		float	Y	期末现金及现金等价物余额
        c_recp_cap_contrib		    float	Y	吸收投资收到的现金
        incl_cash_rec_saims		    float	Y	其中:子公司吸收少数股东投资收到的现金
        uncon_invest_loss		    float	Y	未确认投资损失
        prov_depr_assets		    float	Y	加:资产减值准备
        depr_fa_coga_dpba		    float	Y	固定资产折旧、油气资产折耗、生产性生物资产折旧
        amort_intang_assets		    float	Y	无形资产摊销
        lt_amort_deferred_exp		float	Y	长期待摊费用摊销
        decr_deferred_exp		    float	Y	待摊费用减少
        incr_acc_exp			    float	Y	预提费用增加
        loss_disp_fiolta		    float	Y	处置固定、无形资产和其他长期资产的损失
        loss_scr_fa			        float	Y	固定资产报废损失
        loss_fv_chg			        float	Y	公允价值变动损失
        invest_loss			        float	Y	投资损失
        decr_def_inc_tax_assets		float	Y	递延所得税资产减少
        incr_def_inc_tax_liab		float	Y	递延所得税负债增加
        decr_inventories		    float	Y	存货的减少
        decr_oper_payable		    float	Y	经营性应收项目的减少
        incr_oper_payable		    float	Y	经营性应付项目的增加
        others				        float	Y	其他
        im_net_cashflow_oper_act	float	Y	经营活动产生的现金流量净额(间接法)
        conv_debt_into_cap		    float	Y	债务转为资本
        conv_copbonds_due_within_1y	float	Y	一年内到期的可转换公司债券
        fa_fnc_leases			    float	Y	融资租入固定资产
        end_bal_cash			    float	Y	现金的期末余额
        beg_bal_cash			    float	Y	减:现金的期初余额
        end_bal_cash_equ		    float	Y	加:现金等价物的期末余额
        beg_bal_cash_equ		    float	Y	减:现金等价物的期初余额
        im_n_incr_cash_equ		    float	Y	现金及现金等价物净增加额(间接法)
        update_flag			        str	    N	更新标识
    report types:
        1	合并报表	            上市公司最新报表（默认）
        2	单季合并	            单一季度的合并报表
        3	调整单季合并表     	调整后的单季合并报表（如果有）
        4	调整合并报表	        本年度公布上年同期的财务报表数据，报告期为上年度
        5	调整前合并报表	        数据发生变更，将原数据进行保留，即调整前的原数据
        6	母公司报表	        该公司母公司的财务报表数据
        7	母公司单季表	        母公司的单季度表
        8	母公司调整单季表	    母公司调整后的单季表
        9	母公司调整表	        该公司母公司的本年度公布上年同期的财务报表数据
        10	母公司调整前报表	    母公司调整之前的原始财务报表数据
        11	调整前合并报表	        调整之前合并报表原数据
        12	母公司调整前报表	    母公司报表发生变更前保留的原数据
    example:
        cashflow(ts_code='600000.SH',
                 start_date='20180101',
                 end_date='20180730',
                 fields = 'fa_fnc_leases, end_bal_cash, beg_bal_cash')
    """
    if fields is None:
        fields = 'ts_code, ann_date, f_ann_date, end_date, comp_type, report_type, end_type, net_profit, finan_exp, ' \
                 'c_fr_sale_sg, recp_tax_rends, n_depos_incr_fi, n_incr_loans_cb, n_inc_borr_oth_fi,' \
                 'prem_fr_orig_contr, n_incr_insured_dep, n_reinsur_prem, n_incr_disp_tfa, ifc_cash_incr,' \
                 ' n_incr_disp_faas, n_incr_loans_oth_bank, n_cap_incr_repur, c_fr_oth_operate_a, c_inf_fr_operate_a,' \
                 ' c_paid_goods_s, c_paid_to_for_empl, c_paid_for_taxes, n_incr_clt_loan_adv, n_incr_dep_cbob,' \
                 ' c_pay_claims_orig_inco, pay_handling_chrg, pay_comm_insur_plcy, oth_cash_pay_oper_act,' \
                 ' st_cash_out_act, n_cashflow_act, oth_recp_ral_inv_act, c_disp_withdrwl_invest,' \
                 ' c_recp_return_invest, n_recp_disp_fiolta, n_recp_disp_sobu, stot_inflows_inv_act,' \
                 ' c_pay_acq_const_fiolta, c_paid_invest, n_disp_subs_oth_biz, oth_pay_ral_inv_act,' \
                 ' n_incr_pledge_loan, stot_out_inv_act, n_cashflow_inv_act, c_recp_borrow, proc_issue_bonds,' \
                 ' oth_cash_recp_ral_fnc_act, stot_cash_in_fnc_act, free_cashflow, c_prepay_amt_borr,' \
                 ' c_pay_dist_dpcp_int_exp, incl_dvd_profit_paid_sc_ms, oth_cashpay_ral_fnc_act,' \
                 ' stot_cashout_fnc_act, n_cash_flows_fnc_act, eff_fx_flu_cash, n_incr_cash_cash_equ,' \
                 ' c_cash_equ_beg_period, c_cash_equ_end_period, c_recp_cap_contrib, incl_cash_rec_saims,' \
                 ' uncon_invest_loss, prov_depr_assets, depr_fa_coga_dpba, amort_intang_assets,' \
                 ' lt_amort_deferred_exp, decr_deferred_exp, incr_acc_exp, loss_disp_fiolta, loss_scr_fa,' \
                 ' loss_fv_chg, invest_loss, decr_def_inc_tax_assets, incr_def_inc_tax_liab, decr_inventories,' \
                 ' decr_oper_payable, incr_oper_payable, others, im_net_cashflow_oper_act, conv_debt_into_cap,' \
                 ' conv_copbonds_due_within_1y, fa_fnc_leases, im_n_incr_cash_equ, net_dism_capital_add,' \
                 ' net_cash_rece_sec, credit_impa_loss, use_right_asset_dep, oth_loss_asset, end_bal_cash,' \
                 ' beg_bal_cash, end_bal_cash_equ, beg_bal_cash_equ, update_flag'
    if isinstance(share, list):
        share = list_to_str_format(share)
    if isinstance(fields, list):
        fields = list_to_str_format(fields)
    pro = ts.pro_api()
    start = regulate_date_format(start)
    end = regulate_date_format(end)
    res = pro.cashflow(ts_code=share,
                       ann_date=rpt_date,
                       start_date=start,
                       end_date=end,
                       period=period,
                       report_type=report_type,
                       comp_type=comp_type,
                       fields=fields)
    return res


@retry(Exception)
def indicators(share: str,
               rpt_date: str = None,
               start: str = None,
               end: str = None,
               period: str = None,
               fields: [str, list] = None) -> pd.DataFrame:
    """ 获取上市公司财务数据——财务指标

    :param share: str, TS股票代码,e.g. 600001.SH/000001.SZ
    :param rpt_date: str, 公告日期
    :param start: str, 报告期开始日期
    :param end: str, 报告期结束日期
    :param period: str, 报告期(每个季度最后一天的日期,比如20171231表示年报)
    :param fields: str, 输出数据字段，结果DataFrame的数据列名，用逗号分隔
    :return: pd.DataFrame
        column                      type    default description
        ts_code				        str	    Y	TS代码
        ann_date			        str	    Y	公告日期
        end_date			        str	    Y	报告期
        eps				            float	Y	基本每股收益
        dt_eps				        float	Y	稀释每股收益
        total_revenue_ps		    float	Y	每股营业总收入
        revenue_ps			        float	Y	每股营业收入
        capital_rese_ps			    float	Y	每股资本公积
        surplus_rese_ps			    float	Y	每股盈余公积
        undist_profit_ps		    float	Y	每股未分配利润
        extra_item			        float	Y	非经常性损益
        profit_dedt			        float	Y	扣除非经常性损益后的净利润
        gross_margin			    float	Y	毛利
        current_ratio			    float	Y	流动比率
        quick_ratio			        float	Y	速动比率
        cash_ratio			        float	Y	保守速动比率
        invturn_days			    float	N	存货周转天数
        arturn_days			        float	N	应收账款周转天数
        inv_turn			        float	N	存货周转率
        ar_turn				        float	Y	应收账款周转率
        ca_turn				        float	Y	流动资产周转率
        fa_turn				        float	Y	固定资产周转率
        assets_turn			        float	Y	总资产周转率
        op_income			        float	Y	经营活动净收益
        valuechange_income		    float	N	价值变动净收益
        interst_income			    float	N	利息费用
        daa				            float	N	折旧与摊销
        ebit				        float	Y	息税前利润
        ebitda				        float	Y	息税折旧摊销前利润
        fcff				        float	Y	企业自由现金流量
        fcfe				        float	Y	股权自由现金流量
        current_exint			    float	Y	无息流动负债
        noncurrent_exint		    float	Y	无息非流动负债
        interestdebt			    float	Y	带息债务
        netdebt				        float	Y	净债务
        tangible_asset			    float	Y	有形资产
        working_capital			    float	Y	营运资金
        networking_capital		    float	Y	营运流动资本
        invest_capital			    float	Y	全部投入资本
        retained_earnings		    float	Y	留存收益
        diluted2_eps			    float	Y	期末摊薄每股收益
        bps				            float	Y	每股净资产
        ocfps				        float	Y	每股经营活动产生的现金流量净额
        retainedps			        float	Y	每股留存收益
        cfps				        float	Y	每股现金流量净额
        ebit_ps				        float	Y	每股息税前利润
        fcff_ps				        float	Y	每股企业自由现金流量
        fcfe_ps				        float	Y	每股股东自由现金流量
        netprofit_margin		    float	Y	销售净利率
        grossprofit_margin		    float	Y	销售毛利率
        cogs_of_sales			    float	Y	销售成本率
        expense_of_sales		    float	Y	销售期间费用率
        profit_to_gr			    float	Y	净利润/营业总收入
        saleexp_to_gr			    float	Y	销售费用/营业总收入
        adminexp_of_gr			    float	Y	管理费用/营业总收入
        finaexp_of_gr			    float	Y	财务费用/营业总收入
        impai_ttm			        float	Y	资产减值损失/营业总收入
        gc_of_gr			        float	Y	营业总成本/营业总收入
        op_of_gr			        float	Y	营业利润/营业总收入
        ebit_of_gr			        float	Y	息税前利润/营业总收入
        roe				            float	Y	净资产收益率
        roe_waa				        float	Y	加权平均净资产收益率
        roe_dt				        float	Y	净资产收益率(扣除非经常损益)
        roa				            float	Y	总资产报酬率
        npta				        float	Y	总资产净利润
        roic				        float	Y	投入资本回报率
        roe_yearly			        float	Y	年化净资产收益率
        roa2_yearly			        float	Y	年化总资产报酬率
        roe_avg				        float	N	平均净资产收益率(增发条件)
        opincome_of_ebt			    float	N	经营活动净收益/利润总额
        investincome_of_ebt		    float	N	价值变动净收益/利润总额
        n_op_profit_of_ebt		    float	N	营业外收支净额/利润总额
        tax_to_ebt			        float	N	所得税/利润总额
        dtprofit_to_profit		    float	N	扣除非经常损益后的净利润/净利润
        salescash_to_or			    float	N	销售商品提供劳务收到的现金/营业收入
        ocf_to_or			        float	N	经营活动产生的现金流量净额/营业收入
        ocf_to_opincome			    float	N	经营活动产生的现金流量净额/经营活动净收益
        capitalized_to_da		    float	N	资本支出/折旧和摊销
        debt_to_assets			    float	Y	资产负债率
        assets_to_eqt			    float	Y	权益乘数
        dp_assets_to_eqt		    float	Y	权益乘数(杜邦分析)
        ca_to_assets			    float	Y	流动资产/总资产
        nca_to_assets			    float	Y	非流动资产/总资产
        tbassets_to_totalassets		float	Y	有形资产/总资产
        int_to_talcap			    float	Y	带息债务/全部投入资本
        eqt_to_talcapital		    float	Y	归属于母公司的股东权益/全部投入资本
        currentdebt_to_debt		    float	Y	流动负债/负债合计
        longdeb_to_debt			    float	Y	非流动负债/负债合计
        ocf_to_shortdebt		    float	Y	经营活动产生的现金流量净额/流动负债
        debt_to_eqt			        float	Y	产权比率
        eqt_to_debt			        float	Y	归属于母公司的股东权益/负债合计
        eqt_to_interestdebt		    float	Y	归属于母公司的股东权益/带息债务
        tangibleasset_to_debt		float	Y	有形资产/负债合计
        tangasset_to_intdebt		float	Y	有形资产/带息债务
        tangibleasset_to_netdebt	float	Y	有形资产/净债务
        ocf_to_debt			        float	Y	经营活动产生的现金流量净额/负债合计
        ocf_to_interestdebt		    float	N	经营活动产生的现金流量净额/带息债务
        ocf_to_netdebt			    float	N	经营活动产生的现金流量净额/净债务
        ebit_to_interest		    float	N	已获利息倍数(EBIT/利息费用)
        longdebt_to_workingcapital	float	N	长期债务与营运资金比率
        ebitda_to_debt			    float	N	息税折旧摊销前利润/负债合计
        turn_days			        float	Y	营业周期
        roa_yearly			        float	Y	年化总资产净利率
        roa_dp				        float	Y	总资产净利率(杜邦分析)
        fixed_assets			    float	Y	固定资产合计
        profit_prefin_exp		    float	N	扣除财务费用前营业利润
        non_op_profit			    float	N	非营业利润
        op_to_ebt			        float	N	营业利润／利润总额
        nop_to_ebt			        float	N	非营业利润／利润总额
        ocf_to_profit			    float	N	经营活动产生的现金流量净额／营业利润
        cash_to_liqdebt			    float	N	货币资金／流动负债
        cash_to_liqdebt_withinterest	float	N	货币资金／带息流动负债
        op_to_liqdebt			    float	N	营业利润／流动负债
        op_to_debt			        float	N	营业利润／负债合计
        roic_yearly			        float	N	年化投入资本回报率
        total_fa_trun			    float	N	固定资产合计周转率
        profit_to_op			    float	Y	利润总额／营业收入
        q_opincome			        float	N	经营活动单季度净收益
        q_investincome			    float	N	价值变动单季度净收益
        q_dtprofit			        float	N	扣除非经常损益后的单季度净利润
        q_eps				        float	N	每股收益(单季度)
        q_netprofit_margin		    float	N	销售净利率(单季度)
        q_gsprofit_margin		    float	N	销售毛利率(单季度)
        q_exp_to_sales			    float	N	销售期间费用率(单季度)
        q_profit_to_gr			    float	N	净利润／营业总收入(单季度)
        q_saleexp_to_gr			    float	Y	销售费用／营业总收入 (单季度)
        q_adminexp_to_gr		    float	N	管理费用／营业总收入 (单季度)
        q_finaexp_to_gr			    float	N	财务费用／营业总收入 (单季度)
        q_impair_to_gr_ttm		    float	N	资产减值损失／营业总收入(单季度)
        q_gc_to_gr			        float	Y	营业总成本／营业总收入 (单季度)
        q_op_to_gr			        float	N	营业利润／营业总收入(单季度)
        q_roe				        float	Y	净资产收益率(单季度)
        q_dt_roe			        float	Y	净资产单季度收益率(扣除非经常损益)
        q_npta				        float	Y	总资产净利润(单季度)
        q_opincome_to_ebt		    float	N	经营活动净收益／利润总额(单季度)
        q_investincome_to_ebt		float	N	价值变动净收益／利润总额(单季度)
        q_dtprofit_to_profit		float	N	扣除非经常损益后的净利润／净利润(单季度)
        q_salescash_to_or		    float	N	销售商品提供劳务收到的现金／营业收入(单季度)
        q_ocf_to_sales			    float	Y	经营活动产生的现金流量净额／营业收入(单季度)
        q_ocf_to_or			        float	N	经营活动产生的现金流量净额／经营活动净收益(单季度)
        basic_eps_yoy			    float	Y	基本每股收益同比增长率(%)
        dt_eps_yoy			        float	Y	稀释每股收益同比增长率(%)
        cfps_yoy			        float	Y	每股经营活动产生的现金流量净额同比增长率(%)
        op_yoy				        float	Y	营业利润同比增长率(%)
        ebt_yoy				        float	Y	利润总额同比增长率(%)
        netprofit_yoy			    float	Y	归属母公司股东的净利润同比增长率(%)
        dt_netprofit_yoy		    float	Y	归属母公司股东的净利润-扣除非经常损益同比增长率(%)
        ocf_yoy				        float	Y	经营活动产生的现金流量净额同比增长率(%)
        roe_yoy				        float	Y	净资产收益率(摊薄)同比增长率(%)
        bps_yoy				        float	Y	每股净资产相对年初增长率(%)
        assets_yoy			        float	Y	资产总计相对年初增长率(%)
        eqt_yoy				        float	Y	归属母公司的股东权益相对年初增长率(%)
        tr_yoy				        float	Y	营业总收入同比增长率(%)
        or_yoy				        float	Y	营业收入同比增长率(%)
        q_gr_yoy			        float	N	营业总收入同比增长率(%)(单季度)
        q_gr_qoq			        float	N	营业总收入环比增长率(%)(单季度)
        q_sales_yoy			        float	Y	营业收入同比增长率(%)(单季度)
        q_sales_qoq			        float	N	营业收入环比增长率(%)(单季度)
        q_op_yoy			        float	N	营业利润同比增长率(%)(单季度)
        q_op_qoq			        float	Y	营业利润环比增长率(%)(单季度)
        q_profit_yoy		    	float	N	净利润同比增长率(%)(单季度)
        q_profit_qoq			    float	N	净利润环比增长率(%)(单季度)
        q_netprofit_yoy			    float	N	归属母公司股东的净利润同比增长率(%)(单季度)
        q_netprofit_qoq			    float	N	归属母公司股东的净利润环比增长率(%)(单季度)
        equity_yoy			        float	Y	净资产同比增长率
        rd_exp				        float	N	研发费用
        update_flag			        str	    N	更新标识
    example:
        indicator(ts_code='600000.SH', fields = 'ts_code,ann_date,eps,dt_eps,total_revenue_ps,revenue_ps')
    output:
              ts_code  ann_date    eps  dt_eps  total_revenue_ps  revenue_ps
        0   600000.SH  20191030  1.620    1.62            4.9873      4.9873
        1   600000.SH  20190824  1.070    1.07            3.3251      3.3251
        2   600000.SH  20190430  0.530    0.53            1.7063      1.7063
        3   600000.SH  20190326  1.850    1.85            5.8443      5.8443
        4   600000.SH  20181031  1.440    1.44            4.3305      4.3305
    """
    if fields is None:
        fields = 'ts_code, ann_date, end_date, eps, dt_eps, total_revenue_ps, revenue_ps, capital_rese_ps,' \
                 ' surplus_rese_ps, undist_profit_ps, extra_item, profit_dedt, gross_margin, current_ratio,' \
                 ' quick_ratio, cash_ratio, invturn_days, arturn_days, inv_turn, ar_turn, ca_turn, fa_turn,' \
                 ' assets_turn, op_income, valuechange_income, interst_income, daa, ebit, ebitda, fcff, fcfe,' \
                 ' current_exint, noncurrent_exint, interestdebt, netdebt, tangible_asset, working_capital,' \
                 ' networking_capital, invest_capital, retained_earnings, diluted2_eps, bps, ocfps, retainedps, cfps,' \
                 ' ebit_ps, fcff_ps, fcfe_ps, netprofit_margin, grossprofit_margin, cogs_of_sales, expense_of_sales,' \
                 ' profit_to_gr, saleexp_to_gr, adminexp_of_gr, finaexp_of_gr, impai_ttm, gc_of_gr, op_of_gr,' \
                 ' ebit_of_gr, roe, roe_waa, roe_dt, roa, npta, roic, roe_yearly, roa2_yearly, roe_avg,' \
                 ' opincome_of_ebt, investincome_of_ebt, n_op_profit_of_ebt, tax_to_ebt, dtprofit_to_profit,' \
                 ' salescash_to_or, ocf_to_or, ocf_to_opincome, capitalized_to_da, debt_to_assets, assets_to_eqt,' \
                 ' dp_assets_to_eqt, ca_to_assets, nca_to_assets, tbassets_to_totalassets, int_to_talcap,' \
                 ' eqt_to_talcapital, currentdebt_to_debt, longdeb_to_debt, ocf_to_shortdebt, debt_to_eqt,' \
                 ' eqt_to_debt, eqt_to_interestdebt, tangibleasset_to_debt, tangasset_to_intdebt,' \
                 ' tangibleasset_to_netdebt, ocf_to_debt, ocf_to_interestdebt, ocf_to_netdebt, ebit_to_interest,' \
                 ' longdebt_to_workingcapital, ebitda_to_debt, turn_days, roa_yearly, roa_dp, fixed_assets,' \
                 ' profit_prefin_exp, non_op_profit, op_to_ebt, nop_to_ebt, ocf_to_profit, cash_to_liqdebt,' \
                 ' cash_to_liqdebt_withinterest, op_to_liqdebt, op_to_debt, roic_yearly, total_fa_trun,' \
                 ' profit_to_op, q_opincome, q_investincome, q_dtprofit, q_eps, q_netprofit_margin,' \
                 ' q_gsprofit_margin, q_exp_to_sales, q_profit_to_gr, q_saleexp_to_gr, q_adminexp_to_gr,' \
                 ' q_finaexp_to_gr, q_impair_to_gr_ttm, q_gc_to_gr, q_op_to_gr, q_roe, q_dt_roe, q_npta,' \
                 ' q_opincome_to_ebt, q_investincome_to_ebt, q_dtprofit_to_profit, q_salescash_to_or, q_ocf_to_sales,' \
                 ' q_ocf_to_or, basic_eps_yoy, dt_eps_yoy, cfps_yoy, op_yoy, ebt_yoy, netprofit_yoy,' \
                 ' dt_netprofit_yoy, ocf_yoy, roe_yoy, bps_yoy, assets_yoy, eqt_yoy, tr_yoy, or_yoy, q_gr_yoy,' \
                 ' q_gr_qoq, q_sales_yoy, q_sales_qoq, q_op_yoy, q_op_qoq, q_profit_yoy, q_profit_qoq,' \
                 ' q_netprofit_yoy, q_netprofit_qoq, equity_yoy, rd_exp, update_flag'
    if isinstance(share, list):
        share = list_to_str_format(share)
    if isinstance(fields, list):
        fields = list_to_str_format(fields)
    pro = ts.pro_api()
    res = pro.fina_indicator(ts_code=share,
                             ann_date=rpt_date,
                             start_date=start,
                             end_date=end,
                             period=period,
                             fields=fields)
    return res


@retry(Exception)
def forecast(share: str,
             ann_date: str,
             start: str,
             end: str,
             period: str,
             type: str):
    """ 获取上市公司的业绩预报

    :param share:
    :param ann_date:
    :param start:
    :param end:
    :param period:
    :param type:
    :return:
    DataFrame:
    column          type    description
    ts_code		    str	    TS股票代码
    ann_date	    str	    公告日期
    end_date	    str	    报告期
    type		    str	    业绩预告类型(预增/预减/扭亏/首亏/续亏/续盈/略增/略减)
    p_change_min	float	预告净利润变动幅度下限（%）
    p_change_max	float	预告净利润变动幅度上限（%）
    net_profit_min	float	预告净利润下限（万元）
    net_profit_max	float	预告净利润上限（万元）
    last_parent_net	float	上年同期归属母公司净利润
    first_ann_date	str	    首次公告日
    summary		    str	    业绩预告摘要
    change_reason	str	    业绩变动原因

    """
    fields = 'ts_code, ann_date, end_date, type, p_change_min, p_change_max, net_profit_min, net_profit_max,' \
             ' last_parent_net, first_ann_date, summary, change_reason'
    pro = ts.pro_api()
    try:
        return pro.forecast_vip(ts_code=share,
                                ann_date=ann_date,
                                start_date=start,
                                end_date=end,
                                period=period,
                                type=type,
                                fields=fields)
    except Exception as e:
        return pro.forecast(ts_code=share,
                            ann_date=ann_date,
                            start_date=start,
                            end_date=end,
                            period=period,
                            type=type,
                            fields=fields)


@retry(Exception)
def express(share: str,
            ann_date: str,
            start: str,
            end: str,
            period: str):
    """ 获取上市公司的业绩快报

    :param share:
    :param ann_date:
    :param start:
    :param end:
    :param period:
    :return:
    DataFrame:
    column              type        description
    ts_code		        str	        TS股票代码
    ann_date	        str	        公告日期
    end_date	        str	        报告期
    revenue		        float	    营业收入(元)
    operate_profit	    float	    营业利润(元)
    total_profit	    float	    利润总额(元)
    n_income	        float	    净利润(元)
    total_assets	    float	    总资产(元)
    total_hldr_eqy_
    exc_min_int	        float	    股东权益合计(不含少数股东权益)(元)
    diluted_eps	        float	    每股收益(摊薄)(元)
    diluted_roe	        float	    净资产收益率(摊薄)(%)
    yoy_net_profit	    float	    去年同期修正后净利润
    bps		            float	    每股净资产
    yoy_sales	        float	    同比增长率:营业收入
    yoy_op		        float	    同比增长率:营业利润
    yoy_tp		        float	    同比增长率:利润总额
    yoy_dedu_np	        float	    同比增长率:归属母公司股东的净利润
    yoy_eps		        float	    同比增长率:基本每股收益
    yoy_roe		        float	    同比增减:加权平均净资产收益率
    growth_assets	    float	    比年初增长率:总资产
    yoy_equity	        float	    比年初增长率:归属母公司的股东权益
    growth_bps	        float	    比年初增长率:归属于母公司股东的每股净资产
    or_last_year	    float	    去年同期营业收入
    op_last_year	    float	    去年同期营业利润
    tp_last_year	    float	    去年同期利润总额
    np_last_year	    float	    去年同期净利润
    eps_last_year	    float	    去年同期每股收益
    open_net_assets	    float	    期初净资产
    open_bps	        float	    期初每股净资产
    perf_summary	    str	        业绩简要说明
    is_audit	        int	        是否审计： 1是 0否
    remark		        str	        备注
    """
    fields = 'ts_code, ann_date, end_date, revenue, operate_profit, total_profit, n_income, total_assets, ' \
             'total_hldr_eqy_exc_min_int, diluted_eps, diluted_roe, yoy_net_profit, bps, yoy_sales, yoy_op,' \
             ' yoy_tp, yoy_dedu_np, yoy_eps, yoy_roe, growth_assets, yoy_equity, growth_bps, or_last_year,' \
             ' op_last_year, tp_last_year, np_last_year, eps_last_year, open_net_assets, open_bps, perf_summary,' \
             ' is_audit, remark'
    pro = ts.pro_api()
    try:
        return pro.express_vip(ts_code=share,
                               ann_date=ann_date,
                               start_date=start,
                               end_date=end,
                               period=period,
                               fields=fields)
    except Exception as e:
        return pro.express(ts_code=share,
                           ann_date=ann_date,
                           start_date=start,
                           end_date=end,
                           period=period,
                           fields=fields)


# Market Data
# =================
@retry(Exception)
def top_list(trade_date: str = None,
             shares: str = None,
             fields: str = None) -> pd.DataFrame:
    """ 龙虎榜每日交易明细，2005年至今全部历史数据，单次获取数量不超过10000

    :param trade_date: str, 交易日期
    :param shares: str, 股票代码
    :param fields: str, 输出数据字段，结果DataFrame的数据列名，用逗号分隔
    :return: pd.DataFrame
        column                      type    default description
        trade_date	                str	    Y	    交易日期
        ts_code		                str	    Y	    TS代码
        name		                str	    Y	    名称
        close		                float	Y	    收盘价
        pct_change	                float	Y	    涨跌幅
        turnover_rate	            float	Y	    换手率
        amount		                float	Y	    总成交额
        l_sell		                float	Y	    龙虎榜卖出额
        l_buy		                float	Y	    龙虎榜买入额
        l_amount	                float	Y	    龙虎榜成交额
        net_amount	                float	Y	    龙虎榜净买入额
        net_rate	                float	Y	    龙虎榜净买额占比
        amount_rate	                float	Y	    龙虎榜成交额占比
        float_values	            float	Y	    当日流通市值
        reason		                str	    Y	    上榜理由
    example:
        top_list(trade_date='20180928', fields='trade_date,ts_code,name,close')
    output:
           trade_date    ts_code  name   close
        0    20180928  000007.SZ   全新好   7.830
        1    20180928  000017.SZ  深中华A   4.660
        2    20180928  000505.SZ  京粮控股   5.750
        3    20180928  000566.SZ  海南海药   6.120
        4    20180928  000593.SZ  大通燃气   7.990
        ...
    """
    if fields is None:
        fields = 'trade_date,ts_code,name,close,l_sell,l_buy,l_amount,float_values,reason'
    pro = ts.pro_api()
    return pro.top_list(trade_date=trade_date,
                        ts_code=shares,
                        fields=fields)


# Index Data
# ==================
@retry(Exception)
def index_basic(index: str = None,
                name: str = None,
                market: str = None,
                publisher: str = None,
                category: str = None) -> pd.DataFrame:
    """ 获取大盘指数的基本信息如名称代码等

    :param index: 指数代码
    :param name: 指数简称
    :param market: 交易所或服务商(默认SSE)，包括：
                    MSCI:    MSCI指数
                    CSI:     中证指数
                    SSE:     上交所指数
                    SZSE:    深交所指数
                    CICC:    中金指数
                    SW:      申万指数
                    OTH:     其他指数
    :param publisher: 发布商
    :param category: 指数类别
    :return: pd.DataFrame
        column          type    description
        ts_code	        str	    TS代码
        name	        str	    简称
        fullname	    str	    指数全称
        market	        str	    市场
        publisher	    str	    发布方
        index_type	    str	    指数风格
        category	    str	    指数类别
        base_date	    str	    基期
        base_point	    float	基点
        list_date	    str	    发布日期
        weight_rule	    str	    加权方式
        desc	        str	    描述
        exp_date	    str	    终止日期
    example:
        index_basic(market='SW')
    output:
               ts_code    name         market     publisher   category     base_date  base_point  \
                5         801010.SI    农林牧渔        SW申万       一级行业指数      19991230      1000.0
                6         801011.SI    林业Ⅱ          SW申万         二级行业指数  19991230      1000.0
                7         801012.SI    农产品加工      SW申万      二级行业指数  19991230      1000.0
                8         801013.SI    农业综合Ⅱ       SW申万      二级行业指数  19991230      1000.0
                9         801014.SI    饲料Ⅱ          SW申万       二级行业指数  19991230      1000.0
                10        801015.SI    渔业           SW申万       二级行业指数  19991230      1000.0
                11        801016.SI    种植业         SW申万      二级行业指数  19991230      1000.0
                12        801017.SI    畜禽养殖Ⅱ       SW申万       二级行业指数  20111010      1000.0
                13        801018.SI    动物保健Ⅱ       SW申万研     二级行业指数  19991230      1000.0
                14        801020.SI    采掘           SW申万     一级行业指数  19991230      1000.0
                15        801021.SI    煤炭开采Ⅱ       SW申万      二级行业指数  19991230      1000.0
                16        801022.SI    其他采掘Ⅱ       SW申万      二级行业指数  19991230      1000.0
                17        801023.SI    石油开采Ⅱ       SW申万      二级行业指数  19991230      1000.0
                18        801024.SI    采掘服务Ⅱ       SW申万      二级行业指数  19991230      1000.0
    """
    fields = 'ts_code, name, fullname, market, publisher, index_type, category, ' \
             'base_date, base_point, list_date, weight_rule, desc, exp_date'
    pro = ts.pro_api()
    return pro.index_basic(ts_code=index,
                           name=name,
                           market=market,
                           publisher=publisher,
                           category=category,
                           fields=fields)


@retry(Exception, mute=True)
def index_indicators(trade_date: str = None,
                     index: str = None,
                     start: str = None,
                     end: str = None,
                     fields: str = None) -> pd.DataFrame:
    """ 大盘指数每日指标如市盈率等, 目前只提供上证综指，深证成指，上证50，中证500，中小板指，创业板指的每日指标数据
        支持两三种数据获取方式：
            1，给定特定的trade_date和index，获取当天的指定index的数据
            2，给定特定的trade_date，获取当天所有index的数据
            3，给定特定的index，并指定start和end，获取指定指数在历史区间中的每天的数据

    :param trade_date: str, 交易日期 （格式：YYYYMMDD，比如20181018，下同）
    :param index: str, TS代码
    :param start: str, 开始日期
    :param end: str, 结束日期
    :param fields: str, 输出数据字段，结果DataFrame的数据列名，用逗号分隔
    :return:
        column          type    default description
        ts_code		    str	    Y	    TS代码
        trade_date	    str	    Y	    交易日期
        total_mv	    float	Y	    当日总市值（元）
        float_mv	        float	Y	    当日流通市值（元）
        total_share     float	Y	    当日总股本（股）
        float_share	    float	Y	    当日流通股本（股）
        free_share	    float	Y	    当日自由流通股本（股）
        turnover_rate	float	Y	    换手率
        turnover_rate_f	float	Y	    换手率(基于自由流通股本)
        pe		        float	Y	    市盈率
        pe_ttm		    float	Y	    市盈率TTM
        pb		        float	Y	    市净率
    example:
        index_indicators(trade_date='20181018', fields='ts_code,trade_date,turnover_rate,pe')
    output:
            ts_code  trade_date  turnover_rate     pe
        0  000001.SH   20181018           0.38  11.92
        1  000300.SH   20181018           0.27  11.17
        2  000905.SH   20181018           0.82  18.03
        3  399001.SZ   20181018           0.88  17.48
        4  399005.SZ   20181018           0.85  21.43
        5  399006.SZ   20181018           1.50  29.56
        6  399016.SZ   20181018           1.06  18.86
        7  399300.SZ   20181018           0.27  11.17
    """
    if fields is None:
        fields = 'ts_code,trade_date,turnover_rate,pe,pe_ttm,pb'
    pro = ts.pro_api()
    return pro.index_dailybasic(trade_date=trade_date,
                                ts_code=index,
                                start_date=start,
                                end_date=end,
                                fields=fields)


@retry(Exception)
def composite(index: str = None,
              trade_date: str = None,
              start: str = None,
              end: str = None) -> pd.DataFrame:
    """ 获取各类指数成分和权重，月度数据 ，如需日度指数成分和权重，请联系 waditu@163.com

    :param index: str, 指数代码 (二选一)
    :param trade_date: str, 交易日期 （二选一）
    :param start: str, 开始日期
    :param end: str, 结束日期
    :return: pd.DataFrame
        column      type    description
        index_code	str	    指数代码
        con_code	str	    成分代码
        trade_date	str	    交易日期
        weight	 	float	权重
    example:
        composite(index_code='399300.SZ', start='20180901', end='20180930')
    output:
            index_code   con_code trade_date  weight
        0    399300.SZ  000001.SZ   20180903  0.8656
        1    399300.SZ  000002.SZ   20180903  1.1330
        2    399300.SZ  000060.SZ   20180903  0.1125
        3    399300.SZ  000063.SZ   20180903  0.4273
        4    399300.SZ  000069.SZ   20180903  0.2010
        5    399300.SZ  000157.SZ   20180903  0.1699
        6    399300.SZ  000402.SZ   20180903  0.0816
    """
    pro = ts.pro_api()
    return pro.index_weight(index_code=index,
                            trade_date=trade_date,
                            start_date=start,
                            end_date=end)


# Funds Data
# =============

@retry(Exception)
def fund_basic(market: str = None,
               status: str = None) -> pd.DataFrame:
    """ 获取基金列表

    :param market: str, 交易市场: E场内 O场外（默认E）
    :param status: str, 存续状态 D摘牌 I发行 L上市中
    :return: pd.DataFrame
        column          type    default     description
        ts_code		    str	      Y	        基金代码
        name		    str	      Y	        简称
        management	    str	      Y	        管理人
        custodian	    str	      Y	        托管人
        fund_type	    str	      Y	        投资类型
        found_date	    str	      Y	        成立日期
        due_date	    str	      Y	        到期日期
        list_date	    str	      Y	        上市时间
        issue_date	    str	      Y	        发行日期
        delist_date	    str	      Y	        退市日期
        issue_amount	float	  Y	        发行份额(亿)
        m_fee		    float	  Y	        管理费
        c_fee		    float	  Y	        托管费
        duration_year	float	  Y	        存续期
        p_value		    float	  Y	        面值
        min_amount	    float	  Y	        起点金额(万元)
        exp_return	    float	  Y	        预期收益率
        benchmark	    str	      Y	        业绩比较基准
        status		    str	      Y	        存续状态D摘牌 I发行 L已上市
        invest_type	    str	      Y	        投资风格
        type		    str	      Y	        基金类型
        trustee		    str	      Y	        受托人
        purc_startdate	str	      Y	        日常申购起始日
        redm_startdate	str	      Y	        日常赎回起始日
        market		    str	      Y	        E场内O场外

    example:
        fund_basic(market='E')
    output:
            ts_code        	name         		management	custodian      fund_type 	found_date
        1     512850.SH    	中信建投北京50ETF     中信建投基金   招商银行       	股票型   	20180927
        2     168601.SZ    	汇安裕阳三年定期开放    汇安基金    	中国光大银行   	混合型   	20180927
        3     512860.SH    	华安中国A股ETF       	华安基金    	中国农业银行  	股票型   	20180927
        4     159960.SZ    	恒生国企     		    平安大华基金  中国银行       	股票型   	20180921
        5     501062.SH    	南方瑞合三年       	南方基金    	中国建设银行   	混合型   	20180906
        6     510600.SH    	沪50ETF     		申万菱信基金  中国工商银行    	股票型   	20180903
        7     501061.SH    	金选300C       		中金基金    	中国建设银行    	股票型   	20180830
        8     501060.SH    	金选300A       		中金基金    	中国建设银行 	    股票型   	20180830
        9     166802.SZ     浙商300       		浙商基金      华夏银行    	    股票型   	20180820
        ...                                     ...                                     ...
    """
    if market is None:
        market = 'E'
    pro = ts.pro_api()
    return pro.fund_basic(market=market,
                          status=status)


@retry(Exception)
def fund_net_value(fund: str = None,
                   trade_date: str = None,
                   market: str = None) -> pd.DataFrame:
    """ 获取公募基金净值数据

    :param fund: str, TS基金代码 （二选一）如果可用，给出该基金的历史净值记录
    :param trade_date: str, 净值日期 （二选一）如果可用，给出该日期所有基金的净值记录
    :param market: str, 交易市场类型: E场内 O场外
    :return: pd.DataFrame
        column          type  default   description
        ts_code		    str	    Y	    TS代码
        nav_date	    str	    Y	    净值日期
        ann_date	    str	    Y      	公告日期
        unit_nav	    float	Y	    单位净值
        accum_nav	    float	Y	    累计净值
        accum_div	    float	Y   	累计分红
        net_asset	    float	Y   	资产净值
        total_netasset	float	Y   	合计资产净值
        adj_nav		    float	Y   	复权单位净值
    example:
        fund_neg_value(ts_code='165509.SZ', fields='ts_code, adj_nav')
    output:
        ts_code   adj_nav
        0     165509.SZ  1.827306
        1     165509.SZ  1.811019
        2     165509.SZ  1.815905
        3     165509.SZ  1.801248
        4     165509.SZ  1.835449
        ...         ...       ...
    """
    pro = ts.pro_api()
    return pro.fund_nav(ts_code=fund,
                        nav_date=trade_date,
                        market=market)


# Futures & Options Data
# ===============

@retry(Exception)
def future_basic(exchange: str = None,
                 future_type: str = None) -> pd.DataFrame:
    """ 获取期货合约列表数据

    :param exchange: str, 交易所代码 CFFEX-中金所 DCE-大商所 CZCE-郑商所 SHFE-上期所 INE-上海国际能源交易中心
    :param future_type: str, 合约类型 (1 普通合约 2主力与连续合约 默认取全部)
    :return:
        column          type    default description
        ts_code		    str	    Y	    合约代码
        symbol		    str	    Y	    交易标识
        exchange	    str	    Y	    交易市场
        name		    str	    Y	    中文简称
        fut_code	    str	    Y	    合约产品代码
        multiplier	    float	Y	    合约乘数
        trade_unit	    str	    Y	    交易计量单位
        per_unit	    float	Y	    交易单位(每手)
        quote_unit	    str	    Y	    报价单位
        quote_unit_desc	str	    Y	    最小报价单位说明
        d_mode_desc	    str	    Y	    交割方式说明
        list_date	    str	    Y	    上市日期
        delist_date	    str	    Y	    最后交易日期
        d_month		    str	    Y	    交割月份
        last_ddate	    str	    Y	    最后交割日
        trade_time_desc	str	    N	    交易时间说明
    example:
        future_basic(exchange='DCE', fut_type='1')
    output:
                ts_code  symbol      name   list_date    delist_date
        0      P0805.DCE   P0805   棕榈油0805  20071029    20080516
        1      P0806.DCE   P0806   棕榈油0806  20071029    20080616
        2      P0807.DCE   P0807   棕榈油0807  20071029    20080714
        3      P0808.DCE   P0808   棕榈油0808  20071029    20080814
        4      P0811.DCE   P0811   棕榈油0811  20071115    20081114
        5      P0812.DCE   P0812   棕榈油0812  20071217    20081212
        ...
    """
    if exchange is None:
        exchange = 'CFFEX'
    fields = 'ts_code,symbol,name,fut_code,multiplier,trade_unit,per_unit,quote_unit,quote_unit_desc,d_mode_desc,' \
             'list_date,delist_date,d_month,last_ddate,trade_time_desc'
    pro = ts.pro_api()
    return pro.fut_basic(exchange=exchange,
                         fut_type=future_type,
                         fields=fields)


@retry(Exception)
def options_basic(exchange: str = None,
                  call_put: str = None) -> pd.DataFrame:
    """ 获取期权合约信息

    :param exchange: str, 交易所代码 CFFEX-中金所 DCE-大商所 CZCE-郑商所 SHFE-上期所 INE-上海国际能源交易中心
    :param call_put: str, 期权类型
    :return pd.DataFrame
        column          type    default description
        ts_code		    str	    Y   	TS代码
        exchange	    str 	Y   	交易市场
        name		    str 	Y   	合约名称
        per_unit	    str 	Y   	合约单位
        opt_code    	str 	Y   	标准合约代码
        opt_type    	str 	Y   	合约类型
        call_put    	str 	Y   	期权类型
        exercise_type	str 	Y   	行权方式
        exercise_price	float	Y   	行权价格
        s_month	    	str	    Y   	结算月
        maturity_date	str 	Y   	到期日
        list_price  	float	Y   	挂牌基准价
        list_date   	str 	Y   	开始交易日期
        delist_date 	str 	Y   	最后交易日期
        last_edate  	str 	Y   	最后行权日期
        last_ddate  	str 	Y   	最后交割日期
        quote_unit  	str 	Y   	报价单位
        min_price_chg	str 	Y   	最小价格波幅
    example:
        options_basic(exchange='DCE', fields='ts_code,name,exercise_type,list_date,delist_date')
    output:
                    ts_code                  name             exercise_type list_date delist_date
        0    M1707-C-2400.DCE  豆粕期权1707认购2400            美式  20170605    20170607
        1    M1707-P-2400.DCE  豆粕期权1707认沽2400            美式  20170605    20170607
        2    M1803-P-2550.DCE  豆粕期权1803认沽2550            美式  20170407    20180207
        3    M1707-C-2500.DCE  豆粕期权1707认购2500            美式  20170410    20170607
        4    M1707-P-2500.DCE  豆粕期权1707认沽2500            美式  20170410    20170607
        5    M1803-C-2550.DCE  豆粕期权1803认购2550            美式  20170407    20180207
    """
    fields = 'ts_code,exchange,name,per_unit,opt_code,opt_type,call_put,exercise_type,exercise_price,s_month,' \
             'maturity_date,list_price,list_date,delist_date,last_edate,last_ddate,quote_unit,min_price_chg'
    pro = ts.pro_api()
    return pro.opt_basic(exchange=exchange,
                         call_put=call_put,
                         fields=fields)


@retry(Exception, mute=True)
def future_daily(trade_date: str = None,
                 future: str = None,
                 exchange: str = None,
                 start: str = None,
                 end: str = None) -> pd.DataFrame:
    """ 期货日线行情数据

    :param trade_date: str, 交易日期
    :param future: str, 合约代码
    :param exchange: str, 交易所代码
    :param start: str, 开始日期
    :param end: str, 结束日期
    :return: pd.DataFrame
        column      type    default description
        ts_code		str	    Y	    TS合约代码
        trade_date	str	    Y	    交易日期
        pre_close	float	Y	    昨收盘价
        pre_settle	float	Y   	昨结算价
        open		loat	Y	    开盘价
        high		float	Y   	最高价
        low		    float	Y	    最低价
        close		float	Y	    收盘价
        settle		float	Y	    结算价
        change1		float	Y   	涨跌1 收盘价-昨结算价
        change2		float	Y   	涨跌2 结算价-昨结算价
        vol		    float	Y   	成交量(手)
        amount		float	Y   	成交金额(万元)
        oi		    float	Y   	持仓量(手)
        oi_chg		float	Y   	持仓量变化
        delv_settle	float	N   	交割结算价
    example:
        future_daily(ts_code='CU1811.SHF', start_date='20180101', end_date='20181113')
    output:
                ts_code trade_date  pre_close  pre_settle     open   ...  change2      vol     amount       oi  oi_chg
        0    CU1811.SHF   20181113    48900.0     49030.0  48910.0   ...   -200.0  17270.0  421721.70  16110.0 -6830.0
        1    CU1811.SHF   20181112    49270.0     49340.0  49130.0   ...   -310.0  27710.0  679447.85  22940.0 -7160.0
        2    CU1811.SHF   20181109    49440.0     49500.0  49340.0   ...   -160.0  22530.0  555910.15  30100.0 -4700.0
        3    CU1811.SHF   20181108    49470.0     49460.0  49600.0   ...     40.0  22290.0  551708.00  34800.0 -3530.0
        4    CU1811.SHF   20181107    49670.0     49630.0  49640.0   ...   -170.0  26850.0  664040.10  38330.0 -4560.0
        ..          ...        ...        ...         ...      ...   ...      ...      ...        ...      ...     ...
    """
    if (future is None) and (trade_date is None):
        raise ValueError(f'future code and trade date can not be both None, should provide at least one of them!')
    fields = 'ts_code,trade_date,pre_close,pre_settle,open,high,low,close,' \
             'settle,change1,change2,vol,amount,oi,oi_chg,delv_settle'
    pro = ts.pro_api()
    return pro.fut_daily(trade_date=trade_date,
                         ts_code=future,
                         exchange=exchange,
                         start_date=start,
                         end_date=end,
                         fields=fields)


@retry(Exception, tries=10, mute=True)  # 接口有访问次数限制，因此增加delay
def options_daily(trade_date: str = None,
                  option: str = None,
                  exchange: str = None,
                  start: str = None,
                  end: str = None) -> pd.DataFrame:
    """ 获取期权日线行情

    :param trade_date: str, 交易日期
    :param option: str, 合约代码
    :param exchange: str, 交易所代码
    :param start: str, 开始日期
    :param end: str, 结束日期
    :return: pd.DataFrame
        column      type    default description
        ts_code		str	    Y   	TS代码
        trade_date	str	    Y   	交易日期
        exchange	str	    Y   	交易市场
        pre_settle	float	Y   	昨结算价
        pre_close	float	Y   	前收盘价
        open		float	Y   	开盘价
        high		float	Y   	最高价
        low		    float	Y   	最低价
        close		float	Y   	收盘价
        settle		float	Y   	结算价
        vol		    float	Y   	成交量(手)
        amount		float	Y   	成交金额(万元)
        oi		    float	Y   	持仓量(手)
    example:
        options_daily(trade_date='20181212')
    output:
                  ts_code      trade_date exchange  pre_settle  pre_close     open  \
        0         10001313.SH   20181212      SSE      0.0311     0.0312    0.0355
        1         10001314.SH   20181212      SSE      0.0156     0.0157    0.0170
        2         10001315.SH   20181212      SSE      0.0073     0.0073    0.0076
        3         10001316.SH   20181212      SSE      0.0028     0.0028    0.0029
        4         10001317.SH   20181212      SSE      0.0015     0.0015    0.0015
        5         10001318.SH   20181212      SSE      0.0009     0.0009    0.0009

                 high       low     close    settle     vol       amount       oi
        0      0.0368    0.0293    0.0309    0.0307  3.8354  12614354.72  98882.0
        1      0.0190    0.0142    0.0150    0.0150  1.4472   2349332.88  79980.0
        2      0.0085    0.0060    0.0062    0.0062  1.0092    693117.76  72370.0
        3      0.0042    0.0024    0.0027    0.0027  0.5434    161072.24  55117.0
        4      0.0018    0.0012    0.0013    0.0013  0.4240     57989.19  61746.0
        5      0.0012    0.0008    0.0008    0.0008  0.2067     20700.88  37674.0
    """
    if option is None and trade_date is None:
        raise ValueError(f'one of future and trade_date should be given!')
    fields = 'ts_code,trade_date,pre_close,pre_settle,open,high,low,close,settle,vol,amount,oi'
    pro = ts.pro_api()
    return pro.opt_daily(trade_date=trade_date,
                         ts_code=option,
                         exchange=exchange,
                         start_date=start,
                         end_date=end,
                         fields=fields)
