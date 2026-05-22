from django.contrib import admin
from django.urls import path, include

urlpatterns = [

    path('admin/', admin.site.urls),

    path('api/', include('login_app.urls')),
    path('api/', include('chart_of_accounts.urls')),
    path('api/', include('journal.urls')),
    path('api/', include('ledgers.urls')),
    path('api/', include('Dr_Cr.urls')),
    path('api/', include('trial_balance.urls')),
    path('api/', include('profit_loss.urls')),

]
