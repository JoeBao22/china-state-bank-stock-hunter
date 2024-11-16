import pandas as pd

class StockDataProcessor:
    @staticmethod
    def filter_by_date(df, start_date=None, end_date=None):
        filtered_df = df.copy()
        if start_date:
            filtered_df = filtered_df[filtered_df['日期'] >= start_date]
        if end_date:
            filtered_df = filtered_df[filtered_df['日期'] <= end_date]
        return filtered_df

    @staticmethod
    def calculate_ma(df, periods=[]):
        processed_df = df.copy()
        for period in periods:
            processed_df[f'MA{period}'] = processed_df['收盘'].rolling(window=period).mean()
        return processed_df

    @staticmethod
    def calculate_kdj(df, n=9, m1=3, m2=3):
        processed_df = df.copy()
        low_list = processed_df['最低'].rolling(window=n).min()
        high_list = processed_df['最高'].rolling(window=n).max()
        rsv = (processed_df['收盘'] - low_list) / (high_list - low_list) * 100

        k = rsv.ewm(alpha=1/m1, adjust=False).mean()
        d = k.ewm(alpha=1/m2, adjust=False).mean()
        j = 3 * k - 2 * d
        
        processed_df['KDJ_K'] = k
        processed_df['KDJ_D'] = d
        processed_df['KDJ_J'] = j
        return processed_df
        
    @staticmethod
    def aggregate_by_period(df, period='D'):
        if period not in ['D', 'W', 'M']:
            raise ValueError("period必须是'D'、'W'或'M'之一")
        if period == 'D':
            return df.copy()
        rules = {'W': 'W-FRI', 'M': 'M'}
        resampled = (df.set_index('日期')
                    .resample(rules[period])
                    .agg({
                        '开盘': 'first',
                        '最高': 'max',
                        '最低': 'min',
                        '收盘': 'last',
                    }))
        return resampled.dropna().reset_index()

    @staticmethod
    def calculate_macd(df, fast_period=12, slow_period=26, signal_period=9):
        """
        计算MACD技术指标
        
        参数:
        df: DataFrame，必须包含'收盘'列
        fast_period: 快速EMA周期，默认12
        slow_period: 慢速EMA周期，默认26
        signal_period: 信号线DIF的EMA周期，默认9
        
        返回:
        DataFrame，包含原始数据及MACD指标数据
        """
        processed_df = df.copy()
        
        # 计算快速和慢速指数移动平均线
        fast_ema = processed_df['收盘'].ewm(span=fast_period, adjust=False).mean()
        slow_ema = processed_df['收盘'].ewm(span=slow_period, adjust=False).mean()
        
        # 计算MACD线（DIF）
        processed_df['MACD_DIF'] = fast_ema - slow_ema
        
        # 计算信号线（DEA）
        processed_df['MACD_DEA'] = processed_df['MACD_DIF'].ewm(span=signal_period, adjust=False).mean()
        
        # 计算MACD柱状图（HIST）
        processed_df['MACD_HIST'] = 2 * (processed_df['MACD_DIF'] - processed_df['MACD_DEA'])
        
        return processed_df