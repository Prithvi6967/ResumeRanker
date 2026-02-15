from django.db import models


class Resume(models.Model):
    # Personal Details
    name = models.CharField(max_length=200, blank=True, default='')
    email = models.EmailField(blank=True, default='')
    phone = models.CharField(max_length=20, blank=True, default='')
    address = models.TextField(blank=True, default='')
    location = models.CharField(max_length=200, blank=True, default='')
    dob = models.DateField(null=True, blank=True)
    passport_details = models.CharField(max_length=100, blank=True, default='')
    passport_status = models.CharField(max_length=50, blank=True, default='')

    # Professional Details
    current_company = models.CharField(max_length=200, blank=True, default='')
    domain = models.CharField(max_length=200, blank=True, default='')
    years_of_experience = models.IntegerField(default=0)
    professional_summary = models.TextField(blank=True, default='')


    skills = models.TextField(blank=True, default='')

    # Education Details (JSON field - stores array of education records)
    # Format: [{"degree": "B.Tech", "institution": "XYZ", "year": "2020", "field": "CS"}, ...]
    education = models.JSONField(default=list, blank=True)

    # Projects (JSON field - stores array of projects)
    # Format: [{"title": "Project 1", "description": "...", "technologies": "..."}, ...]
    projects = models.JSONField(default=list, blank=True)


    candidate_id = models.CharField(max_length=50, unique=True, blank=True, default='')


    previous_companies = models.JSONField(default=list, blank=True)


    patents = models.JSONField(default=list, blank=True)

    publications = models.JSONField(default=list, blank=True)

    research_papers = models.JSONField(default=list, blank=True)

    file = models.FileField(upload_to='resumes/')

    # Metadata
    uploaded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Processing Status
    is_parsed = models.BooleanField(default=False)
    parse_error = models.TextField(blank=True, default='')

    def __str__(self):
        return self.name or f"Resume {self.id}"

    class Meta:
        ordering = ['-uploaded_at']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['domain']),
            models.Index(fields=['years_of_experience']),
            models.Index(fields=['is_parsed']),
        ]
