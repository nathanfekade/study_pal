from django.urls import path
from study_space import views
from django.urls.resolvers import URLPattern

urlpatterns = [
    path('book/',views.BookList.as_view(), name='book-list')
]