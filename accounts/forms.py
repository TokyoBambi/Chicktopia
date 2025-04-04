from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django import forms

from .models import Customer


class CreateUserForm(UserCreationForm):
    class Meta:
        model = User
        fields = [
            "first_name",
            "last_name",
            "username",
            "email",
            "password1",
            "password2",
        ]


class UpdateCustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['location', 'phone', 'profile_pic']
        exclude = ['user', 'date_created', 'is_complete']

    location = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your location'
        })
    )

    phone = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your phone number'
        })
    )

    profile_pic = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': 'image/*'
        })
    )

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if phone:
            # Remove any non-digit characters
            phone = ''.join(c for c in phone if c.isdigit())

            # Basic validation for phone number length
            if len(phone) < 9 or len(phone) > 15:
                raise forms.ValidationError(
                    "Please enter a valid phone number.")

        return phone

    def save(self, commit=True):
        customer = super().save(commit=False)

        # If profile updated successfully, mark as complete
        if customer.location and customer.phone:
            customer.is_complete = True

        if commit:
            customer.save()

        return customer
