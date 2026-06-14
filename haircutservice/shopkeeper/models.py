from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Salon(models.Model):

    owner = models.ForeignKey(User,on_delete=models.CASCADE)

    owner_name = models.CharField(max_length=100)

    salon_name = models.CharField(max_length=100)

    address = models.TextField()
    salon_image = models.ImageField(upload_to='salon_image/')
    open_time = models.TimeField()

    close_time = models.TimeField()

    description = models.TextField()
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):

        return self.salon_name
    
class SalonService(models.Model):
    salon = models.ForeignKey(Salon, on_delete=models.CASCADE, related_name="services")

    name = models.CharField(max_length=100)  
    image = models.ImageField(upload_to='service_images/')
    price = models.IntegerField()
    male = models.BooleanField(default=False)
    female = models.BooleanField(default=False)

    def __str__(self):
        return self.name    
    
class SalonImage(models.Model):

    salon = models.ForeignKey(Salon,on_delete=models.CASCADE,related_name='images')

    image = models.ImageField(upload_to='salon_gallery/')
    description = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return self.salon.salon_name    
    

class Service(models.Model):
    salon = models.ForeignKey(Salon, on_delete=models.CASCADE)    
    service_name = models.CharField(max_length=200, null=True , blank=True)
    service_price = models.DecimalField(max_digits=5, decimal_places=2)
    about_service = models.TextField(null=True, blank=True)
    service_image = models.ImageField(upload_to='service/', null=True, blank=True)
    def __str__(self):
        return self.Service_name()