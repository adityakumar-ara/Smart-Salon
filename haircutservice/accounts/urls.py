from django.urls import path, include
from .import views 
urlpatterns = [
    path('signup/',views.SignUp, name='signup'),
    path('login/',views.login, name='login'),
    path('profile/',views.profile, name='profile'),
]
