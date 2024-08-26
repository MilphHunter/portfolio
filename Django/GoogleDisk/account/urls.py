from django.contrib.auth import views as auth_views
from django.urls import path, reverse_lazy

from .views import *

app_name = 'account'

urlpatterns = [
    path('', auth_views.LoginView.as_view(next_page=reverse_lazy('workspace:index')), name='login'),
    path('sign-up/', user_sign_up, name='register'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
]
