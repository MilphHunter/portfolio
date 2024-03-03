from django.urls import path
from . import views

app_name = 'app'

urlpatterns = [
    path('cars/', views.CarListViews.as_view(), name='car_list'),
    path('cars/<int:id>', views.CarDetailView.as_view(), name='car_detail'),
    path('cars/<str:name>/<int:color>/<int:max_speed>/enroll/', views.CarEnrollView.as_view(), name='car_enroll'),
]
