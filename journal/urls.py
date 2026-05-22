from django.urls import path

from .views import create_journal, journals


urlpatterns = [
    path('journal', journals, name='journals_no_slash'),
    path('journal/', journals, name='journals'),
    path('journals', journals, name='journal_list_no_slash'),
    path('journals/', journals, name='journal_list'),
    path('journals/create', create_journal, name='create_journal'),
    path('journals/create/', create_journal, name='create_journal_slash'),
]
