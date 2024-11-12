from strategy_analyzer import get_performance_summary
from strategy_generator import MAStrategy
from stock_data import StockData
from chart import TradeChart, IndicatorDistributionChart
import argparse


class TestArgs:
    """用于测试的参数类"""
    def __init__(self):
        self.stock_code = '601288'
        self.stock_name = '农业银行'
        self.start_date = '2014-01-01'
        self.end_date = None
        self.ratio1 = 1.00
        self.ratio2 = 1.03
        self.period = 'W'
        self.ma_period = 10
        self.indicator_name = '当前价格/MA10'



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


# 使用示例
if __name__ == '__main__':
    args = TestArgs()
    # args = parse_args()
    # print(f"股票代码: {args.stock_code}")
    # print(f"股票名称: {args.stock_name}")
    # print(f"开始日期: {args.start_date}")
    # print(f"结束日期: {args.end_date}")
    # print(f"买入阈值: {args.ratio1}")
    # print(f"卖出阈值: {args.ratio2}")
    # print(f"周期: {args.period}")
    # print(f"MA周期: {args.ma_period}")
    # print(f"指标名称: {args.indicator_name}")

    stock_data = StockData(args.stock_code, args.stock_name)

    strategy = MAStrategy(args.ratio1, args.ratio2, args.period, args.ma_period)
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
    trade_chart = TradeChart(df, trades, args).plot()
    trade_chart.save('./resource/img/trade_chart.png')
    # trade_chart.show()

    # 绘制价格/MA5比值分布
    distribution_chart = IndicatorDistributionChart(df, args).plot()
    distribution_chart.save('./resource/img/distribution_chart.png')
    # distribution_chart.show()
