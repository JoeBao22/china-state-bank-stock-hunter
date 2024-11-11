import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import sys


def set_chinese_font():
    """设置中文字体, 以确保matplotlib图表中的中文显示正常"""
    if sys.platform.startswith("win"):
        # Windows系统
        plt.rcParams["font.sans-serif"] = ["SimHei"]
    elif sys.platform.startswith("linux"):
        # Linux系统
        plt.rcParams["font.sans-serif"] = ["WenQuanYi Micro Hei"]
    elif sys.platform.startswith("darwin"):
        # MacOS系统
        plt.rcParams["font.sans-serif"] = ["PingFang HK"]

    plt.rcParams["axes.unicode_minus"] = False  # 用来正常显示负号


def calculate_ma(df, periods=[]):
    """
    计算多个周期的移动平均线，将结果添加到原始数据中
    参数:
    df: DataFrame，需要包含收盘价
    periods: 需要计算的周期列表，默认为[5, 10, 20]
    """
    df_with_ma = df.copy()
    for period in periods:
        df_with_ma[f"MA{period}"] = df["收盘"].rolling(window=period).mean()
    return df_with_ma


def aggregate_by_period(df, period="D"):
    """
    按指定周期聚合股市数据

    参数:
    df: DataFrame，包含OHLC数据
    period: 周期，'D'(日), 'W'(周), 'M'(月)
    """
    if period == "D":
        return df
    rules = {"W": "W-FRI", "M": "M"}  # 周（以周五为结束）  # 月
    # 将日期列设置为索引，方便后续重采样
    resampled = (
        df.set_index("日期")
        .resample(rules[period])
        .agg(
            {
                "开盘": "first",  # 取周期第一个开盘价
                "最高": "max",  # 取周期最高价
                "最低": "min",  # 取周期最低价
                "收盘": "last",  # 取周期最后收盘价
            }
        )
    )
    # 删除空值并重置索引
    return resampled.dropna().reset_index()


def filter_by_date(df, start_date=None, end_date=None):
    """
    根据日期筛选数据

    参数:
    df: DataFrame，需要包含日期列
    start_date: 开始日期，格式：'YYYY-MM-DD'
    end_date: 结束日期，格式：'YYYY-MM-DD'
    """
    mask = True
    if start_date:
        mask &= df["日期"] >= start_date
    if end_date:
        mask &= df["日期"] <= end_date
    return df[mask].copy()


def get_plot_title(stock_code, start_date, end_date, period):
    period_names = {"D": "日", "W": "周", "M": "月"}
    if start_date or end_date:
        date_range = f"({start_date.strftime('%Y-%m-%d') if start_date else '开始'} 至 {end_date.strftime('%Y-%m-%d') if end_date else '结束'})"
        title = f"{stock_code} - {period_names[period]}K线 {date_range}"
    else:
        title = f"{stock_code} - {period_names[period]}K线"
    return title


def plot_candlestick(
    df, period="D", start_date=None, end_date=None, ma_periods=[5, 10, 20]
):
    """
    使用matplotlib绘制K线图

    参数:
    df: DataFrame，需要包含以下列：
        - 日期
        - 开盘
        - 最高
        - 最低
        - 收盘
    title: 图表标题
    figsize: 图表大小
    start_date: 开始日期，格式：'YYYY-MM-DD'
    end_date: 结束日期，格式：'YYYY-MM-DD'
    period: 周期，'D'(日), 'W'(周), 'M'(月)
    ma_periods: 移动平均线的周期
    """
    if period not in ["D", "W", "M"]:
        raise ValueError("period必须是'D'、'W'或'M'之一")

    plot_df = calculate_ma(filter_by_date(df, start_date, end_date), ma_periods)
    if len(plot_df) == 0:
        raise ValueError("所选日期范围内没有数据")

    fig, ax = plt.subplots(figsize=(12, 8))
    # 设置背景颜色, 使得K线图更易于观察
    ax.set_facecolor("#f6f6f6")
    fig.set_facecolor("white")

    for i in range(len(plot_df)):
        open_price = plot_df["开盘"].iloc[i]
        close_price = plot_df["收盘"].iloc[i]
        high_price = plot_df["最高"].iloc[i]
        low_price = plot_df["最低"].iloc[i]

        # 确定K线颜色（红涨绿跌）
        color = "red" if close_price >= open_price else "green"

        # 绘制实体
        body_height = abs(close_price - open_price)
        bottom = min(open_price, close_price)
        rect = Rectangle((i - 0.3, bottom), 0.6, body_height, facecolor=color)
        ax.add_patch(rect)

        # 绘制上下影线
        ax.plot(
            [i, i], [high_price, max(open_price, close_price)], color=color, linewidth=0.5
        )
        ax.plot(
            [i, i], [low_price, min(open_price, close_price)], color=color, linewidth=0.5
        )

    # 绘制移动平均线
    prop_cycle = plt.rcParams["axes.prop_cycle"]
    colors = prop_cycle.by_key()["color"]

    for idx, ma_period in enumerate(ma_periods):
        ma_values = plot_df[f"MA{ma_period}"].values
        color = colors[idx % len(colors)]  # 循环使用颜色
        ax.plot(
            range(len(plot_df)),
            ma_values,
            label=f"MA{ma_period}",
            color=color,
            linewidth=2,
            alpha=0.8,
            linestyle='dashdot',
            # 'zorder': 5
        )

    num_ticks = min(10, len(plot_df))
    if num_ticks > 1:
        step = max(len(plot_df) // num_ticks, 1)
        ax.set_xticks(range(0, len(plot_df), step))
        date_format = {"D": "%Y-%m-%d", "W": "%Y-%m-%d", "M": "%Y-%m"}
        ax.set_xticklabels(
            plot_df["日期"].iloc[::step].dt.strftime(date_format[period]), rotation=45
        )

    plot_title = get_plot_title(stock_code, start_date, end_date, period)
    ax.set_title(plot_title)
    ax.set_ylabel("价格")
    ax.grid(True, linestyle="--", alpha=0.3)
    ax.legend()
    plt.tight_layout()

    return fig


if __name__ == "__main__":
    set_chinese_font()
    stock_code = "601288"
    start_date = "20210101"
    end_date = "20241231"
    period = "W"
    ma_periods = [5, 10, 20]

    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)

    csv_path = f"resource/stock_price/{stock_code}.csv"
    df = pd.read_csv(csv_path)
    df["日期"] = pd.to_datetime(df["日期"])
    aggregated_df = aggregate_by_period(df, period=period)

    fig = plot_candlestick(aggregated_df, period, start_date, end_date, ma_periods)
    plt.show()
