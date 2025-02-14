from django.urls import path
from study_space import views
from django.urls.resolvers import URLPattern

urlpatterns = [
    path('study/',views.StudyList.as_view(), name='study-list')
]