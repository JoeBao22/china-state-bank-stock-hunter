import pandas as pd
import os
from stock_processor import StockDataProcessor
from stock_data_downloader import StockDownloader

class StockData:
    def __init__(self, stock_code: str, name: str, data_dir: str = "resource/stock_price", force_update: bool = False):
        """
        初始化股票数据对象
        :param stock_code: 股票代码
        :param name: 股票名称
        :param data_dir: 数据存储目录
        :param force_update: 是否强制更新数据
        """
        self.stock_code = stock_code
        self.name = name
        self.data_dir = data_dir
        
        # 下载或更新数据
        downloader = StockDownloader(self.data_dir)
        if force_update or not downloader.is_data_fresh(self.stock_code):
            success = downloader.download_stock_data(self.stock_code, force_update)
            if not success:
                raise FileNotFoundError(f"无法获取股票 {self.stock_code} 的数据")
            
        self.df = self._load_data_from_csv()
    
    def _load_data_from_csv(self) -> pd.DataFrame:
        file_path = os.path.join(self.data_dir, f"{self.stock_code}.csv")
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"找不到股票{self.stock_code}的数据文件：{file_path}")
        
        try:
            df = pd.read_csv(file_path)
            
            required_columns = ['日期', '开盘', '最高', '最低', '收盘']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                raise ValueError(f"数据文件缺少必要的列：{missing_columns}")
            
            df['日期'] = pd.to_datetime(df['日期'])
            df.sort_values('日期', inplace=True)
            df.reset_index(drop=True, inplace=True)
            
            return df
            
        except pd.errors.EmptyDataError:
            raise ValueError(f"数据文件 {file_path} 是空的")
        except pd.errors.ParserError:
            raise ValueError(f"数据文件 {file_path} 格式不正确")

    def filter_by_date(self, start_date=None, end_date=None):
        self.df = StockDataProcessor.filter_by_date(self.df, start_date, end_date)
        return self

    def calculate_ma(self, periods=[]):
        self.df = StockDataProcessor.calculate_ma(self.df, periods)
        return self

    def calculate_kdj(self, n=9, m1=3, m2=3):
        self.df = StockDataProcessor.calculate_kdj(self.df, n, m1, m2)
        return self

    def calculate_macd(self, fast_period=12, slow_period=26, signal_period=9):
        self.df = StockDataProcessor.calculate_macd(self.df, fast_period, slow_period, signal_period)
        return self
    
    def aggregate_by_period(self, period='D'):
        self.df = StockDataProcessor.aggregate_by_period(self.df, period)
        return self
    
    def __str__(self) -> str:
        return f"股票代码：{self.stock_code}\n" \
               f"股票名称：{self.name}\n" \
               f"数据范围：{self.df['日期'].min().strftime('%Y-%m-%d')} 至 {self.df['日期'].max().strftime('%Y-%m-%d')}\n" \
               f"数据条数：{len(self.df)}"
    
    def __repr__(self) -> str:
        return f"StockData(stock_code='{self.stock_code}', name='{self.name}')"


if __name__ == "__main__":
    try:
        # 创建股票数据对象 - 如果数据不是最新的会自动下载
        stock = StockData("601288", "农业银行")
        
        # 强制更新数据
        stock_forced = StockData("601288", "农业银行", force_update=True)
        
        # 链式调用处理数据
        processed_stock = (stock
            .aggregate_by_period('W')
            .filter_by_date('2023-01-01', '2023-12-31')
            .calculate_ma([5, 10, 20]))
        
        print(processed_stock)
        
    except (FileNotFoundError, ValueError) as e:
        print(f"错误：{e}")