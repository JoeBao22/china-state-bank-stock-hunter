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
        new_stock = StockData(self.stock_code, self.name, self.data_dir)
        new_stock.df = StockDataProcessor.filter_by_date(self.df, start_date, end_date)
        return new_stock

    def calculate_ma(self, periods=[]):
        new_stock = StockData(self.stock_code, self.name, self.data_dir)
        new_stock.df = StockDataProcessor.calculate_ma(self.df, periods)
        return new_stock

    def aggregate_by_period(self, period='D'):
        new_stock = StockData(self.stock_code, self.name, self.data_dir)
        new_stock.df = StockDataProcessor.aggregate_by_period(self.df, period)
        return new_stock
    
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