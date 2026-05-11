from django.contrib import admin

# Register your models here.
from .models import Salon, SalonImage, SalonService
admin.site.register(Salon)
admin.site.register(SalonImage)
admin.site.register(SalonService)