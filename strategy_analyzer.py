import pandas as pd
import numpy as np
import sys
import matplotlib.pyplot as plt
from strategy_generator import MAStrategy
from chart import setup_chinese_font, TradeChart, IndicatorDistributionChart


def get_performance_summary(trades):
    """
    获取交易表现摘要
    :param trades: 交易记录, DataFrame
    """
    if len(trades) == 0:
        return {
            'total_trades': 0,
            'win_rate': 0,
            'avg_return': 0,
            'total_return': 0,
            'max_return': 0,
            'min_return': 0,
            'avg_hold_weeks': 0,
            'avg_drawdown': 0,
            'max_drawdown': 0
        }
    win_trades = len(trades[trades['收益率'] > 0])
    total_trades = len(trades)
    trades['持仓周数'] = ((pd.to_datetime(trades['卖出日期']) - 
                            pd.to_datetime(trades['买入日期'])).dt.days / 7).round(1)
    compound_return = np.prod(1 + trades['收益率'] / 100) - 1

    summary = {
        'total_trades': total_trades,
        'win_rate': win_trades / total_trades * 100,
        'avg_return': trades['收益率'].mean(),
        'total_return': compound_return * 100,
        'max_return': trades['收益率'].max(),
        'min_return': trades['收益率'].min(),
        'avg_hold_weeks': trades['持仓周数'].mean(),
        'avg_drawdown': trades['回撤率'].mean(),
        'max_drawdown': trades['回撤率'].min()
    }
    return summary


class Arguments:
    def __init__(self, stock_code, stock_name, start_date, end_date, ratio1, ratio2, period, ma_period, indicator_name):
        self.stock_code = stock_code
        self.stock_name = stock_name
        self.start_date = start_date
        self.end_date = end_date
        self.ratio1 = ratio1
        self.ratio2 = ratio2
        self.period = period
        self.ma_period = ma_period
        self.indicator_name = indicator_name

if __name__ == "__main__":
    from stock_data import StockData
    
    
    args = Arguments(
        stock_code='601288',
        stock_name='农业银行',
        start_date='2018-01-01',
        end_date=None,
        ratio1=1.00,
        ratio2=1.05,
        period='W',
        ma_period=5,
        indicator_name='当前价格/MA5'
    )
    stock_data = StockData(args.stock_code, args.stock_name)

    strategy = MAStrategy(args.ratio1, args.ratio2, args.period, args.ma_period)
    df, signals, trades = strategy.apply_strategy(stock_data, args.start_date, args.end_date)
    
    pd.set_option('display.max_columns', None)
    print("\n交易记录：")
    print(trades)
    
    # 打印策略表现
    print("\n策略表现：")
    summary = get_performance_summary(trades)
    print(f"总交易次数: {summary['total_trades']}")

    # 绘制交易图表
    trade_chart = TradeChart(df, trades, args).plot()
    trade_chart.show()

    # 绘制价格/MA5比值分布
    distribution_chart = IndicatorDistributionChart(df, args).plot()
    distribution_chart.show()
