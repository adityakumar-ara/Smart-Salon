from django.urls import path, include
from .import views 
urlpatterns = [
    path('opensalon/', views.opensalon, name='opensalon'),
    path('salondetail/', views.salon_views, name='salon_detail'),
    path('updatesalon/',views.edit_salon, name='edit_salon'),
]
