import json

from django.http import JsonResponse
from django.shortcuts import render
from django.core.mail import send_mail

from .forms import SendEmailForm
from info import EMAIL_FROM, EMAIL_TO


def index(request):
    email_form = SendEmailForm()
    return render(request, 'portfolio/portfolio.html', context={'email_form': email_form})


def send_email(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        email_form = SendEmailForm(data)
        if email_form.is_valid():
            subject = email_form.cleaned_data['email_subject']
            message = (f"{email_form.cleaned_data['email_text']}\nName: {email_form.cleaned_data['email_name']}"
                       f"\nEmail: {email_form.cleaned_data['email_email']}")

            email_from = EMAIL_FROM
            email_to = [EMAIL_TO,]

            send_mail(subject, message, email_from, email_to)
        else:
            return JsonResponse({'success': False, 'message': "OMG! THERE'S BEEN A MISTAKE. STRANGE..."})
    return JsonResponse({'success': True, 'message': 'MESSAGE SUCCESSFULLY SENT.'})


