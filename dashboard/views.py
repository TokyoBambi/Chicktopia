from django.shortcuts import render, redirect
from django.contrib import messages


from accounts.models import Customer


def dashboard(request):
    if request.user.is_authenticated:
        try:
            customer = request.user.consumer

            if not customer.is_complete:
                messages.info(
                    request, "Please complete your profile information.")
                return redirect("complete_profile")

        except Exception as e:
            # Create a customer if it doesn't exist
            Customer.objects.create(user=request.user)
            messages.info(
                request, "Please complete your profile information.")
            return redirect("complete_profile")

    context = {
        "cart_item_count": request.session.get('cart_item_count', 0)
    }
    return render(request, "dashboard/dashboard.html", context)
