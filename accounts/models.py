from django.db import models
from django.contrib.auth.models import User

class Customer(models.Model):
    user = models.OneToOneField(
        User, null=True, blank=True, on_delete=models.CASCADE)
    name = models.CharField(max_length=100, null=True)
    phone = models.CharField(max_length=15, null=True)
    profile_pic = models.ImageField(
        upload_to="images/", null=True, blank=True)
    date_created = models.DateTimeField(auto_now_add=True)
    

    def __str__(self):
        return self.name