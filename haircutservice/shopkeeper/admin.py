from django.contrib import admin
from .models import Salon, SalonService, SalonImage, QueueEntry, SiderImage
from django.utils.html import format_html

# Custom Admin for SiderImage to show a preview
@admin.register(SiderImage)
class SiderImageAdmin(admin.ModelAdmin):
    list_display = ('image_preview', 'image')

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="max-height: 80px; max-width: 160px;" />', obj.image.url)
        return "(No Image)"
    image_preview.short_description = 'Image Preview'

admin.site.register(Salon)
admin.site.register(SalonService)
admin.site.register(SalonImage)
admin.site.register(QueueEntry)
# The line below is now replaced by the @admin.register decorator above
# admin.site.register(SiderImage)