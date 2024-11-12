# cddp/tasks.py
from celery import shared_task
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from .email_templates import EmailTemplates

@shared_task(
    name='cddp.tasks.send_notification_email',
    retry_backoff=True,
    max_retries=3
)
def send_notification_email(subject, template_name, context, recipient_list):
    """Generic task for sending notification emails"""
    html_message = render_to_string(f'emails/{template_name}.html', context)
    plain_message = strip_tags(html_message)
    
    return send_mail(
        subject=subject,
        message=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=recipient_list,
        html_message=html_message
    )

@shared_task(
    name='cddp.tasks.send_incident_status_notification',
    retry_backoff=True,
    max_retries=3
)
def send_incident_status_notification(incident_id, previous_status, new_status):
    from incident.models import Incident  # Import here to avoid circular imports
    
    try:
        incident = Incident.objects.get(id=incident_id)
        
        status_messages = {
            'VERIFIED': {
                'subject': '✅ Incident Verified: Action Required',
                'message': (
                    f"The incident '{incident.title}' has been verified and requires "
                    f"immediate attention. Priority: {incident.get_priority_display()}"
                )
            },
            'RESPONDING': {
                'subject': '🚀 Response Team Deployed',
                'message': (
                    f"Response teams are now being deployed to handle the incident "
                    f"'{incident.title}'. Help is on the way!"
                )
            },
            'IN_PROGRESS': {
                'subject': '⚡ Incident Response in Progress',
                'message': (
                    f"Teams are actively working on resolving the incident "
                    f"'{incident.title}'. We'll keep you updated on the progress."
                )
            },
            'RESOLVED': {
                'subject': '🌟 Incident Successfully Resolved',
                'message': (
                    f"Great news! The incident '{incident.title}' has been successfully "
                    f"resolved. Thank you for your patience and cooperation."
                )
            },
            'CLOSED': {
                'subject': '🎉 Incident Closed - Mission Accomplished',
                'message': (
                    f"The incident '{incident.title}' has been officially closed. "
                    f"Thank you to all teams involved in the resolution!"
                )
            }
        }

        if new_status in status_messages:
            # Get all stakeholders for this incident
            stakeholders = set()
            stakeholders.add(incident.reporter.user.email)
            stakeholders.update(
                responder.user.email 
                for responder in incident.assigned_responders.all()
            )
            stakeholders.update(
                volunteer.user.email 
                for volunteer in incident.assigned_volunteers.all()
            )

            context = {
                'incident_title': incident.title,
                'incident_priority': incident.get_priority_display(),
                'previous_status': previous_status,
                'new_status': new_status,
                'status_message': status_messages[new_status]['message'],
                'location': incident.address,
                'category': incident.category.name,
                'updated_at': timezone.now().strftime('%Y-%m-%d %H:%M:%S')
            }

            send_notification_email.delay(
                subject=status_messages[new_status]['subject'],
                template_name='incident_status_update',
                context=context,
                recipient_list=list(stakeholders)
            )

    except Incident.DoesNotExist:
        return None



@shared_task(
    name='cddp.tasks.send_responder_assignment_notification',
    retry_backoff=True,
    max_retries=3
)
def send_responder_assignment_notification(incident_id, responder_id):
    from incident.models import Incident 
    from responders.models import Responder
    try:
        incident = Incident.objects.get(id=incident_id)
        responder = Responder.objects.get(id=responder_id)

        subject = f"🚨 New Incident Assigned: {incident.title}"
        context = {
            'responder_name': responder.user.full_name,
            'incident_title': incident.title,
            'incident_priority': incident.get_priority_display(),
            'incident_category': incident.category.name,
            'incident_location': incident.address,
            'assignment_role': incident.incidentassignment_set.get(responder=responder).get_role_display(),
        }

        html_message = render_to_string('emails/responder_assignment.html', context)
        plain_message = strip_tags(html_message)

        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[responder.user.email],
            html_message=html_message
        )

    except (Incident.DoesNotExist, Responder.DoesNotExist):
        return None
    


@shared_task(
    name='cddp.tasks.send_task_assignment_notification',
    retry_backoff=True,
    max_retries=3
)
def send_task_assignment_notification(task_id, volunteer_id):
    from incident.models import Task
    from volunteer.models import Volunteer  
    
    try:
        task = Task.objects.get(id=task_id)
        volunteer = Volunteer.objects.get(id=volunteer_id)
        
        context = {
            'volunteer_name': volunteer.user.full_name,
            'task_title': task.title,
            'task_priority': f"{EmailTemplates.get_priority_indicator(task.priority)} {task.get_priority_display()}",
            'incident_title': task.incident.title,
            'estimated_time': f"⏱️ {task.estimated_time} minutes" if task.estimated_time else "⏱️ Time not specified",
            'due_date': f"📅 Due: {task.due_date.strftime('%Y-%m-%d %H:%M')}" if task.due_date else "No due date",
            'skills_needed': [f"🔧 {skill.name}" for skill in task.required_skills.all()],
        }

        send_notification_email.delay(
            subject=f"🎯 New Task Assignment: {task.title}",
            template_name='emails/task_assignment',
            context=context,
            recipient_list=[volunteer.user.email]
        )

    except (Task.DoesNotExist, Volunteer.DoesNotExist):
        return None



@shared_task(
    name='cddp.tasks.send_task_completion_notification',
    retry_backoff=True,
    max_retries=3
)
def send_task_completion_notification(task_id):
    from incident.models import Task  # Import here to avoid circular imports
    from datetime import timedelta
    try:
        task = Task.objects.get(id=task_id)
        
        # Notify all stakeholders
        stakeholders = set()
        stakeholders.update(
            volunteer.user.email 
            for volunteer in task.volunteers.all()
        )
        stakeholders.add(task.created_by.email)
        
        # If task is part of an incident, notify incident responders
        if task.incident:
            stakeholders.update(
                responder.user.email 
                for responder in task.incident.assigned_responders.all()
            )

        context = {
            'task_title': task.title,
            'incident_title': task.incident.title if task.incident else None,
            'completion_time': timezone.now().strftime('%Y-%m-%d %H:%M:%S'),
            'volunteers': [
                volunteer.user.full_name 
                for volunteer in task.volunteers.all()
            ]
        }

        send_notification_email.delay(
            subject=f"✨ Task Completed: {task.title}",
            template_name='emails/task_completion',
            context=context,
            recipient_list=list(stakeholders)
        )

    except Task.DoesNotExist:
        return None



@shared_task
def send_allocation_notification(resource_id):
    from incident.models import IncidentResource  
    resource = IncidentResource.objects.get(id=resource_id)
    context = {
        'resource': resource,
        'incident': resource.incident,
        'quantity': resource.quantity_allocated,
        'allocator': resource.allocated_by,
        'expected_return_date': resource.expected_return_date,
        'dashboard_url': f"{settings.FRONTEND_URL}{reverse('resource-detail', args=[resource.id])}"
    }

    html_content = render_to_string('emails/resource_allocated.html', context)
    text_content = render_to_string('emails/resource_allocated.txt', context)

    send_mail(
        subject=f'Resource Allocated: {resource.resource.name} for {resource.incident.title}',
        message=text_content,
        html_message=html_content,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[resource.requested_by.email],
        fail_silently=False
    )

@shared_task
def send_return_submission_notification(resource_id, quantity):
    from incident.models import IncidentResource  # Import here to avoid circular import
    resource = IncidentResource.objects.get(id=resource_id)
    context = {
        'resource': resource,
        'quantity': quantity,
        'submitter': resource.requested_by,
        'verification_url': f"{settings.FRONTEND_URL}{reverse('resource-verify-return', args=[resource.id])}"
    }

    html_content = render_to_string('emails/return_submitted.html', context)
    text_content = render_to_string('emails/return_submitted.txt', context)

    send_mail(
        subject=f'Resource Return Submitted: {resource.resource.name}',
        message=text_content,
        html_message=html_content,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[resource.allocated_by.email],
        fail_silently=False
    )


@shared_task
def send_return_verification_notification(resource_id, status):
    from incident.models import IncidentResource  # Import here to avoid circular import
    resource = IncidentResource.objects.get(id=resource_id)
    context = {
        'resource': resource,
        'status': status,
        'verifier': resource.return_verified_by,
        'notes': resource.return_notes,
        'dashboard_url': f"{settings.FRONTEND_URL}{reverse('resource-detail', args=[resource.id])}"
    }

    html_content = render_to_string('emails/return_verified.html', context)
    text_content = render_to_string('emails/return_verified.txt', context)

    send_mail(
        subject=f'Resource Return {status}: {resource.resource.name}',
        message=text_content,
        html_message=html_content,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[resource.requested_by.email],
        fail_silently=False
    )


@shared_task
def send_overdue_reminder(resource_id):
    from incident.models import IncidentResource
    resource = IncidentResource.objects.get(id=resource_id)
    context = {
        'resource': resource,
        'days_overdue': (timezone.now() - resource.expected_return_date).days,
        'return_url': f"{settings.FRONTEND_URL}{reverse('resource-submit-return', args=[resource.id])}",
        'incident': resource.incident
    }

    html_content = render_to_string('emails/overdue_return_reminder.html', context)
    text_content = render_to_string('emails/overdue_return_reminder.txt', context)

    send_mail(
        subject=f'OVERDUE: Please Return {resource.resource.name}',
        message=text_content,
        html_message=html_content,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[resource.requested_by.email],
        fail_silently=False,
        cc=[resource.allocated_by.email]
    )


@shared_task(
    name='cddp.tasks.check_overdue_tasks',
    retry_backoff=True,
    max_retries=3
)
def check_overdue_tasks():
    from incident.models import Task
    """Check for tasks that are overdue and send notifications if needed."""
    overdue_tasks = Task.objects.filter(due_date__lt=timezone.now(), status__in=['PENDING', 'IN_PROGRESS'])
    for task in overdue_tasks:
        volunteers = task.get_volunteers()
        if volunteers is not None:
            try:
                for volunteer in volunteers:
                    context = {
                    'volunteer_name': volunteer.user.full_name,
                    'task_title': task.title,
                    'task_priority': f"{EmailTemplates.get_priority_indicator(task.priority)} {task.get_priority_display()}",
                    'incident_title': task.incident.title,
                    'estimated_time': f"⏱️ {task.estimated_time} minutes" if task.estimated_time else "⏱️ Time not specified",
                    'due_date': f"📅 Due: {task.due_date.strftime('%Y-%m-%d %H:%M')}" if task.due_date else "No due date",
                    'skills_needed': [f"🔧 {skill.name}" for skill in task.required_skills.all()],
                    }
                    send_notification_email.delay(
                        subject=f"🎯 Task Overdue Notification: {task.title}",
                        template_name='task_overdue',
                        context=context,
                        recipient_list=[volunteer.user.email]
                    )
            except Task.DoesNotExist:
                return None

@shared_task(
    name='cddp.tasks.test_stuff',
    retry_backoff=True,
    max_retries=3
)
def test_stuff():
    context = {
    'volunteer_name': "volunteer Mcc",
    'task_title': "Just Testing Bro",
    'task_priority': "'LOW': '⚪',",
    'estimated_time': "⏱️ Time not specified⏱️",
    'due_date': "📅 Due: No due date",
    'skills_needed': [f"🔧 No SKill"],
    }
    send_notification_email.delay(
        subject=f"🎯 Task Test Notification",
        template_name='task_overdue',
        context=context,
        recipient_list=["adebayoworkmail@gmail.com"]
    )


    

@shared_task
def send_task_reminders():
    from incident.models import Task
    """Send reminders for tasks that are approaching their due date within the next 24 hours."""
    reminder_time = timezone.now() + timedelta(hours=24)
    tasks_due_soon = Task.objects.filter(due_date__lte=reminder_time, due_date__gt=timezone.now(), status='PENDING')  #!!! Perhaps not PENDING?
    for task in tasks_due_soon:
        volunteers = task.get_volunteers()
        if volunteers is not None:
            try:
                for volunteer in volunteers:
                    context = {
                    'volunteer_name': volunteer.user.full_name,
                    'task_title': task.title,
                    'task_priority': f"{EmailTemplates.get_priority_indicator(task.priority)} {task.get_priority_display()}",
                    'incident_title': task.incident.title,
                    'estimated_time': f"⏱️ {task.estimated_time} minutes" if task.estimated_time else "⏱️ Time not specified",
                    'due_date': f"📅 Due: {task.due_date.strftime('%Y-%m-%d %H:%M')}" if task.due_date else "No due date",
                    'skills_needed': [f"🔧 {skill.name}" for skill in task.required_skills.all()],
                    }
                    send_notification_email.delay(
                        subject=f"🎯 Upcoming Task Due Reminder: {task.title}",
                        template_name='task_overdue',
                        context=context,
                        recipient_list=[volunteer.user.email]
                    )
            except Task.DoesNotExist:
                return None
