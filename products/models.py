from django.db import models


class Product(models.Model):
    PRODUCT_TYPE_CHOICES = [
        ('broiler', 'Broiler'),
        ('layer', 'Layers'),
        ('kienyeji', 'Kienyeji'),
        ('feeds', 'Feeds'),
    ]

    title = models.CharField(max_length=200)
    product_type = models.CharField(
        max_length=100, choices=PRODUCT_TYPE_CHOICES, null=True, blank=True)
    region = models.CharField(max_length=100)
    description = models.TextField()
    quantity = models.DecimalField(max_digits=7, decimal_places=2)
    price = models.DecimalField(max_digits=7, decimal_places=2)
    photo = models.ImageField(upload_to='products/')

    def __str__(self):
        return self.title
