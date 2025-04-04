from django import forms
from .models import Product


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['title', 'type', 'region',
                  'description', 'quantity', 'price', 'photo']
        exclude = []

    title = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Product Title'
        })
    )

    type = forms.ChoiceField(
        required=True,
        choices=[
            ('broiler', 'Broiler'),
            ('layer', 'Layers'),
            ('kienyeji', 'Kienyeji'),
            ('feeds', 'Feeds')
        ],
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )

    region = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Region'
        })
    )

    description = forms.CharField(
        required=True,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Description',
            'rows': 4
        })
    )

    quantity = forms.IntegerField(
        required=True,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Quantity'
        })
    )

    price = forms.DecimalField(
        required=True,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Price'
        })
    )

    photo = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': 'image/*'
        })
    )

    def clean_price(self):
        price = self.cleaned_data.get('price')
        if price <= 0:
            raise forms.ValidationError("Price must be greater than zero.")
        return price

    def clean_quantity(self):
        quantity = self.cleaned_data.get('quantity')
        if quantity <= 0:
            raise forms.ValidationError("Quantity must be greater than zero.")
        return quantity

    def save(self, commit=True):
        product = super().save(commit=False)

        if commit:
            product.save()

        return product
