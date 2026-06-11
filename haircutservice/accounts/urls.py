from django.urls import path, include
from .import views 
urlpatterns = [
    path('signup/',views.SignUp, name='signup'),
    path('login/',views.login, name='login'),
    path('profile/',views.profile, name='profile'),
    path('logout/',views.logout_user, name='logout'),
    path('editprofile/<int:id>/',views.editprofile, name='editprofile'),
]
