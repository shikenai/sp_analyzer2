from django.contrib import admin
from myapp.models import Trades, Brand, YenRate

# Register your models here.


admin.site.register(Brand)
admin.site.register(Trades)
admin.site.register(YenRate)
