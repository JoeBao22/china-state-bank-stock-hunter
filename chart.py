import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import sys


def setup_chinese_font():
    if sys.platform.startswith("win"):
        plt.rcParams["font.sans-serif"] = ["SimHei"]
    elif sys.platform.startswith("linux"):
        plt.rcParams["font.sans-serif"] = ["WenQuanYi Micro Hei"]
    elif sys.platform.startswith("darwin"):
        plt.rcParams["font.sans-serif"] = ["PingFang HK"]
    plt.rcParams["axes.unicode_minus"] = False


class Chart:
    def __init__(self):
        setup_chinese_font()

    def show(self):
        plt.tight_layout()
        plt.show()

    def save(self, filepath):
        plt.tight_layout()
        plt.savefig(filepath)


class CandlestickChart(Chart):
    def __init__(self, stock_data):
        super().__init__()
        self.stock_data = stock_data
        self.fig, self.ax = plt.subplots(figsize=(12, 8))
        self._setup_basic_style()
        
    def _setup_chinese_font(self):
        if sys.platform.startswith("win"):
            plt.rcParams["font.sans-serif"] = ["SimHei"]
        elif sys.platform.startswith("linux"):
            plt.rcParams["font.sans-serif"] = ["WenQuanYi Micro Hei"]
        elif sys.platform.startswith("darwin"):
            plt.rcParams["font.sans-serif"] = ["PingFang HK"]
        plt.rcParams["axes.unicode_minus"] = False
        
    def _setup_basic_style(self):
        self.ax.set_facecolor("#f6f6f6")
        self.fig.set_facecolor("white")
        self.ax.grid(True, linestyle="--", alpha=0.3)
        
    def plot_candlesticks(self):
        for i in range(len(self.stock_data.df)):
            row = self.stock_data.df.iloc[i]
            color = "red" if row['收盘'] >= row['开盘'] else "green"
            
            body_height = abs(row['收盘'] - row['开盘'])
            bottom = min(row['开盘'], row['收盘'])
            rect = Rectangle((i - 0.3, bottom), 0.6, body_height, facecolor=color)
            self.ax.add_patch(rect)
            
            self.ax.plot([i, i], [row['最高'], max(row['开盘'], row['收盘'])], 
                        color=color, linewidth=0.5)
            self.ax.plot([i, i], [row['最低'], min(row['开盘'], row['收盘'])], 
                        color=color, linewidth=0.5)
        
        return self
        
    def plot_ma_lines(self):
        ma_columns = [col for col in self.stock_data.df.columns if col.startswith('MA')]
        if not ma_columns:
            return self
            
        for idx, col in enumerate(ma_columns):
            self.ax.plot(
                range(len(self.stock_data.df)),
                self.stock_data.df[col],
                label=col,
                linewidth=2,
                alpha=0.8,
                linestyle='dashdot'
            )
            
        self.ax.legend()
        return self
        
    def set_xticks(self):
        df = self.stock_data.df
        num_ticks = min(10, len(df))
        if num_ticks > 1:
            step = max(len(df) // num_ticks, 1)
            self.ax.set_xticks(range(0, len(df), step))
            self.ax.set_xticklabels(
                df['日期'].iloc[::step].dt.strftime('%Y-%m-%d'),
                rotation=45
            )
        return self

    def set_title(self, period='D'):
        period_names = {"D": "日", "W": "周", "M": "月"}
        period_name = period_names.get(period, '日')
        
        dates = self.stock_data.df['日期']
        date_range = f"({dates.min().strftime('%Y-%m-%d')} 至 {dates.max().strftime('%Y-%m-%d')})"
        
        title = f"{self.stock_data.name}({self.stock_data.stock_code}) - {period_name}K线 {date_range}"
        self.ax.set_title(title, pad=15)
        return self


class TradeChart(Chart):
    def __init__(self, df, trades, new_indicator_columns, args):
        super().__init__()
        self.df = df
        self.trades = trades
        self.new_indicator_columns = new_indicator_columns
        self.args = args
        self.fig, (self.price_ax, self.indicator_ax) = plt.subplots(
            2, 1, figsize=(12, 8), height_ratios=[2, 1]
        )
        self._setup_basic_style()
    
    def _setup_basic_style(self):
        for ax in [self.price_ax, self.indicator_ax]:
            ax.set_facecolor("#f6f6f6")
            ax.grid(True, linestyle="--", alpha=0.3)
        self.fig.set_facecolor("white")
    
    def plot_price_line(self):
        self.price_ax.plot(self.df['日期'], self.df['收盘'], 
                          label='收盘价', color='gray', alpha=0.6)
        return self
    
    def plot_trade_points(self):
        for _, trade in self.trades.iterrows():
            label_buy = '买入点' if '买入点' not in [l.get_label() for l in self.price_ax.get_lines()] else ""
            label_sell = '卖出点' if '卖出点' not in [l.get_label() for l in self.price_ax.get_lines()] else ""
            
            self.price_ax.scatter(trade['买入日期'], trade['买入价格'], 
                                color='green', marker='^', s=100, label=label_buy)
            self.price_ax.scatter(trade['卖出日期'], trade['卖出价格'], 
                                color='red', marker='v', s=100, label=label_sell)
            
            return_text = f"{trade['收益率']:.1f}%"
            self.price_ax.annotate(return_text, 
                                 xy=(trade['卖出日期'], trade['卖出价格']),
                                 xytext=(10, 10), textcoords='offset points',
                                 fontsize=8, color='red' if trade['收益率'] > 0 else 'green')
        return self
    
    def set_price_chart_properties(self):
        date_range_str = self._get_date_range_str()
        self.price_ax.set_title(
            f'{self.args.stock_name}({self.args.stock_code}) 周线交易策略 {date_range_str}'
        )
        self.price_ax.set_xlabel('日期')
        self.price_ax.set_ylabel('价格')
        
        handles, labels = self.price_ax.get_legend_handles_labels()
        by_label = dict(zip(labels, handles))
        self.price_ax.legend(by_label.values(), by_label.keys())
        return self
    
    def plot_indicator_line(self):
        if self.new_indicator_columns:
            for col in self.new_indicator_columns:
                self.indicator_ax.plot(self.df['日期'], self.df[col], 
                                     label=col, alpha=0.7)
        return self
    
    def plot_threshold_lines(self):
        self.indicator_ax.axhline(y=self.args.ratio1, color='green', linestyle='--', 
                                label=f'买入阈值 ({self.args.ratio1:.2f})')
        self.indicator_ax.axhline(y=self.args.ratio2, color='red', linestyle='--', 
                                label=f'卖出阈值 ({self.args.ratio2:.2f})')
        self.indicator_ax.axhline(y=1, color='gray', linestyle='-', 
                                label='均衡线 (1.00)', alpha=0.5)
        return self
    
    def plot_indicator_points(self):
        if self.new_indicator_columns:
            for indicator in self.new_indicator_columns:
                for _, trade in self.trades.iterrows():
                    self.indicator_ax.scatter(trade['买入日期'], trade[f'买入时{indicator}指标'], 
                                            color='green', marker='^', s=100)
                    self.indicator_ax.scatter(trade['卖出日期'], trade[f'卖出时{indicator}指标'], 
                                            color='red', marker='v', s=100)
        return self
    
    def set_indicator_chart_properties(self):
        self.indicator_ax.set_title(f'{self.new_indicator_columns}变化')
        self.indicator_ax.set_xlabel('日期')
        self.indicator_ax.set_ylabel('指标值')
        self.indicator_ax.legend()
        return self
    
    def _get_date_range_str(self):
        if self.args.start_date and self.args.end_date:
            return f"({self.args.start_date} 至 {self.args.end_date})"
        elif self.args.start_date:
            return f"({self.args.start_date} 之后)"
        elif self.args.end_date:
            return f"({self.args.end_date} 之前)"
        return ""

    def plot(self):
        return (self
                .plot_price_line()
                .plot_trade_points()
                .set_price_chart_properties()
                .plot_indicator_line()
                .plot_threshold_lines()
                .plot_indicator_points()
                .set_indicator_chart_properties())

class IndicatorDistributionChart(Chart):
    def __init__(self, df, indicator_name, args, bins=50):
        super().__init__()
        self.df = df
        self.indicator_name = indicator_name
        self.args = args
        self.bins = bins
        self.fig, self.dist_ax = plt.subplots(figsize=(12, 6))
        self._setup_basic_style()
        
    def _setup_basic_style(self):
        self.dist_ax.set_facecolor("#f6f6f6")
        self.dist_ax.grid(True, linestyle="--", alpha=0.3)
        self.fig.set_facecolor("white")
        
    def plot_histogram(self):
        self.ratio_data = self.df[f'{self.indicator_name}'].dropna()
        self.dist_ax.hist(self.ratio_data, bins=self.bins, 
                         alpha=0.7, color='blue', density=True)
        return self
        
    def plot_threshold_lines(self):
        ylim = self.dist_ax.get_ylim()
        
        self.dist_ax.vlines(self.args.ratio1, 0, ylim[1], 
                          colors='green', linestyles='--',
                          label=f'买入阈值 ({self.args.ratio1:.2f})')
        self.dist_ax.vlines(self.args.ratio2, 0, ylim[1], 
                          colors='red', linestyles='--',
                          label=f'卖出阈值 ({self.args.ratio2:.2f})')
        self.dist_ax.vlines(1, 0, ylim[1], 
                          colors='gray', linestyles='-',
                          label='均衡线 (1.00)', alpha=0.5)
        return self
        
    def add_statistics(self):
        stats = {
            '均值': self.ratio_data.mean(),
            '中位数': self.ratio_data.median(),
            '标准差': self.ratio_data.std(),
            '10%分位数': self.ratio_data.quantile(0.1),
            '90%分位数': self.ratio_data.quantile(0.9)
        }
        
        stats_text = '\n'.join(
            f'{key}: {value:.3f}' for key, value in stats.items()
        )
        
        self.dist_ax.text(0.02, 0.98, stats_text,
                         transform=self.dist_ax.transAxes,
                         verticalalignment='top',
                         bbox=dict(boxstyle='round', 
                                 facecolor='white', 
                                 alpha=0.8))
        return self
        
    def set_chart_properties(self):
        date_range_str = self._get_date_range_str()
        self.dist_ax.set_title(
            f'{self.args.stock_name}({self.args.stock_code}) '
            f'{self.indicator_name}指标值分布 {date_range_str}'
        )
        
        self.dist_ax.set_xlabel(f'{self.indicator_name}值')
        self.dist_ax.set_ylabel('密度')
        
        self.dist_ax.legend()
        return self
        
    def _get_date_range_str(self):
        if self.args.start_date and self.args.end_date:
            return f"({self.args.start_date} 至 {self.args.end_date})"
        elif self.args.start_date:
            return f"({self.args.start_date} 之后)"
        elif self.args.end_date:
            return f"({self.args.end_date} 之前)"
        return ""

    def plot(self):
        return (self
                .plot_histogram()
                .plot_threshold_lines()
                .add_statistics()
                .set_chart_properties())

# 使用示例
if __name__ == "__main__":
    from stock_data import StockData
    
    # 准备数据
    stock = StockData("601288", "农业银行")
    processed_stock = (stock
        .aggregate_by_period('W')
        .filter_by_date('2023-01-01', '2023-12-31')
        .calculate_ma([5, 10, 20]))
    
    # 绘制图表
    chart = CandlestickChart(processed_stock)
    (chart.plot_candlesticks()
          .plot_ma_lines()
          .set_xticks()
          .set_title('W')
          .show())
