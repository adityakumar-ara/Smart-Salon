from django.urls import path, include
from .import views 
urlpatterns = [
    path('salon/<int:salon_id>/', views.salon_detail_public, name='salon_detail_public'),
    path('opensalon/', views.opensalon, name='opensalon'),
    path('salondetail/', views.salon_views, name='salon_detail'),
    path('updatesalon/',views.edit_salon, name='edit_salon'),
    path('add_service/',views.add_service, name='add_service'),
    path('services/', views.service_views, name="service_views"),
    path('edit_service/<int:service_id>/', views.edit_service, name='edit_service'),
    path('delete_service/<int:service_id>/', views.delete_service, name='delete_service'),
    path('maleservice/', views.male_section, name='male_section'),
    path('femaleservice/', views.female_section, name='female_section'),
    path('join_queue/<int:service_id>/', views.join_queue, name='join_queue'),
    path('leave_queue/<int:service_id>/', views.leave_queue, name='leave_queue'),
    path('accept_order/<int:entry_id>/', views.accept_order, name='accept_order'),
    path('cancel_order/<int:entry_id>/', views.cancel_order, name='cancel_order'),
    path('aboutservice/<int:service_id>/', views.about_service_page, name='about_service_page'),
]
