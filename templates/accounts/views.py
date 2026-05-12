from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages

def login_view(request):
    if request.user.is_authenticated:
        return redirect('/')

    if request.method == 'POST':
        email    = request.POST.get('username')
        password = request.POST.get('password')
        user     = authenticate(request, username=email, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, f'Bienvenue {user.first_name} !')
            return redirect('/')
        else:
            messages.error(request, 'Email ou mot de passe incorrect.')

    return render(request, 'accounts/login.html')


def logout_view(request):
    logout(request)
    messages.info(request, 'Vous êtes déconnecté.')
    return redirect('/')


def register(request):
    return render(request, 'accounts/register.html')