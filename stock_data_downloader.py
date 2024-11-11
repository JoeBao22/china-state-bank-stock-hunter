import os
import time
import random
import akshare as ak
from datetime import datetime

class StockDownloader:
    def __init__(self, data_dir: str = "resource/stock_price"):
        self.data_dir = data_dir
        self._ensure_directory_exists()
        
    def _ensure_directory_exists(self):
        """确保数据目录存在"""
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
    
    def _get_file_path(self, stock_code: str) -> str:
        """获取股票数据文件路径"""
        return os.path.join(self.data_dir, f"{stock_code}.csv")
    
    def is_data_exists(self, stock_code: str) -> bool:
        """检查股票数据是否已经存在"""
        file_path = self._get_file_path(stock_code)
        return os.path.exists(file_path)
    
    def is_data_fresh(self, stock_code: str, max_days_old: int = 1) -> bool:
        """检查数据是否足够新鲜（默认1天）"""
        if not self.is_data_exists(stock_code):
            return False
            
        file_path = self._get_file_path(stock_code)
        file_mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
        days_old = (datetime.now() - file_mtime).days
        return days_old <= max_days_old
    
    def download_stock_data(self, stock_code: str, force_update: bool = False) -> bool:
        """
        下载股票数据
        :param stock_code: 股票代码
        :param force_update: 是否强制更新，即使数据已存在
        :return: 下载是否成功
        """
        if not force_update and self.is_data_fresh(stock_code):
            return True
        
        try:
            # 设置下载参数
            start_date = '20140101'  # 可以通过参数配置
            end_date = datetime.now().strftime('%Y%m%d')
            
            print(f"正在下载股票 {stock_code} 的历史行情数据...")
            stock_price_df = ak.stock_zh_a_hist(
                symbol=stock_code,
                start_date=start_date,
                end_date=end_date,
                adjust='qfq',  # 前复权
                period='daily'
            )
            
            # 保存数据
            file_path = self._get_file_path(stock_code)
            stock_price_df.to_csv(file_path, index=False, encoding='utf-8')
            
            print(f"下载完成股票 {stock_code} 的历史行情数据")
            
            # 添加随机延时，避免请求过于频繁
            time.sleep(random.uniform(3, 10))
            
            return True
            
        except Exception as e:
            print(f"下载股票 {stock_code} 数据时发生错误：{e}")
            return False
    
    def download_multiple_stocks(self, stock_codes: dict, force_update: bool = False):
        """
        批量下载多个股票的数据
        :param stock_codes: 股票代码字典，格式为 {code: name}
        :param force_update: 是否强制更新
        :return: 下载结果字典
        """
        results = {}
        for stock_code in stock_codes:
            success = self.download_stock_data(stock_code, force_update)
            results[stock_code] = success
        return results


if __name__ == '__main__':
    print("akshare版本:", ak.__version__)
    
    # 测试数据下载
    stock_codes = {
        '601398': '工商银行',
        '601939': '建设银行',
        '601288': '农业银行',
        '601988': '中国银行',
        '601328': '交通银行',
    }
    
    downloader = StockDownloader()
    results = downloader.download_multiple_stocks(stock_codes, force_update=True)
    
    # 打印下载结果
    for code, success in results.items():
        status = "成功" if success else "失败"
        print(f"股票 {code} ({stock_codes[code]}) 下载{status}")