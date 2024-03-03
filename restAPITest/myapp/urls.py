from django.urls import path
from myapp.views import myfunc

app_name = 'app'

urlpatterns = [
    path("", myfunc, name='myfunc'),
]