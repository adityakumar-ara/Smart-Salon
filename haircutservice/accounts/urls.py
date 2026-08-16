from django.urls import path

from . import views

urlpatterns = [
    path('signup/', views.SignUp, name='signup'),
    path('verify-otp/', views.verify_otp, name='verify_otp'),
    path('login/', views.login, name='login'),
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('verify-password-reset-otp/', views.verify_password_reset_otp, name='verify_password_reset_otp'),
    path('reset-password/', views.reset_password_confirm, name='reset_password_confirm'),
    path('profile/', views.profile, name='profile'),
    path('logout/', views.logout_user, name='logout'),
    path('editprofile/<int:id>/', views.editprofile, name='editprofile'),
]
