from django.contrib import admin
from .models import Resume


@admin.register(Resume)
class ResumeAdmin(admin.ModelAdmin):
    list_display = [
        'name',
        'email',
        'domain',
        'years_of_experience',
        'current_company',
        'location',
        'candidate_id',
        'is_parsed',
        'uploaded_at'
    ]
    search_fields = ['name', 'email', 'skills', 'domain', 'current_company', 'candidate_id', 'location']
    list_filter = ['is_parsed', 'domain', 'years_of_experience', 'uploaded_at', 'location']
    readonly_fields = ['uploaded_at', 'updated_at']

    fieldsets = (
        ('Candidate Tracking', {
            'fields': ('candidate_id',)
        }),
        ('Personal Information', {
            'fields': ('name', 'email', 'phone', 'address', 'location', 'dob',
                       'passport_details', 'passport_status')
        }),
        ('Professional Information', {
            'fields': ('current_company', 'previous_companies', 'domain', 'years_of_experience',
                       'professional_summary', 'skills')
        }),
        ('Education & Projects', {
            'fields': ('education', 'projects'),
            'classes': ('collapse',)
        }),
        ('Research (Patents & Publications)', {
            'fields': ('patents', 'publications', 'research_papers'),
            'classes': ('collapse',)
        }),
        ('File & Metadata', {
            'fields': ('file', 'is_parsed', 'parse_error',
                       'uploaded_at', 'updated_at')
        }),
    )
