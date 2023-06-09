import datetime

from django.core.management.base import BaseCommand
import pandas as pd
from sp_analyzer2.settings import BASE_DIR
from myapp.models import Brand, Trades, YenRate
import time
import pandas_datareader.data as data
import pandas_datareader as pdr
import datetime as dt
import os
from django_pandas.io import read_frame
import glob
import yfinance as yf


# ----------ここからシステム環境再構築時に使用するもの----------
def reg_brands_from_csv():
    # システム環境再構築時に使うことを想定
    # djangoで吐き出したcsvを新規プロジェクトに移築する時に使ってください
    # とりあえず旧プロジェクトで吐き出したcsvをdataframeとして取得
    df = pd.read_csv(BASE_DIR / "data/brand.csv")
    # よくわからんけど、ググった結果、to_dict(orient='records')すれば良いらしい
    de_records = df.to_dict(orient='records')
    # あとでbulk_createする際に使用する空のリスト
    model_inserts = []
    for d in de_records:
        model_inserts.append(Brand(
            nation=d["nation"],
            market=d["market"],
            name=d["brand_name"],
            code=d["code"],
            division=d["division"],
            industry_code_1=d["industry_code_1"],
            industry_division_1=d["industry_division_1"],
            industry_code_2=d["industry_code_2"],
            industry_division_2=d["industry_division_2"],
            scale_code=d["scale_code"],
            scale_division=d["scale_division"]
        ))
    Brand.objects.bulk_create(model_inserts)


def reg_trades_from_csv():
    # システム環境再構築時に使うことを想定
    # djangoで吐き出したcsvを新規プロジェクトに移築する時に使ってください
    # とりあえず旧プロジェクトで吐き出したcsvをdataframeとして取得
    df = pd.read_csv(BASE_DIR / "data/trade.csv")
    # よくわからんけど、ググった結果、to_dict(orient='records')すれば良いらしい
    de_records = df.to_dict(orient='records')
    # あとでbulk_createする際に使用する空のリスト
    model_inserts = []
    for d in de_records:
        model_inserts.append(Trades(
            brand=Brand.objects.get(code=d["brand_code"].split(".")[0], nation=d["brand_code"].split(".")[1]),
            brand_code=d["brand_code"],
            Date=d["trade_date"],
            Open=d["open_value"],
            Close=d["close_value"],
            High=d["high_value"],
            Low=d["low_value"],
            Volume=d["volume"]
        ))
    Trades.objects.bulk_create(model_inserts)


def get_initial_brands_from_tse():
    # 東証からダウンロードしてきた銘柄情報をそのまま登録するときに使うコード
    df = pd.read_csv(BASE_DIR / "data/before_brand.csv")
    df_records = df.to_dict(orient='records')
    model_inserts = []
    for d in df_records:
        model_inserts.append(Brand(
            nation="jp",
            market="東証一部",
            name=d["銘柄名"],
            code=d["コード"],
            division=d["市場・商品区分"],
            industry_code_1=d["17業種コード"],
            industry_division_1=d["17業種区分"],
            industry_code_2=d["33業種コード"],
            industry_division_2=d["33業種区分"],
            scale_code=d["規模コード"],
            scale_division=d["規模区分"]
        ))
    Brand.objects.bulk_create(model_inserts)


def get_initial_trades_from_csv():
    # google colabで取得してきた取引情報をcsvにした後に実行するコード
    print('get_initial_trades_from_stooq()')
    n = 0
    t1 = time.time()
    all_files = os.path.join(BASE_DIR, 'data', 'trades', '*')
    print(all_files)
    files = glob.glob(all_files)
    for f in files:
        df = pd.read_csv(f, header=[0, 1])
        df = df.swaplevel(axis=1).sort_index(axis=1)
        df = df.reset_index(drop=True)
        df_date = df[["Symbols"]].droplevel(0, axis=1).drop(0).rename(columns={"Attributes": "Date"})

        df = df.drop("Symbols", axis=1)

        model_inserts = []
        list_brand = []
        for i in df.columns:
            if not i[0] in list_brand:
                list_brand.append(i[0])
                _df = pd.concat([df[i[0]].reset_index(drop=True), df_date], axis=1).drop(0)
                _df = _df.dropna()
                _df["Volume"] = _df["Volume"].round()
                _df["Date"] = pd.to_datetime(_df["Date"])
                df_records = _df.to_dict(orient='records')
                _brand = Brand.objects.get(code=i[0].split(".")[0], nation=i[0].split(".")[1])
                for d in df_records:
                    model_inserts.append(Trades(
                        brand=_brand,
                        brand_code=i[0],
                        Date=d["Date"],
                        Open=d["Open"],
                        Close=d["Close"],
                        High=d["High"],
                        Low=d["Low"],
                        Volume=d["Volume"]
                    ))
        Trades.objects.bulk_create(model_inserts)
    print(time.time() - t1)


# ----------ここまでシステム環境再構築時に使用するもの----------

# ----------ここから日々の取引データ取得に関するもの----------
def get_trades_from_stooq():
    print('from stppq')
    target = "nikkei"
    get_target_brands('jp', target)
    t1 = time.time()
    # パターン１　既にある程度の取引情報データを保有しているもの
    # get_target_brands("jp")[0] は、既にある程度の取引状況をデータとして保有しているもの
    # →各銘柄ごとの、取引最終日を取得し、その日以降のデータを取得する必要があるため、listで取得
    owned_brands = get_target_brands('jp', target)[0]
    # 一旦、現在保有している全ての取引情報をdataframeにする
    print('aaa')
    df = read_frame(Trades.objects.all().order_by("Date"))
    print(df)
    # 取引情報のうち、今回の処理に必要なtrade_date, brand_codeのみを抽出する
    # この際、groupby("brand_code").max()　により、格銘柄ごとに現在取得している取引最終日をdataframeとして取得する
    df = df[["Date", "brand_code"]].groupby("brand_code").max()
    # 扱いやすいようにマルチインデックスを解除する
    df = df.reset_index()
    # 既に保有している銘柄に誤りがないか確認
    df = df[df["brand_code"].isin(owned_brands)]
    # あとで処理しやすいように、対象銘柄ごとの取引最終日を、重複なしでリストとして取得
    target_trade_date_list = df["Date"].sort_values().drop_duplicates().to_list()
    returning_list = []
    # stooq APIを利用するときに扱いやすいよう、[ {"key=trade_date": "value=[brand_codes]"} ]
    # という形に整える
    for i in range(len(target_trade_date_list)):
        a = df[df["Date"] == target_trade_date_list[i]]["brand_code"].to_list()
        returning_list.append({target_trade_date_list[i]: a})

    for c in returning_list:
        for last_date, brand_code in c.items():
            if last_date + dt.timedelta(days=60) > dt.date.today():
                print("-----------")
                print(last_date)
                print(brand_code)
                print(last_date + dt.timedelta(days=1))
                print(returning_list)
                if not len(returning_list) == 0:
                    _df = data.DataReader(brand_code, "stooq", last_date + dt.timedelta(days=1), datetime.date.today())
                    register_from_stooq_use_multi_columns_df(_df)
                    time.sleep(2)
    # →全ての銘柄について、一律指定した日からデータ取得日までのデータを取得すれば良い
    new_brands = get_target_brands('jp', target)[1]
    print(new_brands)
    if not len(new_brands) == 0:
        _df = data.DataReader(new_brands, "stooq", dt.date(2018, 1, 1), datetime.date.today())
        register_from_stooq_use_multi_columns_df(_df)
    # ここはもう一括でstooqから取得すれば良いので楽
    print(time.time() - t1)


def register_from_stooq_use_multi_columns_df(_df_multi_columns):
    # stooq-apiから、銘柄をリストで指定してデータを取得すると、
    # multi_columnになっていて使いづらそうだったので、使いやすい形に直す。
    # ついでに、一括登録しておくことにする。
    print('START reg multi')
    # まず、取得してきたdfのカラムを整理
    df = _df_multi_columns.swaplevel(0, 1, axis=1).sort_index(axis=1)
    # 取得してきたdfに存在する銘柄のコードを取得（"7203.jp"形式）してリスト化
    list_brand = []
    for i in df.columns:
        if not i[0] in list_brand:
            list_brand.append(i[0])
    print(list_brand)
    # あとでbulk_createするため、空のリストを作成しておく
    model_inserts = []
    # dfの中にあった銘柄を一件ずつ処理していく
    for brand in list_brand:
        # multi_columnだったdfから、指定した銘柄分のみを抽出し、インデックスを整理
        _df = df[brand].reset_index()
        if 'index' in _df.columns:
            _df = _df.rename(columns={'index': 'Date'})
        # queryの実行回数を減らすために、銘柄のmodelを取得しておく
        _brand = Brand.objects.get(code=brand.split(".")[0], nation=brand.split(".")[1])
        df_records = _df.to_dict(orient='records')
        for d in df_records:
            model_inserts.append(Trades(
                # _brand = 先ほど取得しておいた銘柄のmodel
                brand=_brand,
                # brand = list_brandの中に格納しておいた、銘柄コード（"7203.jp"形式）
                brand_code=brand,
                # ここから下は、dから取得する
                Date=d["Date"],
                Open=d["Open"],
                Close=d["Close"],
                High=d["High"],
                Low=d["Low"],
                Volume=d["Volume"]
            ))
    Trades.objects.bulk_create(model_inserts)
    print('DONE reg multi')


def sort_out_2lists(list1, list2):
    # get_target_brands関数で使用するもの
    # ベン図の交わる部分
    intersection = list(set(list1) & set(list2))
    # ベン図のうち、どちらかに含まれる部分
    union_minus_intersection = list(set(list1) ^ set(list2))
    # ベン図のうち、list1にのみ含まれる部分
    only_list1 = list(set(list1) & set(union_minus_intersection))
    # ベン図のうち、list2にのみ含まれる部分
    only_list2 = list(set(list2) & set(union_minus_intersection))
    return intersection, only_list1, only_list2


def get_target_brands(nation, target):
    print('get target brands')
    # 取引情報を取得するにあたり、①既にある程度取引情報を持っている銘柄　②全く取引情報を持っていない銘柄　の２種類で
    # 処理方法を分ける必要があるため、①と②を分ける処理を行う。
    # この際、自作関数sort_out_2_listsを使用する。
    # returnの一つ目は、２つのリストの交わる部分、二つ目はリスト１にのみ存在する部分、三つ目はリスト２にのみ存在する部分
    # なお、将来海外銘柄を取り扱う可能性を考慮し、引数としてnationをもつ。日本株の場合は一律"jp"

    # 最新の銘柄リスト
    if target == "nikkei":
        print("nikkei")
        list_csv_brand = list(pd.read_csv(BASE_DIR / "data/nikkei_listed_20230313_.csv")["0"])
    elif target == "all":
        print('all')
        list_csv_brand = list(pd.read_csv(BASE_DIR / "data/before_brand.csv")["コード"])  # ここでは数値として取得しているみたい
    list_csv_brand_str = [str(c) + "." + nation for c in list_csv_brand]  # だから文字列に変換する
    # tradesに登録済の銘柄リスト
    brands_in_trades = list(Trades.objects.all().order_by("brand_code").distinct().values_list('brand_code', flat=True))
    print('done get target brands')
    print(len(brands_in_trades))
    # sort_out_2lists(list_csv_brand_str, brands_in_trades)[0]) は、list_csv_brand_strとbrands_in_tradesのどちらにも存在する銘柄
    # sort_out_2lists(list_csv_brand_str, brands_in_trades)[1]) は、list_csv_brand_strにのみ存在する銘柄
    # sort_out_2lists(list_csv_brand_str, brands_in_trades)[2]) は、brands_in_tradesにのみ存在する銘柄
    print(len(sort_out_2lists(list_csv_brand_str, brands_in_trades)[2]))
    return sort_out_2lists(list_csv_brand_str, brands_in_trades)[0], \
           sort_out_2lists(list_csv_brand_str, brands_in_trades)[1], \
           sort_out_2lists(list_csv_brand_str, brands_in_trades)[
               2]


# ----------ここまで日々の取引データ取得に関するもの----------

# ----------ここから東証一部上場企業の銘柄データ取得に関するもの----------
def get_tse_brands():
    print('start get tse brands!')
    # 東証から銘柄データを取得し、before_brand.csvとして全体を格納。この際、登録されていない銘柄は一括登録する。
    # 毎月１回やればいいのかなぁと思うけど、そんなに大したことはしてないので、毎日日付変わった時点に実行すればヨシ
    url = "https://www.jpx.co.jp/markets/statistics-equities/misc/tvdivq0000001vg2-att/data_j.xls"
    new_brand = pd.read_excel(url)
    old_brand = pd.read_csv(os.path.join(BASE_DIR, "data", "before_brand.csv"))

    added_brand = new_brand[~new_brand["コード"].isin(old_brand["コード"])]

    added_brand_records = added_brand.to_dict(orient="records")
    brand_model_inserts = []
    for d in added_brand_records:
        _brands = Brand.objects.filter(code=d["コード"])
        if _brands.count() == 0:
            brand_model_inserts.append(Brand(
                nation="jp",
                market="東証１部",
                brand_name=d["銘柄名"],
                code=d["コード"],
                division=d["市場・商品区分"],
                industry_code_1=d['33業種コード'],
                industry_division_1=d['33業種区分'],
                industry_code_2=d['17業種コード'],
                industry_division_2=d['17業種区分'],
                scale_code=d['規模コード'],
                scale_division=d['規模区分']
            ))
    print(added_brand_records)
    if added_brand_records:
        Brand.objects.bulk_create(brand_model_inserts)
        new_brand.to_csv(os.path.join(BASE_DIR, "data", "before_brand.csv"), index=True, header=True)
        print('新規登録あり')
    else:
        print(Brand.objects.all().count())
        print('新規登録なし')


# ----------ここまで東証一部上場企業の銘柄データ取得に関するもの----------
# ----------ここから円相場取得に関するもの----------
def get_yd():
    start = dt.date(2018, 3, 14)
    end = dt.date(2023, 3, 13)
    # YenRate.objects.all().delete()
    df_yd = data.DataReader('DEXJPUS', 'fred', start, end)
    df_yd = df_yd.reset_index()
    df_yd['DEXJPUS'] = df_yd['DEXJPUS'].interpolate().round(2)
    print(df_yd)
    df_record = df_yd.to_dict(orient='records')
    rate_model_insert = []
    for d in df_record:
        rate_model_insert.append(YenRate(
            Date=d['DATE'],
            rate=d['DEXJPUS']
        ))
    print(rate_model_insert)
    # YenRate.objects.bulk_create(rate_model_insert)
    print('DONE')


class Command(BaseCommand):
    help = "register TSE brands"

    def add_arguments(self, parser):
        parser.add_argument("first", type=str)

    def handle(self, *args, **options):
        if options["first"] == "aaa":
            reg_brands_from_csv()
        elif options["first"] == "bbb":
            reg_trades_from_csv()
        elif options["first"] == "ccc":
            get_initial_trades_from_csv()
