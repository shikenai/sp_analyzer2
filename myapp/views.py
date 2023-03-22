import pandas
from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from myapp.management.commands import stocks, drawer, analyzer
from myapp.models import Trades, Brand
from sp_analyzer2.settings import BASE_DIR
from django_pandas.io import read_frame
import pandas as pd
import pandas_datareader.data as data
import datetime as dt
import os
import json


def analyze(request):
    # count_trades()
    content = analyzer.analyze("7203.jp", 100)
    return render(request, "test.html", context={
        "content": content.to_html()
    })


def count_trades():
    print('count trades')
    start_date = dt.date(2022, 3, 13)
    _targets = list(pd.read_csv(BASE_DIR / "data/nikkei_listed_20230313_.csv")["0"])
    targets = [str(t) + '.jp' for t in _targets]
    print(analyzer.analyze('7203.jp', 10000))
    # cnt_list = []
    # print(targets)
    # for i in range(len(targets)):
    #     # print(_trades[i])
    #     cnt_list.append(
    #         dict(brand=targets[i], cnt=Trades.objects.filter(brand_code=targets[i], Date__gte=start_date).count()))
    #     print(cnt_list)
    # print(cnt_list)


def getYD(request):
    stocks.get_yd()
    return JsonResponse({"user": "taro"})


def get_trade_data(request):
    print('get trade data')
    req = json.loads(request.body)
    plt = drawer.get_svg2http_response(int(req["days"]), req["brand_code"])
    return HttpResponse(plt)


def get_brand_list(request):
    _brand = Brand.objects.all()
    json_brand = list(_brand.values())
    return JsonResponse(json_brand, safe=False)


def home(request):
    # return HttpResponse('asdasd')
    return redirect("http://localhost:5173/")


def get_trades_from_stooq(request):
    stocks.get_trades_from_stooq()
    return JsonResponse({"user": "taro"})


def get_brands_from_tse(request):
    stocks.get_tse_brands()
    return JsonResponse({"user": "taro"})


def check_stooq(request):
    print('check_stooq')
    t1 = pd.Timestamp(2023, 3, 1)
    t2 = pd.Timestamp(2023, 3, 2)
    df = pd.DataFrame(data=[t1, t2], columns=['Date'])
    df["Date2"] = df["Date"].astype(dtype="datetime")
    print(df)
    # print(data.DataReader("7203.jp", "stooq", dt.date(2023, 1, 1), dt.date(2023, 3, 3)))
    return JsonResponse({"user": "taro"})


def get_initial_brands_from_tse(request):
    stocks.get_initial_brands_from_tse()
    return JsonResponse({"user": "taro"})


def get_initial_trades_from_csv(request):
    print('get!')
    stocks.get_initial_trades_from_csv()
    return JsonResponse({"user": "taro"})


def check_stooq_df(request):
    print('check_stooq_df')
    t1 = dt.date(2023, 1, 21)
    t2 = dt.date.today()
    df1 = data.DataReader("7203.jp", "stooq", t1, t2)
    df2 = data.DataReader("1808.jp", "stooq", t1, t2)
    print('--------df1')
    print(df1)
    print(df1.dtypes)
    df1 = df1.reset_index()
    print(df1)
    print(df1.dtypes)
    print('--------df2')
    print(df2)
    print(df2.dtypes)
    df2 = df2.reset_index()
    print(df2)
    print(df2.dtypes)

    return JsonResponse({"user": "taro"})
