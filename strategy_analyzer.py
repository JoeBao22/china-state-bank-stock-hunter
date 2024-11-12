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


