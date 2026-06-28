from django.contrib import admin

# Register your models here.
from .models import *
admin.site.register(Salon)
admin.site.register(SalonImage)
admin.site.register(SalonService)
admin.site.register(QueueEntry)
