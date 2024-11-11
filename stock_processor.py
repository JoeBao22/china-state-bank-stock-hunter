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