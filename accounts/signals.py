from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.dispatch import receiver
from .models import Customer

@receiver(post_save, sender=User)
def create_customer(sender, instance, created, **kwargs):
    """
    Signal handler to create a Customer instance when a User is created
    """
    if created:
        Customer.objects.create(user=instance)
        print(f"Customer created for user: {instance.username}")
