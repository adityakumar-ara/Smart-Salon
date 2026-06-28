from django.db import models
from django.contrib.auth import get_user_model
from urllib.parse import quote_plus

User = get_user_model()

class Salon(models.Model):

    owner = models.ForeignKey(User,on_delete=models.CASCADE)

    owner_name = models.CharField(max_length=100)

    salon_name = models.CharField(max_length=100)

    salon_image = models.ImageField(upload_to='salon_image/')
    latitude = models.FloatField(blank=True, null=True)  
    longitude = models.FloatField(blank=True, null=True)
    open_time = models.TimeField()

    close_time = models.TimeField()

    description = models.TextField( null=True, blank= True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def location_text(self):
        if self.latitude is not None and self.longitude is not None:
            return f"{self.latitude:.6f}, {self.longitude:.6f}"
        return "Location not set"

    @property
    def location_map_url(self):
        if self.latitude is not None and self.longitude is not None:
            label = quote_plus(self.salon_name or 'Salon')
            return f"https://www.google.com/maps/search/?api=1&query={label}%20@{self.latitude},{self.longitude}"
        return ""

    def __str__(self):

        return self.salon_name

    @property
    def waiting_queue_count(self):
        return self.queue_entries.filter(status='waiting').count()
    
class SalonService(models.Model):
    salon = models.ForeignKey(Salon, on_delete=models.CASCADE, related_name="services")

    GENDER_CHOICES = [
        ('male', 'Male Only'),
        ('female', 'Female Only'),
        ('unisex', 'Unisex (Both)'),
    ]
    name = models.CharField(max_length=100)  
    image = models.ImageField(upload_to='service_images/')
    price = models.IntegerField()
    target_gender = models.CharField(
        max_length=10, 
        choices=GENDER_CHOICES, 
        default='unisex'
    )

    def __str__(self):
        return self.name    

class QueueEntry(models.Model):
    STATUS_CHOICES = [
        ('waiting', 'Waiting'),
        ('seated', 'Seated'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    salon = models.ForeignKey(Salon, on_delete=models.CASCADE, related_name='queue_entries')
    service = models.ForeignKey('SalonService', on_delete=models.SET_NULL, null=True, blank=True, related_name='queue_entries')
    customer = models.ForeignKey(User, on_delete=models.CASCADE)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='waiting')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']

    @property
    def position(self):
        if self.status != 'waiting':
            return None
        return self.salon.queue_entries.filter(status='waiting', created_at__lt=self.created_at).count() + 1

    def __str__(self):
        service_name = self.service.name if self.service else 'No Service'
        return f"{self.customer.username} for {service_name} in {self.salon.salon_name} [{self.status}]"

class SalonImage(models.Model):

    salon = models.ForeignKey(Salon,on_delete=models.CASCADE,related_name='images')

    image = models.ImageField(upload_to='salon_gallery/')
    description = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return self.salon.salon_name    
    