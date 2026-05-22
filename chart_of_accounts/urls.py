from django.urls import path

from .views import chart_of_accounts, create_chart_of_account


urlpatterns = [
    path('chart_of_accounts', chart_of_accounts, name='chart_of_accounts'),
    path('chart_of_accounts/create', create_chart_of_account, name='create_chart_of_account'),
]
