from abc import ABC, abstractmethod
import pandas as pd
import numpy as np

class StrategyBase(ABC):
    def apply_strategy(self, stock_data, start_date=None, end_date=None):
        processed_df = self._process_data(stock_data, start_date, end_date)
        signals = self._generate_signals(processed_df)
        trades = self._generate_trades(signals)
        return processed_df, signals, trades

    @abstractmethod
    def _process_data(self, stock_data, start_date=None, end_date=None):
        """
        处理数据，计算必要的指标
        :param stock_data: StockData对象
        :return: DataFrame，包含处理后的数据
        """
        pass

    @abstractmethod
    def _generate_signals(self, df):
        """
        生成交易信号
        :param df: DataFrame，包含必要的交易数据
        :return: DataFrame，包含信号
        """
        pass

    @abstractmethod
    def _generate_trades(self, signals):
        """
        根据信号生成交易记录
        :param signals: DataFrame，包含交易信号
        :return: DataFrame，包含交易记录
        """
        pass


class MAStrategy(StrategyBase):

    def __init__(self, ratio1, ratio2, period, ma_period):
        """
        初始化MA策略
        :param ratio1: 买入阈值，当指标值 < ratio1时买入
        :param ratio2: 卖出阈值，当指标值 > ratio2时卖出
        :param period: 周期, 'D'表示日线，'W'表示周线，'M'表示月线
        :param ma_period: MA周期
        """
        self.ratio1 = ratio1
        self.ratio2 = ratio2
        self.period = period
        self.ma_period = ma_period
        self.new_feature_columns = [f'MA{ma_period}']
        self.new_indicator_columns = ['收盘/MA']

    def _process_data(self, stock_data, start_date=None, end_date=None):
        processed_stock = (stock_data
            .filter_by_date(start_date, end_date)
            .aggregate_by_period(self.period)
            .calculate_ma([self.ma_period]))

        df = processed_stock.df.copy()
        df['收盘/MA'] = df['收盘'] / df[f'MA{self.ma_period}']
        return df

    def _generate_signals(self, df):
        signals = pd.DataFrame(index=df.index)
        signals['日期'] = df['日期']
        signals['收盘'] = df['收盘']
        signals[f'MA{self.ma_period}'] = df[f'MA{self.ma_period}']
        signals['收盘/MA'] = df['收盘/MA']

        # 生成买入信号（1）和卖 出信号（-1）
        signals['SIGNAL'] = 0
        valid_data = signals[f'MA{self.ma_period}'].notna()
        signals.loc[valid_data & (signals['收盘/MA'] < self.ratio1), 'SIGNAL'] = 1
        signals.loc[valid_data & (signals['收盘/MA'] > self.ratio2), 'SIGNAL'] = -1
        return signals

    def _generate_trades(self, signals):
        """生成交易记录"""
        trades = []
        position = 0
        entry_price = 0
        entry_date = None
        max_price = 0

        for idx, row in signals.iterrows():
            if pd.isna(row[f'MA{self.ma_period}']):
                continue

            if position == 0 and row['SIGNAL'] == 1:  # 买入
                position = 1
                entry_price = row['收盘']
                entry_date = row['日期']
                entry_ratio = row['收盘/MA']
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
                        '买入时收盘/MA指标': entry_ratio,
                        '卖出日期': row['日期'],
                        '卖出价格': exit_price,
                        '卖出时收盘/MA指标': row['收盘/MA'],
                        '收益率': profit_pct,
                        '最大收益率': max_profit_pct,
                        '回撤率': drawdown_pct
                    })

        return pd.DataFrame(trades)


class KDJStrategy(StrategyBase):
    def __init__(self, n=9, m1=3, m2=3, period='D'):
        """
        初始化KDJ策略
        :param n: RSV周期
        :param m1: K值周期
        :param m2: D值周期
        :param period: 周期, 'D'表示日线，'W'表示周线，'M'表示月线
        """
        self.n = n
        self.m1 = m1
        self.m2 = m2
        self.period = period
        self.new_feature_columns = ['KDJ_K', 'KDJ_D', 'KDJ_J']
        self.new_indicator_columns = ['K-D']

    def _process_data(self, stock_data, start_date=None, end_date=None):
        """处理数据，计算KDJ指标"""
        processed_stock = (stock_data
            .filter_by_date(start_date, end_date)
            .aggregate_by_period(self.period)
            .calculate_kdj(self.n, self.m1, self.m2))
            
        df = processed_stock.df.copy()
        df['K-D'] = df['KDJ_K'] - df['KDJ_D']
        return df

    def _generate_signals(self, df):
        """生成交易信号"""
        signals = pd.DataFrame(index=df.index)
        signals['日期'] = df['日期']
        signals['收盘'] = df['收盘']
        signals['KDJ_K'] = df['KDJ_K']
        signals['KDJ_D'] = df['KDJ_D']
        signals['KDJ_J'] = df['KDJ_J']
        
        # 生成金叉死叉信号
        signals['SIGNAL'] = 0
        signals['K-D'] = df['K-D']
        valid_data = signals['KDJ_K'].notna() & signals['KDJ_D'].notna()
        
        # 金叉：K线从下向上穿过D线
        golden_cross = (df['KDJ_K'] > df['KDJ_D']) & (df['KDJ_K'].shift(1) <= df['KDJ_D'].shift(1))
        # 死叉：K线从上向下穿过D线
        death_cross = (df['KDJ_K'] < df['KDJ_D']) & (df['KDJ_K'].shift(1) >= df['KDJ_D'].shift(1))
        
        signals.loc[valid_data & golden_cross, 'SIGNAL'] = 1
        signals.loc[valid_data & death_cross, 'SIGNAL'] = -1
        
        return signals

    def _generate_trades(self, signals):
        """生成交易记录"""
        trades = []
        position = 0
        entry_price = 0
        entry_date = None
        max_price = 0
        
        for idx, row in signals.iterrows():
            if pd.isna(row['KDJ_K']) or pd.isna(row['KDJ_D']):
                continue
                
            if position == 0 and row['SIGNAL'] == 1:  # 金叉买入
                position = 1
                entry_price = row['收盘']
                entry_date = row['日期']
                entry_k = row['KDJ_K']
                entry_d = row['KDJ_D']
                max_price = entry_price
                
            elif position == 1:  # 持仓期间更新最高价
                max_price = max(max_price, row['收盘'])
                if row['SIGNAL'] == -1:  # 死叉卖出
                    position = 0
                    exit_price = row['收盘']
                    profit_pct = (exit_price / entry_price - 1) * 100
                    max_profit_pct = (max_price / entry_price - 1) * 100
                    drawdown_pct = (exit_price / max_price - 1) * 100
                    
                    trades.append({
                        '买入日期': entry_date,
                        '买入价格': entry_price,
                        '买入时K-D指标': entry_k - entry_d,
                        '卖出日期': row['日期'],
                        '卖出价格': exit_price,
                        '卖出时K-D指标': row['KDJ_K'] - row['KDJ_D'],
                        '收益率': profit_pct,
                        '最大收益率': max_profit_pct,
                        '回撤率': drawdown_pct
                    })
                    
        return pd.DataFrame(trades)



class MACDStrategy(StrategyBase):
    def __init__(self, fast_period=12, slow_period=26, signal_period=9, period='D'):
        """
        初始化MACD策略
        :param fast_period: 快速EMA周期
        :param slow_period: 慢速EMA周期
        :param signal_period: 信号线周期
        :param period: 周期, 'D'表示日线，'W'表示周线，'M'表示月线
        """
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.signal_period = signal_period
        self.period = period
        self.new_feature_columns = ['MACD_DIF', 'MACD_DEA', 'MACD_HIST']
        self.new_indicator_columns = ['MACD_HIST']

    def _process_data(self, stock_data, start_date=None, end_date=None):
        """处理数据，计算MACD指标"""
        processed_stock = (stock_data
            .filter_by_date(start_date, end_date)
            .aggregate_by_period(self.period)
            .calculate_macd(self.fast_period, self.slow_period, self.signal_period))
            
        return processed_stock.df.copy()

    def _generate_signals(self, df):
        """生成交易信号"""
        signals = pd.DataFrame(index=df.index)
        signals['日期'] = df['日期']
        signals['收盘'] = df['收盘']
        signals['MACD_DIF'] = df['MACD_DIF']
        signals['MACD_DEA'] = df['MACD_DEA']
        signals['MACD_HIST'] = df['MACD_HIST']
        
        # 生成金叉死叉信号
        signals['SIGNAL'] = 0
        valid_data = signals['MACD_DIF'].notna() & signals['MACD_DEA'].notna()
        
        # 金叉：DIF从下向上穿过DEA
        golden_cross = (df['MACD_DIF'] > df['MACD_DEA']) & (df['MACD_DIF'].shift(1) <= df['MACD_DEA'].shift(1))
        # 死叉：DIF从上向下穿过DEA
        death_cross = (df['MACD_DIF'] < df['MACD_DEA']) & (df['MACD_DIF'].shift(1) >= df['MACD_DEA'].shift(1))
        
        signals.loc[valid_data & golden_cross, 'SIGNAL'] = 1
        signals.loc[valid_data & death_cross, 'SIGNAL'] = -1
        
        return signals

    def _generate_trades(self, signals):
        """生成交易记录"""
        trades = []
        position = 0
        entry_price = 0
        entry_date = None
        max_price = 0
        
        for idx, row in signals.iterrows():
            if pd.isna(row['MACD_DIF']) or pd.isna(row['MACD_DEA']):
                continue
                
            if position == 0 and row['SIGNAL'] == 1:  # 金叉买入
                position = 1
                entry_price = row['收盘']
                entry_date = row['日期']
                entry_dif = row['MACD_DIF']
                entry_dea = row['MACD_DEA']
                entry_hist = row['MACD_HIST']
                max_price = entry_price
                
            elif position == 1:  # 持仓期间更新最高价
                max_price = max(max_price, row['收盘'])
                if row['SIGNAL'] == -1:  # 死叉卖出
                    position = 0
                    exit_price = row['收盘']
                    profit_pct = (exit_price / entry_price - 1) * 100
                    max_profit_pct = (max_price / entry_price - 1) * 100
                    drawdown_pct = (exit_price / max_price - 1) * 100
                    
                    trades.append({
                        '买入日期': entry_date,
                        '买入价格': entry_price,
                        '买入时MACD_HIST指标': entry_hist,
                        '买入时DIF-DEA差值': entry_dif - entry_dea,
                        '卖出日期': row['日期'],
                        '卖出价格': exit_price,
                        '卖出时MACD_HIST指标': row['MACD_HIST'],
                        '卖出时DIF-DEA差值': row['MACD_DIF'] - row['MACD_DEA'],
                        '收益率': profit_pct,
                        '最大收益率': max_profit_pct,
                        '回撤率': drawdown_pct
                    })
                    
        return pd.DataFrame(trades)