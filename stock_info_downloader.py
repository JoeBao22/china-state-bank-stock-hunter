import os
import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import random
import akshare as ak


class CompanyInfoDownloader:
    def __init__(self, data_dir: str = "resource/company_info"):
        self.data_dir = data_dir
        self._ensure_directory_exists()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
    def _ensure_directory_exists(self):
        """确保数据目录存在"""
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
    
    def _get_file_path(self, stock_code: str) -> str:
        """获取公司信息文件路径"""
        return os.path.join(self.data_dir, f"{stock_code}.csv")
    
    def is_data_exists(self, stock_code: str) -> bool:
        """检查公司信息是否已经存在"""
        file_path = self._get_file_path(stock_code)
        return os.path.exists(file_path)
    
    def download_company_info(self, stock_code: str) -> bool:
        """
        下载单个公司信息
        :param stock_code: 股票代码
        :param force_update: 是否强制更新，即使数据已存在
        :return: 下载是否成功
        """

        if self.is_data_exists(stock_code):
            print(f"公司 {stock_code} 的信息已存在")
            return True
        try:
            url = f"https://basic.10jqka.com.cn/{stock_code}/"
            print(f"正在下载公司 {stock_code} 的基本信息...")
            
            response = requests.get(url, headers=self.headers)
            response.encoding = 'gbk'
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 提取公司名称和代码
            div_name_code = soup.find('div', class_="code fl")
            if div_name_code is None:
                print(f"未找到公司 {stock_code} 的信息")
                return False
                
            company_name = div_name_code.find_all('h1')[0].text.strip()
            stock_code_found = div_name_code.find_all('h1')[1].text.strip()
            
            # 提取公司详细信息
            company_info = soup.find('table', class_="m_table m_table_db mt10")
            if company_info:
                data = {
                    '公司名称': company_name,
                    '股票代码': stock_code_found
                }
                
                for tr in company_info.find_all('tr'):
                    for td in tr.find_all('td'):
                        content = td.get_text().strip()
                        feature_name = content.split("：")[0]
                        feature_info = content[(len(feature_name)+1):]
                        feature_value = feature_info.strip().split("\n")[0].strip()
                        data[feature_name] = feature_value
                if data['公司名称'] == '' or data['股票代码'] == '':
                    print(f"未找到公司 {stock_code} 的信息")
                    return False
                # 保存数据
                df = pd.DataFrame([data])
                file_path = self._get_file_path(stock_code)
                df.to_csv(file_path, index=False, encoding='utf-8')
                
                print(f"成功下载公司 {stock_code} ({company_name}) 的基本信息")
                
                # 添加随机延时，避免请求过于频繁
                # time.sleep(random.uniform(2, 5))
                time.sleep(0.5)
                
                return True
            return False
            
        except Exception as e:
            print(f"下载公司 {stock_code} 信息时发生错误：{e}")
            return False
    
    def download_multiple_companies(self, stock_codes: list, force_update: bool = False) -> dict:
        """
        批量下载多个公司的信息
        :param stock_codes: 股票代码列表
        :param force_update: 是否强制更新
        :return: 下载结果字典
        """
        results = {}
        for stock_code in stock_codes:
            success = self.download_company_info(stock_code, force_update)
            results[stock_code] = success
        return results

    def load_company_info(self, stock_code: str) -> pd.DataFrame:
        """
        加载已下载的公司信息
        :param stock_code: 股票代码
        :return: 包含公司信息的DataFrame，如果文件不存在返回None
        """
        file_path = self._get_file_path(stock_code)
        if not self.is_data_exists(stock_code):
            return None
        try:
            return pd.read_csv(file_path, encoding='utf-8')
        except Exception as e:
            print(f"加载公司 {stock_code} 信息时发生错误：{e}")
            return None



if __name__ == '__main__':
    downloader = CompanyInfoDownloader()
    # # SZ
    # for i in range(3044):
    #     stock_code = str(i).zfill(6)
    #     downloader.download_company_info(stock_code)

    # SH
    for i in range(5400):
        stock_code = "60" + str(i).zfill(4)
        downloader.download_company_info(stock_code)

# # 使用示例
# stock_code = '000001'  # 平安银行的股票代码

# info_downloader = CompanyInfoDownloader()
# result = info_downloader.download_company_info(stock_code)
# if result:
#     print("\n公司信息预览：")
#     print(info_downloader.load_company_info(stock_code))
# else:
#     print("下载失败")

