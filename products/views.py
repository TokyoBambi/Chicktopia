from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required

from .models import Product
from .forms import ProductForm


@login_required
def upload_product(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('dashboard')
    else:
        form = ProductForm()

    return render(request, 'products/upload_product.html', {'form': form})


def broiler_view(request):
    cart_item_count = request.session.get('cart_item_count', 0)
    broiler_products = Product.objects.filter(
        product_type='broiler')
    return render(request, 'products/broiler.html', {
        'cart_item_count': cart_item_count,
        'products': broiler_products
    })


def layers_view(request):
    cart_item_count = request.session.get('cart_item_count', 0)
    layers_products = Product.objects.filter(
        product_type='layer')
    return render(request, 'products/layers.html', {
        'cart_item_count': cart_item_count,
        'products': layers_products
    })


def kienyeji_view(request):
    cart_item_count = request.session.get('cart_item_count', 0)
    kienyeji_products = Product.objects.filter(
        product_type='kienyeji')
    return render(request, 'products/kienyeji.html', {
        'cart_item_count': cart_item_count,
        'products': kienyeji_products
    })


def feeds_view(request):
    cart_item_count = request.session.get('cart_item_count', 0)
    feeds_products = Product.objects.filter(
        product_type='feeds')
    return render(request, 'products/feeds.html', {
        'cart_item_count': cart_item_count,
        'products': feeds_products
    })


def product_list(request):
    products = Product.objects.all()  # Fetch all products
    return render(request, 'products/product_list.html', {'products': products})


def product_detail(request, product_id):
    # Fetch the product by ID
    product = get_object_or_404(Product, id=product_id)
    return render(request, 'products/product_detail.html', {'product': product})


def add_to_cart(request, product_id):
    # Fetch the product from the database
    product = get_object_or_404(Product, id=product_id)
    quantity = 1  # Default quantity
    cart_items = request.session.get('cart_items', [])

    # Check if the product is already in the cart
    for item in cart_items:
        if item['title'] == product.title:  # Check by title instead of product_id
            # Increment quantity if already in cart
            item['quantity'] += quantity
            break
    else:
        # If not found, add a new item with the required structure
        cart_items.append({
            'title': product.title,
            'price': str(product.price),  # Ensure price is a string
            'quantity': quantity,
            'imageUrl': product.photo.url if product.photo else '',  # Handle missing photo
        })

    request.session['cart_items'] = cart_items  # Update the session
    return redirect('product_detail', product_id=product_id)
