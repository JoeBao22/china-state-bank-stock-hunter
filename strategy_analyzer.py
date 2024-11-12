import pandas as pd
import numpy as np
import sys
import matplotlib.pyplot as plt

class WeeklyPriceMAStrategy:
    def __init__(self, stock_data, ratio1, ratio2, start_date=None, end_date=None):
        """
        初始化周线价格/MA10策略分析器
        :param stock_data: StockData对象
        :param ratio1: 买入阈值，当价格/MA10 < ratio1时买入（价格低于MA10一定比例）
        :param ratio2: 卖出阈值，当价格/MA10 > ratio2时卖出（价格高于MA10一定比例）
        :param start_date: 起始日期，格式：'YYYY-MM-DD'
        :param end_date: 结束日期，格式：'YYYY-MM-DD'
        """
        self.stock_data = stock_data
        self.ratio1 = ratio1
        self.ratio2 = ratio2
        self.start_date = start_date
        self.end_date = end_date
        self.df = None
        self.signals = None
        self.trades = None
        self._setup_chinese_font()
        self._prepare_data()
    
    def _setup_chinese_font(self):
        """设置中文字体支持"""
        if sys.platform.startswith("win"):
            plt.rcParams["font.sans-serif"] = ["SimHei"]
        elif sys.platform.startswith("linux"):
            plt.rcParams["font.sans-serif"] = ["WenQuanYi Micro Hei"]
        elif sys.platform.startswith("darwin"):
            plt.rcParams["font.sans-serif"] = ["PingFang HK"]
        plt.rcParams["axes.unicode_minus"] = False
    
    def _prepare_data(self):
        """准备数据，计算周线和信号"""
        # 利用StockData的链式调用特性处理数据
        processed_stock = (self.stock_data
            .aggregate_by_period('W')  # 转换为周线
            .filter_by_date(self.start_date, self.end_date)  # 按日期过滤
            .calculate_ma([10]))  # 计算MA10
        
        self.df = processed_stock.df.copy()
        
        # 计算价格/MA10比率
        self.df['PRICE_MA_RATIO'] = self.df['收盘'] / self.df['MA10']
        
        # 生成买卖信号
        self.signals = self._generate_signals()
        
        # 生成交易记录
        self.trades = self._generate_trades()
    
    def _generate_signals(self):
        """生成买卖信号"""
        signals = pd.DataFrame(index=self.df.index)
        signals['日期'] = self.df['日期']
        signals['收盘'] = self.df['收盘']
        signals['MA10'] = self.df['MA10']
        signals['PRICE_MA_RATIO'] = self.df['PRICE_MA_RATIO']
        
        # 生成买入信号（1）和卖出信号（-1）
        signals['SIGNAL'] = 0
        valid_data = signals['MA10'].notna()
        signals.loc[valid_data & (signals['PRICE_MA_RATIO'] < self.ratio1), 'SIGNAL'] = 1
        signals.loc[valid_data & (signals['PRICE_MA_RATIO'] > self.ratio2), 'SIGNAL'] = -1
        
        return signals
    
    def _generate_trades(self):
        """生成交易记录"""
        trades = []
        position = 0
        entry_price = 0
        entry_date = None
        max_price = 0
        
        for idx, row in self.signals.iterrows():
            if pd.isna(row['MA10']):
                continue
                
            if position == 0 and row['SIGNAL'] == 1:  # 买入
                position = 1
                entry_price = row['收盘']
                entry_date = row['日期']
                entry_ratio = row['PRICE_MA_RATIO']
                max_price = entry_price
            elif position == 1:  # 持仓期间更新最高价
                max_price = max(max_price, row['收盘'])
                if row['SIGNAL'] == -1:  # 卖出
                    position = 0
                    exit_price = row['收盘']
                    profit_pct = (exit_price / entry_price - 1) * 100
                    max_profit_pct = (max_price / entry_price - 1) * 100
                    drawdown_pct = (exit_price / max_price - 1) * 100
                    trades.append({
                        '买入日期': entry_date,
                        '买入价格': entry_price,
                        '买入时价格/MA10比值': entry_ratio,
                        '卖出日期': row['日期'],
                        '卖出价格': exit_price,
                        '卖出时价格/MA10比值': row['PRICE_MA_RATIO'],
                        '收益率': profit_pct,
                        '最大收益率': max_profit_pct,
                        '回撤率': drawdown_pct
                    })
        
        return pd.DataFrame(trades)

    def get_performance_summary(self):
        """获取策略表现摘要"""
        if len(self.trades) == 0:
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
        
        # 计算各种指标
        win_trades = len(self.trades[self.trades['收益率'] > 0])
        total_trades = len(self.trades)
        
        # 计算持仓周数
        self.trades['持仓周数'] = ((pd.to_datetime(self.trades['卖出日期']) - 
                               pd.to_datetime(self.trades['买入日期'])).dt.days / 7).round(1)
        
        # 计算复利收益率
        compound_return = np.prod(1 + self.trades['收益率'] / 100) - 1
        
        summary = {
            'total_trades': total_trades,
            'win_rate': win_trades / total_trades * 100,
            'avg_return': self.trades['收益率'].mean(),
            'total_return': compound_return * 100,
            'max_return': self.trades['收益率'].max(),
            'min_return': self.trades['收益率'].min(),
            'avg_hold_weeks': self.trades['持仓周数'].mean(),
            'avg_drawdown': self.trades['回撤率'].mean(),
            'max_drawdown': self.trades['回撤率'].min()
        }
        
        return summary

    def plot_trades(self):
        """绘制交易图表"""
        try:
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 12), height_ratios=[2, 1])
            
            # 上图：价格和MA10
            ax1.plot(self.df['日期'], self.df['收盘'], label='收盘价', color='gray', alpha=0.6)
            ax1.plot(self.df['日期'], self.df['MA10'], label='MA10', color='blue', alpha=0.6)
            
            # 标记买入点和卖出点
            for _, trade in self.trades.iterrows():
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
            if self.start_date and self.end_date:
                date_range_str = f"({self.start_date} 至 {self.end_date})"
            elif self.start_date:
                date_range_str = f"({self.start_date} 之后)"
            elif self.end_date:
                date_range_str = f"({self.end_date} 之前)"
            
            ax1.set_title(f'{self.stock_data.name}({self.stock_data.stock_code}) 周线交易策略 {date_range_str}')
            ax1.set_xlabel('日期')
            ax1.set_ylabel('价格')
            ax1.legend()
            ax1.grid(True)
            
            # 下图：价格/MA10比值
            ax2.plot(self.df['日期'], self.df['PRICE_MA_RATIO'], label='价格/MA10', color='purple')
            ax2.axhline(y=self.ratio1, color='green', linestyle='--', label=f'买入阈值 ({self.ratio1:.2f})')
            ax2.axhline(y=self.ratio2, color='red', linestyle='--', label=f'卖出阈值 ({self.ratio2:.2f})')
            ax2.axhline(y=1, color='gray', linestyle='-', label='均衡线 (1.00)', alpha=0.5)
            
            # 标记买卖点的比值
            for _, trade in self.trades.iterrows():
                ax2.scatter(trade['买入日期'], trade['买入时价格/MA10比值'], color='green', marker='^', s=100)
                ax2.scatter(trade['卖出日期'], trade['卖出时价格/MA10比值'], color='red', marker='v', s=100)
            
            ax2.set_title('价格/MA10比值变化')
            ax2.set_xlabel('日期')
            ax2.set_ylabel('比值')
            ax2.legend()
            ax2.grid(True)
            
            plt.tight_layout()
            return plt
            
        except ImportError:
            print("请安装matplotlib库以使用绘图功能")
            return None

    def plot_ratio_distribution(self, bins=50):
        """
        绘制价格/MA10比值的分布直方图
        :param bins: 直方图的箱数
        """
        plt.figure(figsize=(12, 6))
        
        # 绘制直方图
        ratio_data = self.df['PRICE_MA_RATIO'].dropna()
        plt.hist(ratio_data, bins=bins, alpha=0.7, color='blue', density=True)
        
        # 添加买入卖出阈值线
        ylim = plt.gca().get_ylim()
        plt.vlines(self.ratio1, 0, ylim[1], colors='green', linestyles='--', 
                  label=f'买入阈值 ({self.ratio1:.2f})')
        plt.vlines(self.ratio2, 0, ylim[1], colors='red', linestyles='--', 
                  label=f'卖出阈值 ({self.ratio2:.2f})')
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
        if self.start_date and self.end_date:
            date_range_str = f"({self.start_date} 至 {self.end_date})"
        elif self.start_date:
            date_range_str = f"({self.start_date} 之后)"
        elif self.end_date:
            date_range_str = f"({self.end_date} 之前)"
            
        plt.title(f'{self.stock_data.name}({self.stock_data.stock_code}) 价格/MA10比值分布 {date_range_str}')
        plt.xlabel('价格/MA10比值')
        plt.ylabel('密度')
        plt.grid(True, alpha=0.3)
        plt.legend()
        
        return plt


if __name__ == "__main__":
    from stock_data import StockData
    
    # 创建股票数据对象
    stock = StockData("601288", "农业银行")
    
    # 测试2018年至今的策略
    analyzer = WeeklyPriceMAStrategy(
        stock_data=stock,
        ratio1=1.00,  # 当价格低于MA10的95%时买入
        ratio2=1.05,  # 当价格高于MA10的105%时卖出
        start_date='2018-01-01',
        end_date=None
    )
    
    # 打印交易记录
    pd.set_option('display.max_columns', None)
    print("\n交易记录：")
    print(analyzer.trades)
    
    # 打印策略表现
    print("\n策略表现：")
    summary = analyzer.get_performance_summary()
    print(f"总交易次数: {summary['total_trades']}")

    # 绘制交易图表
    plt = analyzer.plot_trades()
    plt.show()
