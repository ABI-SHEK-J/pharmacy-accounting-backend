from django.urls import path

from .views import trial_balance


urlpatterns = [
    path('trial_balance', trial_balance, name='trial_balance'),
    path('trial_balance/', trial_balance, name='trial_balance_slash'),
]
