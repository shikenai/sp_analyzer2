from django.core.management.base import BaseCommand
import pandas as pd
from sp_analyzer2.settings import BASE_DIR
from myapp.models import Brand, Trades, YenRate
import time
from django_pandas.io import read_frame
import datetime
import numpy as np
from myapp.management.commands import analyzer_pycaret


def set_sanyaku(row):
    # set_ichimoku_cloud()後に使用するもの。三役好転か、三役暗転かどうかを判定する
    if row["conversion_line"] > row["base_line"] and row["lagging_span"] > row["Close"] > row["leading_span1"] and \
            row["Close"] > row["leading_span2"]:
        row["sanyaku"] = True
    elif row["conversion_line"] < row["base_line"] and row["lagging_span"] < row["Close"] < row[
        "leading_span1"] and row["Close"] < row["leading_span2"]:
        row["sanyaku"] = False
    else:
        row["sanyaku"] = None
    # set_ichimoku_cloud()後に使用するもの。終値が雲の上にあるのか下にあるのかを判定する
    if row["Close"] > row["leading_span1"] and row["Close"] > row["leading_span2"]:
        row["over_cloud"] = True
    else:
        row["over_cloud"] = False
    return row


def set_ichimoku_cloud(df):
    # 一目均衡表に関するデータを作成
    additional_dates = pd.date_range(
        start=df["Date"].max() + datetime.timedelta(days=1),
        end=df["Date"].max() + datetime.timedelta(days=25),
    )

    df = pd.concat([df, pd.DataFrame(additional_dates, columns=["Date"])], ignore_index=True)
    # 基準線
    high26 = df["High"].rolling(window=26).max()
    low26 = df["Low"].rolling(window=26).min()
    df["base_line"] = (high26 + low26) / 2
    # 転換線
    high9 = df["High"].rolling(window=9).max()
    low9 = df["Low"].rolling(window=9).min()
    df["conversion_line"] = (high9 + low9) / 2
    # 先行スパン1
    leading_span1 = (df["base_line"] + df["conversion_line"]) / 2
    df["leading_span1"] = leading_span1.shift(25)

    # 先行スパン2
    high52 = df["High"].rolling(window=52).max()
    low52 = df["Low"].rolling(window=52).min()
    leading_span2 = (high52 + low52) / 2
    df["leading_span2"] = leading_span2.shift(25)

    # 遅行スパン
    df["lagging_span"] = df["Close"].shift(-25)

    return df


def compare_2columns(df, column1, column2):
    df["{}_minus_{}".format(column1, column2)] = df[column1] - df[column2]


# ------MACD--start------
# 指数平滑移動平均計算
def calc_ema(prices, period):
    ema = np.zeros(len(prices))
    ema[:] = np.nan  # NaN で初期化
    ema[period - 1] = prices[:period].mean()  # 最初だけ単純移動平均
    for d in range(period, len(prices)):
        ema[d] = ema[d - 1] + (prices[d] - ema[d - 1]) / (period + 1) * 2
    return ema


# MACD 計算
def calc_macd(prices, period_short, period_long, period_signal):
    ema_short = calc_ema(prices, period_short)
    ema_long = calc_ema(prices, period_long)
    macd = ema_short - ema_long  # MACD = 短期移動平均 - 長期移動平均
    signal = pd.Series(macd).rolling(period_signal).mean()  # シグナル = MACD の移動平均
    hist = macd - signal
    hist_rate = hist / prices
    return macd, signal, hist, hist_rate


def set_macd(df):
    df['macd_line'], df['macd_signal'], df['macd_hist'], df['macd_hist_rate'] = calc_macd(df.Close, 12, 26, 9)
    return df


# ------MACD---end-------
def operate_single_column(df, column, **kwargs):
    # 指定した一つの列に対して、前日との差分及びその率並びに移動平均を取得するもの
    # 使用例：一昨日と昨日の終値の異動、異動/終値（終値からみて、どの程度異動したのか）
    if kwargs.get('diff'):
        df["diff_{}".format(column)] = df[column].diff()
    if kwargs.get('diff_pct'):
        df["diff_pct_{}".format(column)] = df[column].pct_change()
    if kwargs.get('ma_span'):
        for span in kwargs['ma_span']:
            df["{}MA_{}".format(span, column)] = df[column].rolling(span).mean()


def operate_double_columns(df, column1, column2, **kwargs):
    if kwargs.get('size_comparison'):
        df["{}_gt_{}".format(column1, column2)] = df[column1] - df[column2]
    if kwargs.get('size_comparison_pct'):
        x = "{}_minus_{}".format(column1, column2)
        df[x] = df[column1] - df[column2]
        df["{}_/_{}_pct".format(column1, column2)] = df[x] / df[column1]


def set_gdx(row, short, long, name):
    new_column = "trend_by_{}".format(name)
    # short（短期）が上昇
    if row[short] > 0:
        # 短期上昇
        if row[long] < 0:
            row[new_column] = "買い"
        else:
            if row[short] >= row[long]:
                # 短期の上昇が長期の上昇より強い
                row[new_column] = "まだ上昇"
            else:
                # 短期の上昇が長期の上昇よりも緩い
                row[new_column] = "注意"
    else:
        # 短期が下降
        if row[long] > 0:
            row[new_column] = "下降！"
        else:
            if row[short] > row[long]:
                row[new_column] = '好転？'
            else:
                row[new_column] = 'まだまだ暗黒'
    return row


def preprocessing(brand, cnt):
    pd.set_option('display.max_columns', None)
    _brand = Brand.objects.get(code=brand.split(".")[0], nation=brand.split(".")[1])
    division = _brand.industry_division_1
    _trades = Trades.objects.filter(brand_code=brand).order_by("Date")
    n = _trades.count()
    x = cnt
    if n < x:
        n_minus = 0
    else:
        n_minus = n - x
    _df = read_frame(_trades.all()[n_minus:n])
    rate_yd = YenRate.objects.order_by("Date")
    df_yd = read_frame(rate_yd.all())
    df = pd.merge(_df, df_yd, left_on='Date', right_on='Date', how='inner')
    df = df.drop(["id_x", "id_y", "brand", "brand_code"], axis=1)

    operate_single_column(df, 'rate', diff=True, diff_pct=True, ma_span=[3])
    operate_single_column(df, 'Volume', diff=True, diff_pct=True, ma_span=[])
    # # Close列に対して、変化推移、変化率、３日移動平均、２５日移動平均を追加
    operate_single_column(df, "Close", diff=True, diff_pct=True, ma_span=[3, 25])
    operate_double_columns(df, "3MA_Close", "25MA_Close", size_comparison=True)
    df = df.apply(set_gdx, args=("3MA_Close", "25MA_Close", 'MA'), axis=1)
    operate_single_column(df, '3MA_Close_gt_25MA_Close', diff=True, diff_pct=True, ma_span=[3])

    df = set_ichimoku_cloud(df)
    df = df.apply(set_sanyaku, axis=1)
    df = set_macd(df)
    df = add_bb_rsi_sc(df)

    # 三日分を分析させるときに使用①　（②もあるよ）
    list_shift_num = [1, 2]
    df = shift_and_rename_columns_name(df, list_shift_num)

    df = df[26:]
    df = df.reset_index(drop=True)
    col_num = df.columns.get_loc('Close')
    n = 21
    index_num = df.shape[0]
    division_list = []
    max_list = []
    for i in range(index_num):
        division_list.append(division)
        if i + n <= index_num:
            max_list.append(df.iloc[i + 1:i + n, [col_num]].max().max())
        else:
            max_list.append(np.nan)
    column_name = "{}日後までの最大値".format(n)
    df[column_name] = max_list
    df['division'] = division_list
    operate_double_columns(df, column_name, "Close", size_comparison_pct=True)
    # df = df[
    #     ['Date', 'Close', '3MA_Close', '25MA_Close', 'trend_by_MA', '3MA_3MA_Close_gt_25MA_Close', '21日後までの最大値',
    #      "21日後までの最大値_/_Close_pct"]]
    # df = df.rename(
    #     columns={'Date': '日付', 'Close': '終値', '3MA_Close': '短期移動平均（３日）', '25MA_Close': '短期移動平均（25日）',
    #              'trend_by_MA': 'シグナル（移動平均）', '3MA_3MA_Close_gt_25MA_Close': 'シグナル（オリジナル）',
    #              '21日後までの最大値_/_Close_pct': '21日後までの最大値（伸び率）'})

    _target_index_list = ["Close", "Volume", "diff_pct_3MA_Close_gt_25MA_Close", "rate", "diff_pct_rate",
                          "trend_by_MA", "macd_hist_rate", "21日後までの最大値_/_Close_pct", "diff_pct_Volume", 'division',
                          'over_cloud', 'Upper_band', 'Lower_band', 'RSI']
    target_index_list = _target_index_list

    # 三日分を分析させるときに使用②　（①もあるよ）
    remove_list = []
    for num in list_shift_num:
        new_list = [f'shift{str(num)}_{str(c)}' for c in _target_index_list]
        target_index_list = target_index_list + new_list
        remove_list.append(f'shift{str(num)}_21日後までの最大値_/_Close_pct')
        remove_list.append(f'shift{str(num)}_division')
    # remove_list = ['shift1_21日後までの最大値_/_Close_pct', 'shift2_21日後までの最大値_/_Close_pct', 'shift1_division', 'shift2_division']
    for item in remove_list:
        target_index_list.remove(item)

    _last_df = df[target_index_list]
    last_df = _last_df[7:_last_df.shape[0] - 26]
    last_df.rename(columns={"21日後までの最大値_/_Close_pct": 'target'}, inplace=True)
    # print(last_df.columns)
    # analyzer_pycaret.save_test(last_df, "target")
    # analyzer_pycaret.load_test(last_df)
    return last_df


def shift_and_rename_columns_name(df, list_shift_num):
    old_columns = list(df.columns)
    for num in list_shift_num:
        new_columns = [f'shift{str(num)}_{str(c)}' for c in old_columns]
        switch_columns = dict(zip(old_columns, new_columns))
        shifted_df = df[old_columns].shift(num).rename(columns=switch_columns)
        df = pd.concat([df, shifted_df], axis=1)
    # print(merged_df)
    return df


def add_bb_rsi_sc(df, n_fast=12, n_slow=26, n_signal=9, n_std=2, n_rsi=14):
    df['MA_slow'] = df['Close'].rolling(n_slow).mean()
    df['Std'] = df['Close'].rolling(n_std).mean()
    df['Upper_band'] = df["MA_slow"] + n_std * df['Std']
    df['Upper_band'] = df['Upper_band'] / df['Close']
    df['Lower_band'] = df["MA_slow"] - n_std * df['Std']
    df['Lower_band'] = df['Lower_band'] / df['Close']
    delta = df['Close'].diff()
    up = delta.where(delta > 0, 0)
    down = delta.where(delta < 0, 0)
    df['RSI'] = up.rolling(n_rsi).mean() / (up.rolling(n_rsi).mean() + down.rolling(n_rsi).mean()) * 100

    return df


class Command(BaseCommand):
    help = "register TSE brands"

    def add_arguments(self, parser):
        parser.add_argument("first", type=str)

    def handle(self, *args, **options):
        analyze()
