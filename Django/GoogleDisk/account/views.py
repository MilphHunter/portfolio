from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User
from django.shortcuts import redirect, render
from django.urls import reverse

from .forms import RegisterForm
from .models import Profile


def user_sign_up(request):
    if request.method == 'POST':
        user_form = RegisterForm(request.POST)
        if user_form.is_valid():
            email = user_form.cleaned_data['email']
            if User.objects.filter(email=email).exists():
                user_form.add_error('email', 'Цей email вже використвується.')
                return render(request, 'account/registration/signup.html', {'user_form': user_form})
            new_user = user_form.save(commit=False)
            new_user.password = make_password(user_form.cleaned_data['password'])
            new_user.save()
            userPin = user_form.cleaned_data['safepass1'] + user_form.cleaned_data['safepass2'] + \
                      user_form.cleaned_data['safepass3'] + user_form.cleaned_data['safepass4']
            Profile.objects.create(user=new_user, userPin=userPin)
            login_url = reverse('account:login')
            return redirect(login_url)
    else:
        user_form = RegisterForm()
    return render(request, 'account/registration/signup.html', {'user_form': user_form})
