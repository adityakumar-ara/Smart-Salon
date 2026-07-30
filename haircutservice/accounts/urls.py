from django.urls import path

from . import views

urlpatterns = [
    path('signup/', views.SignUp, name='signup'),
    path('verify-otp/', views.verify_otp, name='verify_otp'),
    path('login/', views.login, name='login'),
    path('profile/', views.profile, name='profile'),
    path('logout/', views.logout_user, name='logout'),
    path('editprofile/<int:id>/', views.editprofile, name='editprofile'),
]
