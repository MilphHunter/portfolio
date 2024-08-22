from django.urls import path

from .views import *

app_name = 'portfolio'

urlpatterns = [
    path('', index, name='index'),
    path('send-email/', send_email, name='send_email'),
]
