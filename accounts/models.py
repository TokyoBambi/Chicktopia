from django.db import models
from django.contrib.auth.models import User


class Customer(models.Model):
    user = models.OneToOneField(
        User, null=True, blank=True, on_delete=models.CASCADE, related_name='consumer')
    location = models.CharField(max_length=100, null=True)
    phone = models.CharField(max_length=15, null=True)
    profile_pic = models.ImageField(
        upload_to="images/", null=True, blank=True)
    date_created = models.DateTimeField(auto_now_add=True)
    is_complete = models.BooleanField(default=False)

    def __str__(self):
        return str(self.user)
