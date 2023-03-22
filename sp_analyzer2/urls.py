from django.contrib import admin
from django.urls import path
from myapp import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home),
    path('api/get_trade_data.json', views.get_trade_data),
    path('api/get_brand_list.json', views.get_brand_list),
    path('api/analyze', views.analyze),
    path('api/get_trades_from_stooq', views.get_trades_from_stooq),
    path('api/get_brands_from_tse', views.get_brands_from_tse),
    path('api/check_stooq', views.check_stooq),
    path('api/check_stooq_df', views.check_stooq_df),
    path('api/get_initial_brands_from_tse', views.get_initial_brands_from_tse),
    path('api/get_initial_trades_from_csv', views.get_initial_trades_from_csv),
    path('api/getYD.json', views.getYD),
]