from strategy_analyzer import get_performance_summary
from strategy_generator import MAStrategy, KDJStrategy, MACDStrategy
from stock_data import StockData
from chart import TradeChart, IndicatorDistributionChart
import argparse


class TestMAArgs:
    """用于测试的参数类"""
    def __init__(self):
        self.stock_code = '601288'
        self.stock_name = '农业银行'
        # self.stock_code = '600900'
        # self.stock_name = '长江电力'
        self.start_date = '2014-01-01'
        self.end_date = None
        self.ratio1 = 1.00
        self.ratio2 = 1.03
        self.period = 'W'
        self.ma_period = 10


class TestKDJArgs:
    """用于测试的参数类"""
    def __init__(self):
        self.stock_code = '601288'
        self.stock_name = '农业银行'
        self.start_date = '2014-01-01'
        self.end_date = None
        self.n = 9
        self.m1 = 3
        self.m2 = 3
        self.period = 'W'


class TestMACDArgs:
    """用于测试的参数类"""
    def __init__(self):
        self.stock_code = '601288'
        self.stock_name = '农业银行'
        self.start_date = '2014-01-01'
        self.end_date = None
        self.fast_period = 12
        self.slow_period = 26
        self.signal_period = 9
        self.period = 'W'

def parse_args():
    parser = argparse.ArgumentParser(description='股票交易策略分析工具')
    
    # 必需参数
    parser.add_argument('--stock-code', 
                       type=str, 
                       required=True,
                       help='股票代码，例如: 601288')
    
    parser.add_argument('--stock-name', 
                       type=str, 
                       required=True,
                       help='股票名称，例如: 农业银行')
    
    # 可选参数
    parser.add_argument('--start-date', 
                       type=str, 
                       default='2018-01-01',
                       help='开始日期，格式：YYYY-MM-DD，默认：2018-01-01')
    
    parser.add_argument('--end-date', 
                       type=str, 
                       default=None,
                       help='结束日期，格式：YYYY-MM-DD，默认：None（至今）')
    
    parser.add_argument('--ratio1', 
                       type=float, 
                       default=1.00,
                       help='买入阈值，默认：1.00')
    
    parser.add_argument('--ratio2', 
                       type=float, 
                       default=1.05,
                       help='卖出阈值，默认：1.05')
    
    parser.add_argument('--period', 
                       type=str, 
                       choices=['D', 'W', 'M'],
                       default='W',
                       help='周期，D=日线，W=周线，M=月线，默认：W')
    
    parser.add_argument('--ma-period', 
                       type=int, 
                       default=5,
                       help='移动平均周期，默认：5')
    
    parser.add_argument('--indicator-name',
                       type=str,
                       default=None,
                       help='指标名称，默认：根据ma-period自动生成')
    
    args = parser.parse_args()
    
    # 如果没有提供indicator_name，则自动生成
    if args.indicator_name is None:
        args.indicator_name = f'当前价格/MA{args.ma_period}'
    
    return args


def test_ma():
    args = TestMAArgs()
    strategy = MAStrategy(args.ratio1, args.ratio2, args.period, args.ma_period)
    stock_data = StockData(args.stock_code, args.stock_name)

    df, signals, trades = strategy.apply_strategy(stock_data, args.start_date, args.end_date)
    
    print("\n交易记录：")
    print(trades)
    
    # 打印策略表现
    print("\n策略表现：")
    summary = get_performance_summary(trades)
    print(f"总交易次数: {summary['total_trades']}")
    print(f"胜率: {summary['win_rate']:.2f}%")
    print(f"平均收益率: {summary['avg_return']:.2f}%")
    print(f"总收益率: {summary['total_return']:.2f}%")
    print(f"最大单笔收益: {summary['max_return']:.2f}%")
    print(f"最小单笔收益: {summary['min_return']:.2f}%")
    print(f"平均持仓周数: {summary['avg_hold_weeks']:.1f}")
    print(f"平均回撤率: {summary['avg_drawdown']:.2f}%")
    print(f"最大回撤率: {summary['max_drawdown']:.2f}%")

    # 绘制交易图表
    trade_chart = TradeChart(df, trades, strategy.new_indicator_columns, args).plot()
    trade_chart.show()

    new_indicators = strategy.new_indicator_columns
    distribution_chart = IndicatorDistributionChart(df, new_indicators[0], args).plot()
    # (IndicatorDistributionChart(df, new_indicators[0], args)
    #             .plot_histogram()
    #             .add_statistics()
    #             .set_chart_properties())
    distribution_chart.show()

def test_kdj():
    args = TestKDJArgs()
    strategy = KDJStrategy(args.n, args.m1, args.m2, args.period)
    stock_data = StockData(args.stock_code, args.stock_name)

    df, signals, trades = strategy.apply_strategy(stock_data, args.start_date, args.end_date)
    
    print("\n交易记录：")
    print(trades)
    
    # 打印策略表现
    print("\n策略表现：")
    summary = get_performance_summary(trades)
    print(f"总交易次数: {summary['total_trades']}")
    print(f"胜率: {summary['win_rate']:.2f}%")
    print(f"平均收益率: {summary['avg_return']:.2f}%")
    print(f"总收益率: {summary['total_return']:.2f}%")
    print(f"最大单笔收益: {summary['max_return']:.2f}%")
    print(f"最小单笔收益: {summary['min_return']:.2f}%")
    print(f"平均持仓周数: {summary['avg_hold_weeks']:.1f}")
    print(f"平均回撤率: {summary['avg_drawdown']:.2f}%")
    print(f"最大回撤率: {summary['max_drawdown']:.2f}%")

    new_indicators = strategy.new_indicator_columns
    # 绘制交易图表
    trade_chart = (TradeChart(df, trades, new_indicators, args)
                .plot_price_line()
                .plot_trade_points()
                .set_price_chart_properties()
                .plot_indicator_line()
                .plot_indicator_points()
                .set_indicator_chart_properties())

    trade_chart.show()

    distribution_chart = (IndicatorDistributionChart(df, new_indicators[0], args)
                .plot_histogram()
                .add_statistics()
                .set_chart_properties())
    distribution_chart.show()

def test_macd():
    args = TestMACDArgs()
    strategy = MACDStrategy(args.fast_period, args.slow_period, args.signal_period, args.period)
    stock_data = StockData(args.stock_code, args.stock_name)

    df, signals, trades = strategy.apply_strategy(stock_data, args.start_date, args.end_date)
    
    print("\n交易记录：")
    print(trades)
    
    # 打印策略表现
    print("\n策略表现：")
    summary = get_performance_summary(trades)
    print(f"总交易次数: {summary['total_trades']}")
    print(f"胜率: {summary['win_rate']:.2f}%")
    print(f"平均收益率: {summary['avg_return']:.2f}%")
    print(f"总收益率: {summary['total_return']:.2f}%")
    print(f"最大单笔收益: {summary['max_return']:.2f}%")
    print(f"最小单笔收益: {summary['min_return']:.2f}%")
    print(f"平均持仓周数: {summary['avg_hold_weeks']:.1f}")
    print(f"平均回撤率: {summary['avg_drawdown']:.2f}%")
    print(f"最大回撤率: {summary['max_drawdown']:.2f}%")

    new_indicators = strategy.new_indicator_columns
    # 绘制交易图表
    trade_chart = (TradeChart(df, trades, new_indicators, args)
                .plot_price_line()
                .plot_trade_points()
                .set_price_chart_properties()
                .plot_indicator_line()
                .plot_indicator_points()
                .set_indicator_chart_properties())

    trade_chart.show()

    distribution_chart = (IndicatorDistributionChart(df, new_indicators[0], args)
                .plot_histogram()
                .add_statistics()
                .set_chart_properties())
    distribution_chart.show()


# 使用示例
if __name__ == '__main__':
    test_macd()