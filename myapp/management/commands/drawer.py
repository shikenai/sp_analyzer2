import io
from django.core.management.base import BaseCommand
import matplotlib
import matplotlib.pyplot as plt
from django.http import HttpResponse
from myapp.models import Trades
import pandas as pd
# import mplfinance as mf
from django_pandas.io import read_frame

# バックエンドを指定
matplotlib.use('Agg')


# SVG化
def plt2svg():
    buf = io.BytesIO()
    plt.savefig(buf, format='svg', bbox_inches='tight')
    s = buf.getvalue()
    buf.close()
    return s


# 実行するビュー関数
def get_svg2http_response(days, brand_code):
    _trades = Trades.objects.filter(brand_code=brand_code).order_by("Date")
    n = _trades.count()
    print(n)
    x = days
    if n < x:
        n_minus = 0
    else:
        n_minus = n - x
    df = read_frame(_trades.all()[n_minus:n])

    df["Date"] = pd.to_datetime(df["Date"])
    df = df.set_index("Date")
    df = df.reindex(columns=['Open', 'High', 'Low', 'Close', 'Volume'])

    # mf.plot(df,
    #         type="candle",
    #         mav=[5, 12],
    #         volume=True)
    svg = plt2svg()  # SVG化
    plt.cla()  # グラフをリセット
    plt.close()
    response = HttpResponse(svg, content_type='image/svg+xml')
    res_str = response.content.decode('utf-8')
    return res_str


# BaseCommandを継承して作成
class Command(BaseCommand):
    help = "register TSE brands"

    def add_arguments(self, parser):
        parser.add_argument("first", type=str)

    def handle(self, *args, **options):
        get_svg2http_response()