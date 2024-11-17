from django.core.mail import send_mail
from .models import User
from cddp.settings import EMAIL_HOST_USER ,CLIENT_URL, ADMIN_EMAIL
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator


def send_registration_email(email):
    user = User.objects.get(email=email)
    subject = "Welcome to CDDP"
    message = render_to_string(
        'account-welcome.html', 
        {
            'user': user,  # Passing user details to the template
            'support_email': ADMIN_EMAIL,  # Using the ADMIN_EMAIL from settings
        }
    )
    send_mail(
        subject=subject,
        message=message,
        from_email=EMAIL_HOST_USER,
        recipient_list=[email],
        fail_silently=False,
        html_message=message,  
    )





def send_verification_email(email, token):
    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        user = None

    if user is not None:
        
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        verification_url = f"{CLIENT_URL}/auth/verify/{uid}/{token}/"

        subject = "Crowdsourced Disaster Response Platform"
        context = {
            'full_name' : user.first_name,
            'user_email': email,
            'verification_url': verification_url,
        }
        message = render_to_string('account-verify.html', context)
        html_message = render_to_string('account-verify.html',context)
        sender = EMAIL_HOST_USER 
        recipients = [email]
        
        send_mail(subject=subject , message=message,from_email=sender,recipient_list=recipients,html_message=html_message)




def send_password_reset_email(email):

    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        user = None

    if user is not None:
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        reset_link = f"{CLIENT_URL}/reset-password?uid={uid}&token={token}"
        subject = 'Password Reset Request'
        context = {'reset_link': reset_link}
        message = render_to_string('password_reset_email.html', context)
        html_message = render_to_string('password_reset_email.html', context)
        send_mail(subject, message, EMAIL_HOST_USER, [user.email], html_message=html_message)