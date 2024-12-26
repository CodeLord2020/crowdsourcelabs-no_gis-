from django.shortcuts import render
from accounts.permissions import AdminPermission
# Create your views here.

from rest_framework import generics, permissions, viewsets, filters
from rest_framework.response import Response
from rest_framework import status
from .models import FAQ, ContactRequest
from .serializers import FAQSerializer, ContactRequestSerializer
from django.conf import settings
from django.core.mail import send_mail
from rest_framework.decorators import action
from django.template.loader import render_to_string


class FAQViewSet(viewsets.ModelViewSet):
    queryset = FAQ.objects.all()
    serializer_class = FAQSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter]
    search_fields = ['question', 'answer']

    def get_queryset(self):
        queryset = FAQ.objects.all()
        query = self.request.query_params.get('search', None)
        if query is not None:
            queryset = FAQ.objects.search(query)
        return queryset
    

class ContactRequestViewSet(viewsets.ModelViewSet):
    queryset = ContactRequest.objects.all()
    serializer_class = ContactRequestSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        try:
            self.send_email_notification(serializer.instance)
        except Exception as e:
            return Response(
                {"message": "Request has been submitted, but we couldn't send the notification email."},
                status=status.HTTP_201_CREATED
            )
     
        return Response(
            {"message": "Your request has been submitted successfully. We'll get back to you soon."},
            status=status.HTTP_201_CREATED
        )
    
    def send_email_notification(self, contact_request):
        subject = f"New Contact Request: {contact_request.subject}"
        from_email = settings.EMAIL_HOST_USER
        recipient_list = [settings.ADMIN_EMAIL]

        # Render the HTML message using a template
        html_message = render_to_string('contact.html', {
            'name': contact_request.name,
            'email': contact_request.email,
            'message': contact_request.message,
            'subject': contact_request.subject,
        })

        # Sending the email with both plain text and HTML
        send_mail(
            subject,
            message='',  # leave plain text empty if only HTML is preferred
            from_email=from_email,
            recipient_list=recipient_list,
            fail_silently=False,
            html_message=html_message,  # the HTML content
        )

    @action(detail=True, methods=['patch'], permission_classes=[AdminPermission])
    def resolve(self, request, pk=None):
        contact_request = self.get_object()
        contact_request.is_resolved = not contact_request.is_resolved
        contact_request.save()

        return Response(
            {"message": f"Contact request has been marked as {'resolved' if contact_request.is_resolved else 'unresolved'}."},
            status=status.HTTP_200_OK
        )

    # def send_email_notification1(self, contact_request):
    #     subject = f"New Contact Request: {contact_request.subject}"
    #     message = f"Name: {contact_request.name}\nEmail: {contact_request.email}\nMessage: {contact_request.message}"
    #     from_email = settings.EMAIL_HOST_USER
    #     recipient_list = [settings.ADMIN_EMAIL] 
    #     send_mail(subject, message, from_email, recipient_list, fail_silently=False)

