import os
import time
import random
# 需要先安装akshare，可使用pip install akshare
import akshare as ak 


def download_stock_price(stock_code, start_date, end_date, adj, period, folder_path):
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    print("正在下载", stock_code, "的历史行情数据...")
    try:
        # 通过akshare从东方财富网下载股票数据。接口文档：
        # https://github.com/akfamily/akshare/blob/c8adcd5be6c833d99bc05cbb2ab1d3aed8b86d4e/akshare/stock_feature/stock_hist_em.py#L1015
        stock_price_df = ak.stock_zh_a_hist(symbol=stock_code, start_date=start_date, end_date=end_date, adjust=adj, period=period)
        stock_path = os.path.join(folder_path, stock_code + '.csv')
        stock_price_df.to_csv(stock_path, index=False, mode='w', encoding='utf-8')
    except Exception as e:
        print("下载失败:", e)
    print("下载完成", stock_code, "的历史行情数据。")
    time.sleep(random.uniform(300, 1000) / 100)


if __name__ == '__main__':
    print("akshare版本:", ak.__version__)
    start_date = '20140101'
    end_date = time.strftime('%Y%m%d', time.localtime(time.time()))
    adj = 'qfq'
    period = 'daily'
    stock_codes = {
        '601398': '工商银行',
        '601939': '建设银行',
        '601288': '农业银行',
        '601988': '中国银行',
        '601328': '交通银行',
    }
    folder_path = "resource/stock_price"

    for stock_code in stock_codes.keys():
        download_stock_price(stock_code, start_date, end_date, adj, period, folder_path)


