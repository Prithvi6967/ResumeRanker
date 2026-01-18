
from django.urls import path
from . import views

app_name = 'resumes'

urlpatterns = [
    path('', views.index, name='index'),
    path('rank/', views.rank_resumes, name='rank_resumes'),
]
