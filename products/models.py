from django.db import models


class Product(models.Model):
    title = models.CharField(max_length=200)
    type = models.CharField(max_length=100, default='General')
    region = models.CharField(max_length=100)
    description = models.TextField()
    quantity = models.DecimalField(max_digits=7, decimal_places=2)
    price = models.DecimalField(max_digits=7, decimal_places=2)
    photo = models.ImageField(upload_to='products/')

    def __str__(self):
        return self.title
