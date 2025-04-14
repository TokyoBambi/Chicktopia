import json
import uuid
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count
from django.contrib import messages
from django.utils import timezone
from django.db import transaction
from decimal import Decimal  # Import Decimal for precise decimal arithmetic

from .models import Order, OrderItem, Payment, Sale, Product
from products.models import Product
from accounts.models import Customer


def update_cart(request):
    """
    AJAX view to update the cart data in the session
    """
    try:
        data = json.loads(request.body)
        count = data.get('count', 0)
        cart_items = data.get('cart_items', [])
        total_price = data.get('total_price', 0)

        # Print debugging info
        print("Updating cart in session:")
        print(f"Count: {count}")
        print(f"Items: {cart_items}")
        print(f"Total: {total_price}")

        # Store all cart data in session
        # Also store as cart_item_count
        request.session['cart_item_count'] = count
        # Store as 'count' too for compatibility
        request.session['count'] = count
        request.session['cart_items'] = cart_items
        request.session['total_price'] = total_price
        request.session.modified = True
        request.session.save()

        return JsonResponse({'success': True})
    except Exception as e:
        print(f"Error in update_cart: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)})


def checkout_view(request):
    """
    Checkout view that displays all selected cart items
    """
    cart_items = request.session.get('cart_items', [])
    total_price = request.session.get('total_price', 0)
    cart_item_count = request.session.get('count', 0)

    if isinstance(cart_items, str):
        try:
            cart_items = json.loads(cart_items)
        except json.JSONDecodeError:
            cart_items = []

    for item in cart_items:
        try:
            price = float(item.get('price', 0))
            quantity = int(item.get('quantity', 1))

            item_total = price * quantity

            item['price'] = "{:.2f}".format(price)
            item['total'] = "{:.2f}".format(item_total)

            if 'imageUrl' not in item:
                item['imageUrl'] = '/static/img/placeholder.png'

            if 'title' not in item:
                item['title'] = "Unknown Item"

        except (ValueError, TypeError) as e:
            item['price'] = "0.00"
            item['total'] = "0.00"

    try:
        formatted_total_price = "{:.2f}".format(float(total_price))
    except (ValueError, TypeError):
        formatted_total_price = "0.00"

    print(f"Cart items received: {cart_items}")  # Check the cart items

    debug_info = {
        'has_items': bool(cart_items),
        'num_items': sum(cart_item['quantity'] for cart_item in cart_items),
        'session_keys': list(request.session.keys()),
        'cart_data': json.dumps(cart_items, indent=2)
    }

    context = {
        'cart_items': cart_items,
        'total_price': formatted_total_price,
        'cart_item_count': cart_item_count,
        'debug_info': debug_info
    }

    return render(request, 'retail/checkout.html', context)


@login_required
def order_list(request):
    """View to display all orders, with optional filtering"""
    status = request.GET.get('status')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')

    orders = Order.objects.all()

    if status:
        orders = orders.filter(status=status)
    if date_from:
        orders = orders.filter(date_ordered__gte=date_from)
    if date_to:
        orders = orders.filter(date_ordered__lte=date_to)

    context = {
        'orders': orders,
        'status_choices': Order.ORDER_STATUS_CHOICES,
    }

    return render(request, 'retail/order_list.html', context)


@login_required
def order_detail(request, order_id):
    """View to display details of a specific order"""
    order = get_object_or_404(Order, id=order_id)
    order_items = order.orderitem_set.all()

    try:
        payment = Payment.objects.get(order=order)
    except Payment.DoesNotExist:
        payment = None

    context = {
        'order': order,
        'order_items': order_items,
        'payment': payment,
    }

    return render(request, 'retail/order_detail.html', context)


@login_required
def create_order(request):
    """View to create a new order"""
    if request.method == 'POST':
        user_id = request.POST.get('user')
        status = request.POST.get('status', 'pending')
        shipping_address = request.POST.get('shipping_address')
        phone_number = request.POST.get('phone_number')
        notes = request.POST.get('notes')

        order = Order(
            id=uuid.uuid4(),
            status=status,
            shipping_address=shipping_address,
            phone_number=phone_number,
            notes=notes
        )

        if user_id:
            from django.contrib.auth.models import User
            try:
                user = User.objects.get(id=user_id)
                order.user = user
            except User.DoesNotExist:
                pass
        elif request.user.is_authenticated:
            order.user = request.user

        order.save()

        product_ids = request.POST.getlist('product')
        quantities = request.POST.getlist('quantity')

        if len(product_ids) == len(quantities):
            for i in range(len(product_ids)):
                try:
                    product = Product.objects.get(id=product_ids[i])
                    quantity = int(quantities[i])
                    if quantity > 0:
                        OrderItem.objects.create(
                            order=order,
                            product=product,
                            quantity=quantity
                        )
                except (Product.DoesNotExist, ValueError):
                    continue

        order.total_amount = order.get_order_total
        order.save()

        messages.success(request, f'Order {order.id} created successfully!')
        return redirect('order_detail', order_id=order.id)

    products = Product.objects.all()

    context = {
        'products': products,
        'status_choices': Order.ORDER_STATUS_CHOICES,
    }

    return render(request, 'retail/create_order.html', context)


@login_required
def update_order(request, order_id):
    """Update an existing order based on the current cart items."""
    order = get_object_or_404(Order, id=order_id, user=request.user)

    if request.method == "POST":
        cart_items = request.session.get('cart_items', [])
        total_price = 0

        with transaction.atomic():
            # Clear existing order items
            order.orderitem_set.all().delete()

            for item in cart_items:
                product = get_object_or_404(Product, title=item['title'])
                quantity = item['quantity']

                if product.quantity >= quantity:
                    product.quantity -= quantity
                    product.save()

                    # Create new order items
                    order_item = OrderItem(
                        order=order, product=product, quantity=quantity)
                    order_item.save()

                    total_price += float(item['price']) * quantity
                else:
                    return render(request, 'error.html', {'message': 'Not enough stock for ' + product.title})

            # Update order total
            order.total_amount = total_price
            order.save()

            # Update payment and sales records as needed
            # (Similar logic as in create_order_from_cart)

        return redirect('order_success')

    return render(request, 'retail/update_order.html', {'order': order})


@login_required
def delete_order(request, order_id):
    """View to delete an order"""
    order = get_object_or_404(Order, id=order_id)

    if request.method == 'POST':

        if order.status == 'pending':
            order.delete()
            messages.success(request, 'Order deleted successfully!')
            return redirect('order_list')
        else:
            messages.error(request, 'Only pending orders can be deleted!')

    context = {
        'order': order,
    }

    return render(request, 'retail/delete_order.html', context)


@login_required
def create_order_from_cart(request):
    """Create an order from cart items in session"""

    if request.method == "POST":
        cart_items = request.session.get('cart_items', [])
        total_price = Decimal(0)  # Initialize total_price as a Decimal
        print(f"Cart items received: {cart_items}")  # Debugging line

        if not cart_items:
            return render(request, 'error.html', {'message': 'Your cart is empty.'})

        with transaction.atomic():  # Ensure atomicity
            # Create the order first
            order = Order.objects.create(
                user=request.user,  # Associate the order with the logged-in user
                total_amount=Decimal(0.00),  # Initialize total amount
            )

            for item in cart_items:
                # Check if 'title' and 'quantity' are in the item
                if 'title' not in item or 'quantity' not in item:
                    return render(request, 'error.html', {'message': 'Product title or quantity is missing in cart items.'})

                # Fetch the product by title
                product = get_object_or_404(
                    Product, title=item['title'])  # Fetch product by title
                quantity = item['quantity']

                # Check if enough quantity is available
                if product.quantity >= quantity:
                    product.quantity -= quantity  # Reduce the product quantity
                    product.save()  # Save the updated product

                    # Create an order item entry
                    order_item = OrderItem(
                        order=order,  # Link the order item to the order
                        product=product,
                        quantity=quantity,
                    )
                    order_item.save()  # Save the order item instance

                    # Update total price for the order
                    # Convert price to Decimal
                    total_price += Decimal(item['price']) * quantity
                else:
                    return render(request, 'error.html', {'message': f'Not enough stock for {product.title}.'})

            # Update the total amount in the order
            order.total_amount = total_price
            order.save()  # Save the order instance

            # Create a payment for the order
            payment = Payment.objects.create(
                order=order,
                payment_method='credit_card',  # Example payment method, adjust as needed
                amount_paid=total_price,
                status='completed',  # Assuming the payment is successful
            )

            # Check if a sale already exists for the customer
            sale, created = Sale.objects.get_or_create(
                customer=request.user.consumer,  # Assuming you have a Customer model linked to User
                # Set defaults if creating a new sale
                defaults={'order': order, 'total_amount': total_price}
            )

            if not created:
                # If the sale already exists, update the total amount and add new products
                sale.total_amount += total_price  # Update total amount
                sale.save()  # Save the updated sale

            # Add products to the sale
            for item in order.orderitem_set.all():
                sale.products.add(item.product)  # Add each product to the sale

            # Clear the cart after successful order placement
            request.session['cart_items'] = []  # Clear the cart
            request.session['cart_item_count'] = 0  # Reset cart item count

        # Redirect to a success page or order summary
        return redirect('order_success')  # Replace with your success URL

    # Render checkout page if not POST
    return render(request, 'retail/cart_to_order.html')


@login_required
def order_success(request):
    """Display order success page with order details"""
    # Assuming you want to show the latest order for the user
    order = Order.objects.filter(
        user=request.user).order_by('-date_ordered').first()

    if order is None:
        return render(request, 'error.html', {'message': 'No order found.'})

    # Get cart items from the session
    cart_items = request.session.get('cart_items', [])

    return render(request, 'retail/order_success.html', {'order': order, 'cart_items': cart_items})


@login_required
def payment_list(request):
    """View to display all payments"""

    status = request.GET.get('status')
    method = request.GET.get('method')

    payments = Payment.objects.all()

    if status:
        payments = payments.filter(status=status)
    if method:
        payments = payments.filter(payment_method=method)

    context = {
        'payments': payments,
        'payment_status_choices': Payment.PAYMENT_STATUS_CHOICES,
        'payment_method_choices': Payment.PAYMENT_METHOD_CHOICES,
    }

    return render(request, 'retail/payment_list.html', context)


@login_required
def payment_detail(request, payment_id):
    """View to display details of a specific payment"""
    payment = get_object_or_404(Payment, id=payment_id)

    context = {
        'payment': payment,
    }

    return render(request, 'retail/payment_detail.html', context)


@login_required
def create_payment(request, order_id):
    """Create a payment for the specified order."""
    order = get_object_or_404(Order, id=order_id, user=request.user)

    if request.method == "POST":
        # Check if a payment already exists for this order
        existing_payment = Payment.objects.filter(order=order).first()
        if existing_payment:
            return render(request, 'error.html', {'message': 'Payment already exists for this order.'})

        # Assuming you have a payment method and amount in the request
        payment_method = request.POST.get(
            'payment_method', 'credit_card')  # Default payment method
        amount_paid = order.total_amount  # Use the order's total amount

        # Create the payment
        payment = Payment.objects.create(
            order=order,
            payment_method=payment_method,
            amount_paid=amount_paid,
            status='completed',  # Assuming the payment is successful
        )

        # Redirect to a success page or order summary
        return redirect('payment_success')  # Replace with your success URL

    return render(request, 'retail/create_payment.html', {'order': order})


@login_required
def update_payment(request, payment_id):
    """View to update an existing payment"""
    payment = get_object_or_404(Payment, id=payment_id)
    order = payment.order

    if request.method == 'POST':

        payment.payment_method = request.POST.get(
            'payment_method', payment.payment_method)
        payment.amount_paid = request.POST.get(
            'amount_paid', payment.amount_paid)
        payment.transaction_id = request.POST.get(
            'transaction_id', payment.transaction_id)
        payment.status = request.POST.get('status', payment.status)
        payment.save()

        if payment.status == 'completed' and order.status == 'pending':
            order.status = 'paid'
            order.save()
        elif payment.status == 'refunded' and order.status == 'paid':
            order.status = 'cancelled'
            order.save()

        messages.success(request, 'Payment updated successfully!')
        return redirect('payment_detail', payment_id=payment.id)

    context = {
        'payment': payment,
        'order': order,
        'payment_method_choices': Payment.PAYMENT_METHOD_CHOICES,
        'payment_status_choices': Payment.PAYMENT_STATUS_CHOICES,
    }

    return render(request, 'retail/update_payment.html', context)


@login_required
def sale_list(request):
    """View to display all sales"""

    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')

    sales = Sale.objects.all()

    if date_from:
        sales = sales.filter(sale_date__gte=date_from)
    if date_to:
        sales = sales.filter(sale_date__lte=date_to)

    total_sales_amount = sales.aggregate(Sum('total_amount'))[
        'total_amount__sum'] or 0
    total_profit = sales.aggregate(Sum('profit'))['profit__sum'] or 0

    context = {
        'sales': sales,
        'total_sales_amount': total_sales_amount,
        'total_profit': total_profit,
    }

    return render(request, 'retail/sale_list.html', context)


@login_required
def sale_detail(request, sale_id):
    """View to display details of a specific sale"""
    sale = get_object_or_404(Sale, id=sale_id)

    context = {
        'sale': sale,
        'products': sale.products.all(),
    }

    return render(request, 'retail/sale_detail.html', context)


@login_required
def create_sale(request, order_id):
    """Create a sale for the specified order."""
    order = get_object_or_404(Order, id=order_id, user=request.user)

    if request.method == "POST":
        # Create the sale
        sale = Sale.objects.create(
            order=order,
            customer=request.user.consumer,  # Assuming you have a Customer model linked to User
            total_amount=order.total_amount,  # Total amount for the sale
        )

        # Add products to the sale
        for item in order.orderitem_set.all():
            sale.products.add(item.product)  # Add each product to the sale

        # Redirect to a success page or order summary
        return redirect('sale_success')  # Replace with your success URL

    return render(request, 'retail/create_sale.html', {'order': order})


@login_required
def update_sale(request, sale_id):
    """View to update an existing sale record"""
    sale = get_object_or_404(Sale, id=sale_id)

    if request.method == 'POST':

        customer_id = request.POST.get('customer')
        product_ids = request.POST.getlist('products')
        total_amount = request.POST.get('total_amount')
        profit = request.POST.get('profit')

        try:

            if customer_id:
                customer = Customer.objects.get(id=customer_id)
                sale.customer = customer

            sale.total_amount = total_amount
            sale.profit = profit
            sale.save()

            if product_ids:
                products = Product.objects.filter(id__in=product_ids)
                sale.products.set(products)

            messages.success(request, 'Sale updated successfully!')
            return redirect('sale_detail', sale_id=sale.id)

        except Customer.DoesNotExist:
            messages.error(request, 'Invalid customer selected!')

    customers = Customer.objects.all()
    products = Product.objects.all()

    context = {
        'sale': sale,
        'customers': customers,
        'products': products,
        'selected_products': sale.products.all(),
    }

    return render(request, 'retail/update_sale.html', context)


@login_required
def delete_sale(request, sale_id):
    """View to delete a sale record"""
    sale = get_object_or_404(Sale, id=sale_id)

    if request.method == 'POST':
        if request.user.is_staff:
            sale.delete()
            messages.success(request, 'Sale record deleted successfully!')
            return redirect('sale_list')
        else:
            messages.error(
                request, 'You do not have permission to delete sales!')

    context = {
        'sale': sale,
    }

    return render(request, 'retail/delete_sale.html', context)


@login_required
def buyer_report(request):
    """View to display the order history and spending for the buyer."""
    orders = Order.objects.filter(user=request.user).order_by('-date_ordered')
    total_spending = orders.aggregate(Sum('total_amount'))[
        'total_amount__sum'] or 0

    context = {
        'orders': orders,
        'total_spending': total_spending,
    }

    return render(request, 'retail/buyer_report.html', context)


@login_required
def seller_report(request):
    """View to display sales metrics for the seller."""
    sales = Sale.objects.filter(
        customer__user=request.user)  # Assuming you have a way to link products to sellers
    total_sales = sales.count()
    total_revenue = sales.aggregate(Sum('total_amount'))[
        'total_amount__sum'] or 0
    total_profit = sales.aggregate(Sum('profit'))['profit__sum'] or 0

    context = {
        'sales': sales,
        'total_sales': total_sales,
        'total_revenue': total_revenue,
        'total_profit': total_profit,
    }

    return render(request, 'retail/seller_report.html', context)
