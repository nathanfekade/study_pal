from django.urls import path
from study_space import views
from django.urls.resolvers import URLPattern

urlpatterns = [
    path('book/',views.BookList.as_view(), name='book-list'),
    path('book/<int:pk>/', views.BookDetail.as_view(), name='book-detail'),
    path('questionairre/', views.QuestionairreList.as_view(), name='questionairre-list'),
    path('questionairre/<int:pk>', views.QuestionairreDetail.as_view(), name='questionairre-detail')

]