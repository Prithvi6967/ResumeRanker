from django.urls import path
from . import views

app_name = 'resumes'

urlpatterns = [
    path('', views.index, name='index'),
    path('upload/', views.upload_resume, name='upload_resume'),
    path('rank/', views.rank_resumes, name='rank_resumes'),
]
