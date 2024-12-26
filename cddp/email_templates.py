from django.template.loader import render_to_string
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from django.utils.html import strip_tags




class EmailTemplates:
    @staticmethod
    def get_emoji_status(status):
        emoji_map = {
            'REPORTED': '🔔',
            'VERIFIED': '✅',
            'RESPONDING': '🚀',
            'IN_PROGRESS': '⚡',
            'RESOLVED': '🌟',
            'CLOSED': '🎉',
            'INVALID': '❌'
        }
        return emoji_map.get(status, '📝')

    @staticmethod
    def get_priority_indicator(priority):
        priority_map = {
            'LOW': '⚪',
            'MEDIUM': '🔵',
            'HIGH': '🔶',
            'CRITICAL': '🔴',
            'EMERGENCY': '⭐'
        }
        return priority_map.get(priority, '⚪')

    @staticmethod
    def send_task_assignment_email(task, volunteer):
        subject = f"🎯 New Task Assignment: {task.title}"
        
        context = {
            'volunteer_name': volunteer.user.full_name,
            'task_title': task.title,
            'task_priority': f"{EmailTemplates.get_priority_indicator(task.priority)} Priority: {task.priority}",
            'incident_title': task.incident.title,
            'estimated_time': f"⏱️ {task.estimated_time} minutes" if task.estimated_time else "⏱️ Time not specified",
            'due_date': f"📅 Due: {task.due_date.strftime('%Y-%m-%d %H:%M')}" if task.due_date else "No due date",
            'skills_needed': [f"🔧 {skill.name}" for skill in task.required_skills.all()],
        }
        
        html_message = render_to_string('emails/task_assignment.html', context)
        
        send_mail(
            subject=subject,
            message=strip_tags(html_message),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[volunteer.user.email],
            html_message=html_message
        )

    @staticmethod
    def send_task_reminder_email(task, volunteer):
        hours_remaining = (task.due_date - timezone.now()).total_seconds() / 3600
        urgency = "🔴 URGENT: " if hours_remaining < 24 else "⚠️ Reminder: "
        
        subject = f"{urgency}Task Due Soon - {task.title}"
        
        context = {
            'volunteer_name': volunteer.user.full_name,
            'task_title': task.title,
            'hours_remaining': f"⏰ {int(hours_remaining)} hours remaining",
            'incident_title': task.incident.title,
            'completion_percentage': task.completion_percentage,
        }
        
        html_message = render_to_string('emails/task_reminder.html', context)
        
        send_mail(
            subject=subject,
            message=strip_tags(html_message),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[volunteer.user.email],
            html_message=html_message
        )
