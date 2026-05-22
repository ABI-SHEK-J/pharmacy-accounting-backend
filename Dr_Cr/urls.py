from django.urls import path

from .views import debtors_creditors


urlpatterns = [
    path('debtors_creditors', debtors_creditors, name='debtors_creditors'),
    path('debtors_creditors/', debtors_creditors, name='debtors_creditors_slash'),
]
