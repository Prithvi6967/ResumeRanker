from django.db import models


class Resume(models.Model):
    name = models.CharField(max_length=200, blank=True, default='Resume')
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    years_of_experience = models.IntegerField(default=0)
    skills = models.TextField(blank=True)
    file = models.FileField(upload_to='resumes/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['-uploaded_at']