from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid


from products.models import Product
from accounts.models import Customer


class Order(models.Model):
    """Model for tracking customer orders"""
    ORDER_STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('paid', 'Paid'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True)
    date_ordered = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=20, choices=ORDER_STATUS_CHOICES, default='pending')
    total_amount = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.00)
    shipping_address = models.TextField(null=True, blank=True)
    phone_number = models.CharField(max_length=15, null=True, blank=True)
    notes = models.TextField(null=True, blank=True)

    class Meta:
        ordering = ['-date_ordered']

    def __str__(self):
        return f"Order {self.id}"

    @property
    def get_order_total(self):
        """Calculate order total from all items"""
        order_items = self.orderitem_set.all()
        return sum([item.get_total for item in order_items])

    @property
    def get_items_count(self):
        """Get the total count of items in the order"""
        order_items = self.orderitem_set.all()
        return sum([item.quantity for item in order_items])


class OrderItem(models.Model):
    """Model for tracking individual items within an order"""
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)

    def __str__(self):
        return f"{self.quantity} x {str(self.product)}"

    @property
    def get_total(self):
        """Calculate total price for this item"""
        return self.product.price * self.quantity


class Payment(models.Model):
    """Model for tracking payment information for completed orders"""
    PAYMENT_METHOD_CHOICES = (
        ('mpesa', 'M-Pesa'),
        ('card', 'Credit/Debit Card'),
        ('cash', 'Cash on Delivery'),
        ('bank', 'Bank Transfer'),
    )

    PAYMENT_STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.OneToOneField(Order, on_delete=models.CASCADE)
    payment_method = models.CharField(
        max_length=20, choices=PAYMENT_METHOD_CHOICES)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_id = models.CharField(
        max_length=100, null=True, blank=True)  # For external payment IDs
    payment_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')

    def __str__(self):
        return f"Payment {self.id} for {self.order}"


class Sale(models.Model):
    """Model for tracking completed sales (useful for reporting)"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.OneToOneField(Order, on_delete=models.CASCADE)
    customer = models.OneToOneField(Customer, on_delete=models.CASCADE)
    products = models.ManyToManyField(Product)
    sale_date = models.DateTimeField(default=timezone.now)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    profit = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return f"Sale {self.id}"

    class Meta:
        ordering = ['-sale_date']
