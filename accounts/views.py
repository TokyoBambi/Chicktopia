from django.contrib.auth import authenticate, login as auth_login, logout as logout_user
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages


from .forms import CreateUserForm


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
        print(username,password)

        user = authenticate(request, username=username, password=password)
        print(user)     
        if user is not None:
            auth_login(request, user)

            return redirect("dashboard")

        else:    
            messages.error(request, "Invalid username or password.")

    context = {}
    return render(request, "accounts/login.html", context)

@login_required
def logout(request):
    logout_user(request)
    return redirect("login")