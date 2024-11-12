import pandas as pd
import numpy as np
import sys
import matplotlib.pyplot as plt
from strategy_generator import MAStrategy
from chart import setup_chinese_font


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
    def __init__(self, stock_code, stock_name, start_date, end_date, ratio1, ratio2, period, ma_period):
        self.stock_code = stock_code
        self.stock_name = stock_name
        self.start_date = start_date
        self.end_date = end_date
        self.ratio1 = ratio1
        self.ratio2 = ratio2
        self.period = period
        self.ma_period = ma_period

class WeeklyPriceMAStrategy:
    @staticmethod
    def plot_trades(df, trades, args):
        """绘制交易图表"""
        setup_chinese_font()
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 12), height_ratios=[2, 1])

        # 上图：价格和MA10
        ax1.plot(df['日期'], df['收盘'], label='收盘价', color='gray', alpha=0.6)
        ax1.plot(df['日期'], df[f'MA{args.ma_period}'], label=f'MA{args.ma_period}', color='blue', alpha=0.6)

        # 标记买入点和卖出点
        for _, trade in trades.iterrows():
            label_buy = '买入点' if '买入点' not in [l.get_label() for l in ax1.get_lines()] else ""
            label_sell = '卖出点' if '卖出点' not in [l.get_label() for l in ax1.get_lines()] else ""

            ax1.scatter(trade['买入日期'], trade['买入价格'], color='green', marker='^', s=100, label=label_buy)
            ax1.scatter(trade['卖出日期'], trade['卖出价格'], color='red', marker='v', s=100, label=label_sell)

            # 添加收益率标注
            return_text = f"{trade['收益率']:.1f}%"
            ax1.annotate(return_text, 
                        xy=(trade['卖出日期'], trade['卖出价格']),
                        xytext=(10, 10), textcoords='offset points',
                        fontsize=8, color='red' if trade['收益率'] > 0 else 'green')

        # 设置标题，包含日期范围信息
        date_range_str = ""
        if args.start_date and args.end_date:
            date_range_str = f"({args.start_date} 至 {args.end_date})"
        elif args.start_date:
            date_range_str = f"({args.start_date} 之后)"
        elif args.end_date:
            date_range_str = f"({args.end_date} 之前)"

        ax1.set_title(f'{args.stock_name}({args.stock_code}) 周线交易策略 {date_range_str}')
        ax1.set_xlabel('日期')
        ax1.set_ylabel('价格')
        ax1.legend()
        ax1.grid(True)

        # 下图：价格/MA10比值
        ax2.plot(df['日期'], df['PRICE_MA_RATIO'], label=f'价格/MA{args.ma_period}', color='purple')
        ax2.axhline(y=args.ratio1, color='green', linestyle='--', label=f'买入阈值 ({args.ratio1:.2f})')
        ax2.axhline(y=args.ratio2, color='red', linestyle='--', label=f'卖出阈值 ({args.ratio2:.2f})')
        ax2.axhline(y=1, color='gray', linestyle='-', label='均衡线 (1.00)', alpha=0.5)

        # 标记买卖点的比值
        for _, trade in trades.iterrows():
            ax2.scatter(trade['买入日期'], trade[f'买入时指标'], color='green', marker='^', s=100)
            ax2.scatter(trade['卖出日期'], trade[f'卖出时指标'], color='red', marker='v', s=100)

        ax2.set_title(f'价格/MA{args.ma_period}比值变化')
        ax2.set_xlabel('日期')
        ax2.set_ylabel('比值')
        ax2.legend()
        ax2.grid(True)

        plt.tight_layout()
        return plt

    @staticmethod
    def plot_ratio_distribution(df, args, bins=50):
        """
        绘制价格/MA10比值的分布直方图
        :param bins: 直方图的箱数
        """
        setup_chinese_font()
        plt.figure(figsize=(12, 6))

        # 绘制直方图
        ratio_data = df['PRICE_MA_RATIO'].dropna()
        plt.hist(ratio_data, bins=bins, alpha=0.7, color='blue', density=True)

        # 添加买入卖出阈值线
        ylim = plt.gca().get_ylim()
        plt.vlines(args.ratio1, 0, ylim[1], colors='green', linestyles='--', 
                  label=f'买入阈值 ({args.ratio1:.2f})')
        plt.vlines(args.ratio2, 0, ylim[1], colors='red', linestyles='--', 
                  label=f'卖出阈值 ({args.ratio2:.2f})')
        plt.vlines(1, 0, ylim[1], colors='gray', linestyles='-', 
                  label='均衡线 (1.00)', alpha=0.5)

        # 计算并显示统计信息
        mean = ratio_data.mean()
        std = ratio_data.std()
        median = ratio_data.median()
        lower_percentile = np.percentile(ratio_data, 10)
        upper_percentile = np.percentile(ratio_data, 90)

        # 在图上添加统计信息
        stats_text = (f'均值: {mean:.3f}\n'
                     f'中位数: {median:.3f}\n'
                     f'标准差: {std:.3f}\n'
                     f'10%分位数: {lower_percentile:.3f}\n'
                     f'90%分位数: {upper_percentile:.3f}')
        plt.text(0.02, 0.98, stats_text,
                transform=plt.gca().transAxes,
                verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

        # 设置标题，包含日期范围信息
        date_range_str = ""
        if args.start_date and args.end_date:
            date_range_str = f"({args.start_date} 至 {args.end_date})"
        elif args.start_date:
            date_range_str = f"({args.start_date} 之后)"
        elif args.end_date:
            date_range_str = f"({args.end_date} 之前)"

        plt.title(f'{args.stock_name}({args.stock_code}) 价格/MA{args.ma_period}比值分布 {date_range_str}')
        plt.xlabel(f'价格/MA{args.ma_period}比值')
        plt.ylabel('密度')
        plt.grid(True, alpha=0.3)
        plt.legend()

        return plt


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
        ma_period=5
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
    plt = WeeklyPriceMAStrategy.plot_trades(df, trades, args)
    plt.show()

    # 绘制价格/MA5比值分布
    plt = WeeklyPriceMAStrategy.plot_ratio_distribution(df, args)
    plt.show()
