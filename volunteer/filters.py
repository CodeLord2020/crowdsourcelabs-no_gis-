
from django_filters.rest_framework import  FilterSet, BaseInFilter, ChoiceFilter ,CharFilter, ModelMultipleChoiceFilter, NumberFilter, BooleanFilter, DateTimeFilter
from .models import Skill, VolunteerSkill, Volunteer
from django.db.models import Avg, Count


class SkillFilterSet(FilterSet):
    name = CharFilter(lookup_expr='icontains')
    category = CharFilter(method='filter_category')
    created_after = DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_before = DateTimeFilter(field_name='created_at', lookup_expr='lte')
    has_volunteers = BooleanFilter(method='filter_has_volunteers')
    min_proficiency = NumberFilter(method='filter_min_proficiency')

    class Meta:
        model = Skill
        fields = ['name', 'category']

    def filter_category(self, queryset, name, value):
        if value:
            return queryset.filter(category__iexact=value)
        return queryset

    def filter_has_volunteers(self, queryset, name, value):
        if value is True:
            return queryset.annotate(
                volunteer_count=Count('volunteerskill')
            ).filter(volunteer_count__gt=0)
        return queryset

    def filter_min_proficiency(self, queryset, name, value):
        return queryset.annotate(
            avg_proficiency=Avg('volunteerskill__proficiency_level')
        ).filter(avg_proficiency__gte=value)
    

class VolunteerSkillFilterSet(FilterSet):
    verified = BooleanFilter()
    min_proficiency = NumberFilter(field_name='proficiency_level', lookup_expr='gte')
    max_proficiency = NumberFilter(field_name='proficiency_level', lookup_expr='lte')
    skill_category = CharFilter(field_name='skill__category')
    
    class Meta:
        model = VolunteerSkill
        fields = ['verified', 'proficiency_level', 'skill']



class VolunteerFilter(FilterSet):
    min_rating = NumberFilter(field_name="rating", lookup_expr='gte')
    max_rating = NumberFilter(field_name="rating", lookup_expr='lte')
    skills = ModelMultipleChoiceFilter(
        queryset=Skill.objects.all(),
        field_name='skills',
        conjoined=True  # All specified skills must be present
    )
    min_verified_hours = NumberFilter(field_name="verified_hours", lookup_expr='gte')
    skills_category = ChoiceFilter(
        field_name="skills__category",
        choices=Skill.CATEGORY_CHOICES
    )
    multiple_skills = BaseInFilter(
        field_name="skills__id",
        lookup_expr='in'
    )
    created_after = DateTimeFilter(field_name="created_at", lookup_expr='gte')
    created_before = DateTimeFilter(field_name="created_at", lookup_expr='lte')

    min_proficiency = NumberFilter(
        field_name="volunteerskill__proficiency_level",
        lookup_expr='gte'
    )
    max_proficiency = NumberFilter(
        field_name="volunteerskill__proficiency_level",
        lookup_expr='lte'
    )
    proficiency_level = NumberFilter(
        field_name='volunteerskill__proficiency_level',
        method='filter_by_proficiency'
    )
    verified_skills_only = BooleanFilter(method='filter_verified_skills')


    class Meta:
        model = Volunteer
        fields = {
            'is_available': ['exact'],
            'experience_level': ['exact', 'in'],
            'max_travel_distance': ['lte', 'gte'],
        }

    def filter_by_proficiency(self, queryset, name, value):
        return queryset.filter(volunteerskill__proficiency_level=value).distinct()

    def filter_verified_skills(self, queryset, name, value):
        if value:
            return queryset.filter(volunteerskill__verified=True).distinct()
        return queryset
