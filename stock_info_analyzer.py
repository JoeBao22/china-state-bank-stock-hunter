# 筛选条件:
# 1. 1.业绩优良：说得直白一点，连续两到三年业绩都是正数，没有负数指标。

# 2.估值比较低：那你要计算PEG的数值。PEG数值尽量控制在0.35-0.85之间。如果估值太低，要么是真的低估值，要么就是垃圾股。

# 3.市值要小：流通股本10亿股，流通市值300亿以下的股。小股票比较好拉，适合散户小资金。

# 4.查查公司董事长，或者董事局主席，或者控股大股东的能力如何：有没有干劲冲劲，是颓养天年，还是一直滋滋业业；是奋发图强居安思危，还是养尊处优得过且过。

# 这几个不难吧！其实每个股票f10里面都有些介绍，实在没有的，可以去百度里面找。这个办法涵盖了你想的投资还是投机。

# 选好后看什么指标买？

# 1.macd线：要选择白线出海或者临近白线出海的股票。

# 2.KDJ线：要选择三条线交叉抬头向上时的股票。

# 3.趋势向上的股票：从底部开始向上走的股票。

import csv 
import os


def calculate_peg(pe_ratio, growth_rate):
    """
    计算PEG
    pe_ratio: 市盈率
    growth_rate: 增长率(%)
    """
    if growth_rate == 0:
        return float('inf')  # 避免除以0
    return pe_ratio / growth_rate

for i in range(1, 3044):
    file_path = f'./resource/company_info/{str(i).zfill(6)}.csv'
    satisfy = True
    if not os.path.exists(file_path):
        continue
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        headers = next(reader)
        total_shares_index = headers.index('总股本')
        total_market_value_index = headers.index('总市值')
        pe_ratio_index = headers.index('市盈率(静态)')
        growth_rate_index = headers.index('净资产收益率')
        for row in reader:
            total_shares = row[total_shares_index]
            if total_shares == "未公布":
                continue
            # total_shares < 10亿
            total_shares = float(total_shares[:-2])
            if total_shares > 10:
                continue
            total_market_value = row[total_market_value_index]
            if total_market_value == "未公布":
                continue
            total_market_value = float(total_market_value[:-1])
            # total_market_value < 300亿
            if total_market_value > 300:
                continue
            # print(row)
            pe_ratio = row[pe_ratio_index]
            if pe_ratio == "亏损" or pe_ratio == "未公布":
                continue
            # print(pe_ratio)
            pe_ratio = float(pe_ratio)
            growth_rate = row[growth_rate_index]
            if growth_rate == "未公布":
                continue
            # print(growth_rate)
            growth_rate = float(growth_rate[:-1])
            # PEG < 0.85
            peg = calculate_peg(pe_ratio, growth_rate)
            # print("peg:", peg)
            # if peg > 0.85 or peg < 0.35:
            # 考虑现在普遍股票估值偏高，放宽条件:当前中证1000 6000,最低点4177, peg可放宽30%左右
            # 但太便宜的肯定不行
            if peg > 1.105 or peg < 0.35:
                continue
            print(f"股票代码: {str(i).zfill(6)} 符合筛选条件")
            break
            
