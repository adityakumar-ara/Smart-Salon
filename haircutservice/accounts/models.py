from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.
class CustomUser(AbstractUser):
    is_customer = models.BooleanField(default=False)
    is_shopkeeper = models.BooleanField(default=False)
   
    name = models.CharField(max_length=20)
    mobile = models.CharField(max_length=10)
    image = models.ImageField(upload_to='CustomUser', blank=True, null=True)


    