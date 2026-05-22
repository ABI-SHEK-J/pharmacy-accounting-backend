from django.urls import path

from .views import profit_loss


urlpatterns = [
    path('profit_loss', profit_loss, name='profit_loss'),
    path('profit_loss/', profit_loss, name='profit_loss_slash'),
]
