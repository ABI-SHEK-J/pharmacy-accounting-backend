from django.urls import path

from .views import ledgers, period_statement


urlpatterns = [
    path('ledgers', ledgers, name='ledgers'),
    path('ledgers/', ledgers, name='ledgers_slash'),
    path('period_statement', period_statement, name='period_statement'),
    path('period_statement/', period_statement, name='period_statement_slash'),
]
