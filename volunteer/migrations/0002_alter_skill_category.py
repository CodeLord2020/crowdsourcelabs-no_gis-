# Generated by Django 5.1.2 on 2024-11-02 07:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('volunteer', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='skill',
            name='category',
            field=models.CharField(choices=[('HEALTH', 'Health & Safety'), ('MANAGEMENT', 'Management & Leadership'), ('COMMUNICATION', 'Communication & Public Relations'), ('EDUCATION', 'Education & Tutoring'), ('TECH', 'Technology & IT Support'), ('LOGISTICS', 'Logistics & Transportation'), ('LANGUAGE', 'Language Skills'), ('ENVIRONMENT', 'Environmental Conservation'), ('ANIMAL_CARE', 'Animal Care'), ('MENTORING', 'Mentoring & Coaching'), ('ADMIN_SUPPORT', 'Administrative Support'), ('ARTS', 'Arts & Culture'), ('HUMAN_SERVICES', 'Human Services'), ('LEGAL', 'Legal Assistance'), ('FUNDRAISING', 'Fundraising & Grant Writing'), ('RESEARCH', 'Research & Data Analysis'), ('DISASTER_RELIEF', 'Disaster Relief'), ('ADVOCACY', 'Advocacy & Policy'), ('SPORTS', 'Sports & Recreation'), ('HOSPITALITY', 'Hospitality & Events'), ('OTHERS', 'Other Categories')], default='OTHERS', max_length=50),
        ),
    ]
