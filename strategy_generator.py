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
        :param ratio1: 买入阈值，当PRICE_MA_RATIO < ratio1时买入
        :param ratio2: 卖出阈值，当PRICE_MA_RATIO > ratio2时卖出
        :param period: 周期, 'D'表示日线，'W'表示周线，'M'表示月线
        :param ma_period: MA周期
        """
        self.ratio1 = ratio1
        self.ratio2 = ratio2
        self.period = period
        self.ma_period = ma_period

    def _process_data(self, stock_data, start_date=None, end_date=None):
        processed_stock = (stock_data
            .filter_by_date(start_date, end_date)
            .aggregate_by_period(self.period)
            .calculate_ma([self.ma_period]))

        df = processed_stock.df.copy()
        df['PRICE_MA_RATIO'] = df['收盘'] / df[f'MA{self.ma_period}']
        return df

    def _generate_signals(self, df):
        signals = pd.DataFrame(index=df.index)
        signals['日期'] = df['日期']
        signals['收盘'] = df['收盘']
        signals[f'MA{self.ma_period}'] = df[f'MA{self.ma_period}']
        signals['PRICE_MA_RATIO'] = df['PRICE_MA_RATIO']

        # 生成买入信号（1）和卖 出信号（-1）
        signals['SIGNAL'] = 0
        valid_data = signals[f'MA{self.ma_period}'].notna()
        signals.loc[valid_data & (signals['PRICE_MA_RATIO'] < self.ratio1), 'SIGNAL'] = 1
        signals.loc[valid_data & (signals['PRICE_MA_RATIO'] > self.ratio2), 'SIGNAL'] = -1
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
                entry_ratio = row['PRICE_MA_RATIO']
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
                        '买入时指标': entry_ratio,
                        '卖出日期': row['日期'],
                        '卖出价格': exit_price,
                        '卖出时指标': row['PRICE_MA_RATIO'],
                        '收益率': profit_pct,
                        '最大收益率': max_profit_pct,
                        '回撤率': drawdown_pct
                    })

        return pd.DataFrame(trades)
