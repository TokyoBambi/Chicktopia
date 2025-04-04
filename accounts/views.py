from django.contrib.auth import authenticate, login as auth_login, logout as logout_user
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages


from .models import Customer
from .forms import CreateUserForm, UpdateCustomerForm


def register(request):
    form = CreateUserForm()
    if request.method == "POST":
        form = CreateUserForm(request.POST)

        if form.is_valid():
            form.save()

            return redirect("login")
        else:
            messages.error(request, "Registration Failed.")

    context = {
        "form": form,
    }
    return render(request, "accounts/register.html", context)


def login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            auth_login(request, user)

            try:
                customer = user.consumer

                if not customer.is_complete:
                    messages.info(
                        request, "Please complete your profile information.")
                    return redirect("complete_profile")

            except Exception as e:
                # Create a customer if it doesn't exist
                Customer.objects.create(user=user)
                messages.info(
                    request, "Please complete your profile information.")
                return redirect("complete_profile")

            return redirect("dashboard")

        else:
            messages.error(request, "Invalid username or password.")

    context = {}
    return render(request, "accounts/login.html", context)


@login_required
def logout(request):
    logout_user(request)
    return redirect("login")


@login_required
def complete_profile(request):
    customer = request.user.consumer

    if request.method == "POST":
        form = UpdateCustomerForm(
            request.POST, request.FILES, instance=customer)
        if form.is_valid():
            form.save()
            messages.success(
                request, "Your profile has been updated successfully!")
            return redirect("dashboard")
    else:
        form = UpdateCustomerForm(instance=customer)

    context = {"form": form}
    return render(request, "accounts/complete_profile.html", context)
