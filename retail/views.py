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

from .models import Order, OrderItem, Payment, Sale
from products.models import Product
from accounts.models import Customer


# ----- Cart Views -----

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
        request.session.modified = True  # Mark session as modified
        request.session.save()  # Explicitly save the session

        # Verify the data was saved correctly
        print("Verifying session data:")
        print(f"Session cart_items: {request.session.get('cart_items')}")
        print(f"Session total_price: {request.session.get('total_price')}")
        print(f"Session count: {request.session.get('count')}")
        print(f"Session keys: {list(request.session.keys())}")

        return JsonResponse({'success': True})
    except Exception as e:
        print(f"Error in update_cart: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)})


def checkout_view(request):
    """
    Checkout view that displays all selected cart items
    """
    import json
    from django import forms

    # Debug print of session data
    print("SESSION DATA:")
    for key in request.session.keys():
        print(f"  {key}: {request.session[key]}")

    # Get cart data from session
    cart_items = request.session.get('cart_items', [])
    total_price = request.session.get('total_price', 0)
    # Note: 'count' not 'cart_item_count'
    cart_item_count = request.session.get('count', 0)

    # Ensure cart_items is a list
    if isinstance(cart_items, str):
        try:
            cart_items = json.loads(cart_items)
        except json.JSONDecodeError:
            cart_items = []

    # Format cart items for display
    for item in cart_items:
        try:
            # Parse and format price to ensure consistent display
            price = float(item.get('price', 0))
            quantity = int(item.get('quantity', 1))

            # Calculate total for each item
            item_total = price * quantity

            # Format for display - this is important to match the template
            item['price'] = "{:.2f}".format(price)
            item['total'] = "{:.2f}".format(item_total)

            # Ensure all required keys exist
            if 'imageUrl' not in item:
                item['imageUrl'] = '/static/img/placeholder.png'

            if 'title' not in item:
                item['title'] = "Unknown Item"

        except (ValueError, TypeError) as e:
            print(f"Error processing item {item}: {str(e)}")
            item['price'] = "0.00"
            item['total'] = "0.00"

    # Format total price for display
    try:
        formatted_total_price = "{:.2f}".format(float(total_price))
    except (ValueError, TypeError):
        formatted_total_price = "0.00"

    # Debug cart data after processing
    print(f"Processed cart items: {cart_items}")
    print(f"Formatted total price: {formatted_total_price}")

    # Add debug info to context
    debug_info = {
        'has_items': bool(cart_items),
        'num_items': len(cart_items),
        'session_keys': list(request.session.keys()),
        'cart_data': json.dumps(cart_items, indent=2)
    }

    # Create context for template
    context = {
        'cart_items': cart_items,
        'total_price': formatted_total_price,
        'cart_item_count': cart_item_count,
        'debug_info': debug_info
    }

    return render(request, 'retail/checkout.html', context)


# ----- Order Views -----

@login_required
def order_list(request):
    """View to display all orders, with optional filtering"""
    # Get filter parameters
    status = request.GET.get('status')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')

    # Start with all orders
    orders = Order.objects.all()

    # Apply filters if provided
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
        # Extract form data
        user_id = request.POST.get('user')
        status = request.POST.get('status', 'pending')
        shipping_address = request.POST.get('shipping_address')
        phone_number = request.POST.get('phone_number')
        notes = request.POST.get('notes')

        # Create a new order
        order = Order(
            id=uuid.uuid4(),
            status=status,
            shipping_address=shipping_address,
            phone_number=phone_number,
            notes=notes
        )

        # Set user if provided
        if user_id:
            from django.contrib.auth.models import User
            try:
                user = User.objects.get(id=user_id)
                order.user = user
            except User.DoesNotExist:
                pass
        elif request.user.is_authenticated:
            order.user = request.user

        # Save the order
        order.save()

        # Process product items
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

        # Update total amount
        order.total_amount = order.get_order_total
        order.save()

        messages.success(request, f'Order {order.id} created successfully!')
        return redirect('order_detail', order_id=order.id)

    # Get data for the form
    products = Product.objects.all()

    context = {
        'products': products,
        'status_choices': Order.ORDER_STATUS_CHOICES,
    }

    return render(request, 'retail/create_order.html', context)


@login_required
def update_order(request, order_id):
    """View to update an existing order"""
    order = get_object_or_404(Order, id=order_id)
    order_items = order.orderitem_set.all()

    if request.method == 'POST':
        # Update order details
        order.status = request.POST.get('status', order.status)
        order.shipping_address = request.POST.get(
            'shipping_address', order.shipping_address)
        order.phone_number = request.POST.get(
            'phone_number', order.phone_number)
        order.notes = request.POST.get('notes', order.notes)
        order.save()

        # Update existing items (this is simplified - a real form would be more complex)
        item_ids = request.POST.getlist('item_id')
        item_quantities = request.POST.getlist('item_quantity')

        if len(item_ids) == len(item_quantities):
            for i in range(len(item_ids)):
                try:
                    item = OrderItem.objects.get(id=item_ids[i], order=order)
                    quantity = int(item_quantities[i])
                    if quantity > 0:
                        item.quantity = quantity
                        item.save()
                    else:
                        item.delete()
                except (OrderItem.DoesNotExist, ValueError):
                    continue

        # Add new items
        new_product_ids = request.POST.getlist('new_product')
        new_quantities = request.POST.getlist('new_quantity')

        if len(new_product_ids) == len(new_quantities):
            for i in range(len(new_product_ids)):
                try:
                    product = Product.objects.get(id=new_product_ids[i])
                    quantity = int(new_quantities[i])
                    if quantity > 0:
                        OrderItem.objects.create(
                            order=order,
                            product=product,
                            quantity=quantity
                        )
                except (Product.DoesNotExist, ValueError):
                    continue

        # Update total amount
        order.total_amount = order.get_order_total
        order.save()

        messages.success(request, f'Order {order.id} updated successfully!')
        return redirect('order_detail', order_id=order.id)

    # Get data for the form
    products = Product.objects.all()

    context = {
        'order': order,
        'order_items': order_items,
        'products': products,
        'status_choices': Order.ORDER_STATUS_CHOICES,
    }

    return render(request, 'retail/update_order.html', context)


@login_required
def delete_order(request, order_id):
    """View to delete an order"""
    order = get_object_or_404(Order, id=order_id)

    if request.method == 'POST':
        # Only allow deletion if order is pending
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
    # Get cart data
    cart_items = request.session.get('cart_items', [])
    total_price = request.session.get('total_price', 0)

    if not cart_items:
        messages.error(request, 'Your cart is empty!')
        return redirect('checkout')

    if request.method == 'POST':
        # Create new order
        order = Order(
            id=uuid.uuid4(),
            user=request.user if request.user.is_authenticated else None,
            status='pending',
            shipping_address=request.POST.get('shipping_address'),
            phone_number=request.POST.get('phone_number'),
            notes=request.POST.get('notes'),
            total_amount=total_price
        )
        order.save()

        # Create order items from cart
        for item in cart_items:
            try:
                product_id = item.get('id')
                quantity = item.get('quantity', 1)
                product = Product.objects.get(id=product_id)

                OrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity=quantity
                )
            except Product.DoesNotExist:
                continue

        # Clear cart
        request.session['cart_items'] = []
        request.session['cart_item_count'] = 0
        request.session['total_price'] = 0
        request.session.save()

        messages.success(request, 'Order created successfully!')
        return redirect('order_detail', order_id=order.id)

    context = {
        'cart_items': cart_items,
        'total_price': total_price,
    }

    return render(request, 'retail/cart_to_order.html', context)


# ----- Payment Views -----

@login_required
def payment_list(request):
    """View to display all payments"""
    # Get filter parameters
    status = request.GET.get('status')
    method = request.GET.get('method')

    # Start with all payments
    payments = Payment.objects.all()

    # Apply filters
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
    """View to create a new payment for an order"""
    order = get_object_or_404(Order, id=order_id)

    # Check if payment already exists
    try:
        existing_payment = Payment.objects.get(order=order)
        messages.warning(
            request, f'A payment already exists for this order: {existing_payment.id}')
        return redirect('payment_detail', payment_id=existing_payment.id)
    except Payment.DoesNotExist:
        pass

    if request.method == 'POST':
        # Create new payment
        payment_method = request.POST.get('payment_method')
        amount_paid = request.POST.get('amount_paid', order.total_amount)
        transaction_id = request.POST.get('transaction_id')
        status = request.POST.get('status', 'pending')

        payment = Payment(
            id=uuid.uuid4(),
            order=order,
            payment_method=payment_method,
            amount_paid=amount_paid,
            transaction_id=transaction_id,
            status=status
        )
        payment.save()

        # Update order status if payment is completed
        if payment.status == 'completed':
            order.status = 'paid'
            order.save()

        messages.success(request, 'Payment created successfully!')
        return redirect('payment_detail', payment_id=payment.id)

    context = {
        'order': order,
        'payment_method_choices': Payment.PAYMENT_METHOD_CHOICES,
        'payment_status_choices': Payment.PAYMENT_STATUS_CHOICES,
    }

    return render(request, 'retail/create_payment.html', context)


@login_required
def update_payment(request, payment_id):
    """View to update an existing payment"""
    payment = get_object_or_404(Payment, id=payment_id)
    order = payment.order

    if request.method == 'POST':
        # Update payment details
        payment.payment_method = request.POST.get(
            'payment_method', payment.payment_method)
        payment.amount_paid = request.POST.get(
            'amount_paid', payment.amount_paid)
        payment.transaction_id = request.POST.get(
            'transaction_id', payment.transaction_id)
        payment.status = request.POST.get('status', payment.status)
        payment.save()

        # Update order status based on payment status
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


# ----- Sale Views -----

@login_required
def sale_list(request):
    """View to display all sales"""
    # Get filter parameters
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')

    # Start with all sales
    sales = Sale.objects.all()

    # Apply filters
    if date_from:
        sales = sales.filter(sale_date__gte=date_from)
    if date_to:
        sales = sales.filter(sale_date__lte=date_to)

    # Calculate totals
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
def create_sale(request):
    """View to create a new sale record"""
    if request.method == 'POST':
        # Get form data
        order_id = request.POST.get('order')
        customer_id = request.POST.get('customer')
        product_ids = request.POST.getlist('products')
        total_amount = request.POST.get('total_amount')
        profit = request.POST.get('profit')

        try:
            # Get related objects
            order = Order.objects.get(id=order_id)
            customer = Customer.objects.get(id=customer_id)

            # Create sale
            sale = Sale(
                id=uuid.uuid4(),
                order=order,
                customer=customer,
                sale_date=timezone.now(),
                total_amount=total_amount,
                profit=profit
            )
            sale.save()

            # Add products
            products = Product.objects.filter(id__in=product_ids)
            sale.products.set(products)

            messages.success(request, 'Sale recorded successfully!')
            return redirect('sale_detail', sale_id=sale.id)

        except (Order.DoesNotExist, Customer.DoesNotExist):
            messages.error(request, 'Invalid order or customer selected!')

    # Get data for the form
    orders = Order.objects.filter(status='delivered')
    customers = Customer.objects.all()
    products = Product.objects.all()

    context = {
        'orders': orders,
        'customers': customers,
        'products': products,
    }

    return render(request, 'retail/create_sale.html', context)


@login_required
def update_sale(request, sale_id):
    """View to update an existing sale record"""
    sale = get_object_or_404(Sale, id=sale_id)

    if request.method == 'POST':
        # Get form data
        customer_id = request.POST.get('customer')
        product_ids = request.POST.getlist('products')
        total_amount = request.POST.get('total_amount')
        profit = request.POST.get('profit')

        try:
            # Update customer if changed
            if customer_id:
                customer = Customer.objects.get(id=customer_id)
                sale.customer = customer

            # Update other fields
            sale.total_amount = total_amount
            sale.profit = profit
            sale.save()

            # Update products
            if product_ids:
                products = Product.objects.filter(id__in=product_ids)
                sale.products.set(products)

            messages.success(request, 'Sale updated successfully!')
            return redirect('sale_detail', sale_id=sale.id)

        except Customer.DoesNotExist:
            messages.error(request, 'Invalid customer selected!')

    # Get data for the form
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
        if request.user.is_staff:  # Only allow staff to delete sales
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


# ----- Dashboard View -----
