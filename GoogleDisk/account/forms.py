from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.validators import ASCIIUsernameValidator


class RegisterForm(forms.ModelForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'логін'}),
        validators=[ASCIIUsernameValidator(message="Будьласка введіть корректне ім`я користувача.")])
    email = forms.EmailField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'пошта'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'пароль'}))
    safepass1 = forms.CharField(widget=forms.TextInput(
        attrs={'class': 'form-control1', 'oninput': 'formatPinCode(this)', 'style': 'font-size: 15px;',
               'placeholder': 'P'}), max_length=1)
    safepass2 = forms.CharField(widget=forms.TextInput(
        attrs={'class': 'form-control1', 'oninput': 'formatPinCode(this)', 'style': 'font-size: 15px;',
               'placeholder': 'A'}), max_length=1)
    safepass3 = forms.CharField(widget=forms.TextInput(
        attrs={'class': 'form-control1', 'oninput': 'formatPinCode(this)', 'style': 'font-size: 15px;',
               'placeholder': 'S'}), max_length=1)
    safepass4 = forms.CharField(widget=forms.TextInput(
        attrs={'class': 'form-control1', 'oninput': 'formatPinCode(this)', 'style': 'font-size: 15px;',
               'placeholder': 'S'}), max_length=1)

    class Meta:
        model = User
        fields = ['username', 'email', 'password']
