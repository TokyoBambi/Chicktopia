from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

from .forms import ProductForm


@login_required
def upload_product(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)  # Handle file uploads
        if form.is_valid():
            form.save()  # Save the product to the database
            # Redirect to a success page or dashboard
            return redirect('dashboard')
    else:
        form = ProductForm()  # Create an empty form for GET requests

    return render(request, 'products/upload_product.html', {'form': form})


def broiler_view(request):
    # Example of getting cart item count
    cart_item_count = request.session.get('cart_item_count', 0)
    return render(request, 'products/broiler.html', {'cart_item_count': cart_item_count})


def layers_view(request):
    cart_item_count = request.session.get('cart_item_count', 0)
    return render(request, 'products/layers.html', {'cart_item_count': cart_item_count})


def kienyeji_view(request):
    cart_item_count = request.session.get('cart_item_count', 0)
    return render(request, 'products/kienyeji.html', {'cart_item_count': cart_item_count})


def feeds_view(request):
    cart_item_count = request.session.get('cart_item_count', 0)
    return render(request, 'products/feeds.html', {'cart_item_count': cart_item_count})


def services_view(request):
    return render(request, 'products/services.html')


def aboutus_view(request):
    return render(request, 'about us.html')
