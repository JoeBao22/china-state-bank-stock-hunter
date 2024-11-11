import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import sys

class CandlestickChart:
    def __init__(self, stock_data):
        self.stock_data = stock_data
        self._setup_chinese_font()
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
        
    def show(self):
        plt.tight_layout()
        plt.show()
        
    def save(self, filepath):
        plt.tight_layout()
        self.fig.savefig(filepath)

# 使用示例
if __name__ == "__main__":
    from stock import StockData
    
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