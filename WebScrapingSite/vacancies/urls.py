from django.urls import path
from .views import *

app_name = "vacancies"

urlpatterns = [path("", main_window, name="freelance_list")]
