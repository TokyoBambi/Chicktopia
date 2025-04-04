from django import forms
from .models import Order, OrderItem, Payment, Sale
from products.models import Product
from accounts.models import Customer


class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['user', 'status', 'shipping_address',
                  'phone_number', 'notes']
        widgets = {
            'shipping_address': forms.Textarea(attrs={'rows': 3}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }


class OrderItemForm(forms.ModelForm):
    class Meta:
        model = OrderItem
        fields = ['product', 'quantity']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # You might want to filter products based on some criteria
        self.fields['product'].queryset = Product.objects.all()


class OrderItemFormSet(forms.BaseInlineFormSet):
    def clean(self):
        super().clean()
        # Validate that at least one item is added to the order
        if any(self.errors):
            return
        if not any(cleaned_data and not cleaned_data.get('DELETE', False)
                   for cleaned_data in self.cleaned_data):
            raise forms.ValidationError('At least one order item is required.')


class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['payment_method', 'amount_paid', 'transaction_id', 'status']


class SaleForm(forms.ModelForm):
    class Meta:
        model = Sale
        fields = ['order', 'customer', 'products',
                  'sale_date', 'total_amount', 'profit']
        widgets = {
            'sale_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter available orders, customers, and products as needed
        self.fields['order'].queryset = Order.objects.filter(
            status='delivered')
        self.fields['customer'].queryset = Customer.objects.all()
        self.fields['products'].queryset = Product.objects.all()
