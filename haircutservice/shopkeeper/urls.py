from django.urls import path, include
from .import views 
urlpatterns = [
    path('opensalon', views.opensalon, name='opensalon')
]
